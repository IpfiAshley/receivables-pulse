from datetime import date, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
import csv
import io
import json
import sqlite3

ROOT = Path(__file__).resolve().parent
DB = ROOT / "receivables.sqlite3"
WEB = ROOT


def db_connect():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute("""CREATE TABLE IF NOT EXISTS invoices (
        invoice_id TEXT PRIMARY KEY, customer TEXT NOT NULL, email TEXT NOT NULL DEFAULT '',
        invoice_date TEXT NOT NULL, due_date TEXT NOT NULL, amount REAL NOT NULL,
        paid REAL NOT NULL DEFAULT 0, imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""")
    conn.commit()
    return conn


def get_summary():
    today = date.today()
    with db_connect() as conn:
        rows = [dict(r) for r in conn.execute("SELECT * FROM invoices")]
    open_rows = []
    for row in rows:
        outstanding = max(0, row["amount"] - row["paid"])
        if outstanding <= 0:
            continue
        days_overdue = (today - date.fromisoformat(row["due_date"])).days
        row.update(outstanding=round(outstanding, 2), days_overdue=max(0, days_overdue), is_overdue=days_overdue > 0)
        open_rows.append(row)
    open_rows.sort(key=lambda x: (not x["is_overdue"], -x["days_overdue"], -x["outstanding"]))
    buckets = {"Not due": 0, "1–30 days": 0, "31–60 days": 0, "61–90 days": 0, "90+ days": 0}
    for row in open_rows:
        d = row["days_overdue"]
        key = "Not due" if d == 0 else "1–30 days" if d <= 30 else "31–60 days" if d <= 60 else "61–90 days" if d <= 90 else "90+ days"
        buckets[key] += row["outstanding"]
    customers = {}
    for row in open_rows:
        customers[row["customer"]] = customers.get(row["customer"], 0) + row["outstanding"]
    total = sum(r["outstanding"] for r in open_rows)
    overdue = sum(r["outstanding"] for r in open_rows if r["is_overdue"])
    return {"asOf": today.isoformat(), "openBalance": round(total, 2), "overdueBalance": round(overdue, 2),
            "overdueCount": sum(1 for r in open_rows if r["is_overdue"]), "openCount": len(open_rows),
            "buckets": buckets, "customers": sorted([{"name": k, "balance": round(v, 2)} for k, v in customers.items()], key=lambda x: -x["balance"])[:8],
            "invoices": open_rows}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def send_json(self, code, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/summary":
            return self.send_json(200, get_summary())
        if path == "/template.csv":
            raw = b"invoice_id,customer,email,invoice_date,due_date,amount,paid\n"
            self.send_response(200)
            self.send_header("Content-Type", "text/csv; charset=utf-8")
            self.send_header("Content-Disposition", "attachment; filename=receivables-template.csv")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            return self.wfile.write(raw)
        if path in ("/", "/index.html"):
            raw = (WEB / "index.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            return self.wfile.write(raw)
        return self.send_json(404, {"error": "Not found"})

    def do_POST(self):
        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length", 0))
        if length > 12_000_000:
            return self.send_json(413, {"error": "File is too large (12 MB limit)."})
        raw = self.rfile.read(length)
        if path == "/api/import":
            try:
                text = raw.decode("utf-8-sig")
                reader = csv.DictReader(io.StringIO(text))
                needed = {"invoice_id", "customer", "invoice_date", "due_date", "amount"}
                if not reader.fieldnames or not needed.issubset({h.strip().lower() for h in reader.fieldnames}):
                    raise ValueError("Required CSV columns: invoice_id, customer, invoice_date, due_date, amount. Optional: email, paid.")
                clean = []
                for n, source in enumerate(reader, start=2):
                    row = {str(k).strip().lower(): (v or "").strip() for k, v in source.items() if k}
                    inv, customer = row.get("invoice_id", ""), row.get("customer", "")
                    if not inv or not customer:
                        raise ValueError(f"Row {n}: invoice_id and customer are required.")
                    inv_date = date.fromisoformat(row["invoice_date"]).isoformat()
                    due = date.fromisoformat(row["due_date"]).isoformat()
                    amount = float(row["amount"])
                    paid = float(row.get("paid", "0") or 0)
                    if amount < 0 or paid < 0 or paid > amount:
                        raise ValueError(f"Row {n}: amounts must be non-negative and paid cannot exceed amount.")
                    clean.append((inv, customer[:160], row.get("email", "")[:200], inv_date, due, amount, paid))
                if not clean:
                    raise ValueError("No invoice rows found in this CSV.")
                with db_connect() as conn:
                    conn.executemany("""INSERT INTO invoices(invoice_id,customer,email,invoice_date,due_date,amount,paid)
                        VALUES(?,?,?,?,?,?,?) ON CONFLICT(invoice_id) DO UPDATE SET customer=excluded.customer,
                        email=excluded.email,invoice_date=excluded.invoice_date,due_date=excluded.due_date,
                        amount=excluded.amount,paid=excluded.paid,imported_at=CURRENT_TIMESTAMP""", clean)
                return self.send_json(200, {"ok": True, "count": len(clean)})
            except (UnicodeDecodeError, csv.Error, ValueError, KeyError) as exc:
                return self.send_json(400, {"error": str(exc) or "Could not read this CSV."})
        if path == "/api/clear":
            with db_connect() as conn:
                conn.execute("DELETE FROM invoices")
            return self.send_json(200, {"ok": True})
        return self.send_json(404, {"error": "Not found"})


if __name__ == "__main__":
    db_connect().close()
    print("Receivables Pulse is running at http://127.0.0.1:8766")
    ThreadingHTTPServer(("127.0.0.1", 8766), Handler).serve_forever()


