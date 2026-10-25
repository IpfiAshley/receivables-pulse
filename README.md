# Receivables Pulse

Receivables Pulse helps a small business turn an accounts receivable export into a prioritized customer follow-up queue. It summarizes open and overdue balances, shows an aging breakdown, highlights larger customer balances, and prepares editable payment reminder drafts for each invoice.

## Run locally

Requires Python 3.10 or newer. No packages to install.

```powershell
cd outputs/receivables-pulse
python app.py
```

Open <http://127.0.0.1:8766>. The app creates `receivables.sqlite3` locally when first run. It listens only on this computer and does not send invoice data to an online service.

## Import your receivables

Export your open invoices from your invoicing or bookkeeping system as CSV. Required headings are:

- `invoice_id`
- `customer`
- `invoice_date`
- `due_date`
- `amount`

Optional headings are `email` and `paid`. Dates should use `YYYY-MM-DD`; amounts should be numeric with no currency symbol. Download the CSV template in the app for the expected layout. Importing the same invoice ID again updates its row, so a fresh export can refresh the work queue.

## What the analysis means

Past due is calculated from the invoice due date and the computer's current date. The aging chart groups open balances into not due, 1–30, 31–60, 61–90, and 90+ days late. The queue puts overdue invoices first, then sorts by days late and amount. Email drafts are editable suggestions; they are not sent automatically. Review them and confirm payment status with your customer before sending.

This is a lightweight local work queue, not accounting software. It does not reconcile bank payments, predict whether an invoice will be paid, or replace your accounting records. Back up the SQLite file if you want to keep records when moving computers.
