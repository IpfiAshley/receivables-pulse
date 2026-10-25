# Receivables Pulse

Receivables Pulse is a small, local-first accounts receivable follow-up workspace for small businesses. It turns an accounts receivable CSV export into a clear list of unpaid invoices, shows which balances are overdue, and helps staff prepare customer reminders.

The problem it addresses is simple: when invoice information is spread across bookkeeping screens or spreadsheets, it can be hard to see what is owed, how late it is, and who should be contacted first. Receivables Pulse gives that information one focused view.

## What it does

- Summarizes total outstanding and overdue balances.
- Shows the number of open invoices and customers with overdue balances.
- Groups outstanding balances by age: not due, 1–30, 31–60, 61–90, and more than 90 days overdue.
- Ranks invoices with overdue items first, oldest due date first, then larger balance.
- Shows the largest outstanding customer balances.
- Prepares an editable payment reminder for an invoice. You can copy the draft or open it in your email app; it never sends email automatically.
- Exports the current follow-up queue to CSV.
- Imports a fresh CSV export and updates an existing invoice when its invoice ID matches.

It is a collection work queue, not accounting software. It does not contact customers, process payments, reconcile a bank account, or predict whether an invoice will be paid.

## Run the app

You need Python 3.10 or newer. The app uses Python's standard library, so there are no extra packages to install.

```powershell
git clone https://github.com/IpfiAshley/receivables-pulse.git
cd receivables-pulse
python app.py
```

Keep the terminal window open while you use the app. Open <http://127.0.0.1:8766> in your browser. To stop the app, return to the terminal and press `Ctrl+C`.

On first run, the app creates `receivables.sqlite3` in the project folder. This database stores imported invoice data on that computer. It is excluded from Git by `.gitignore`.

## Get your invoice data ready

Export open invoices or accounts receivable from your invoicing or bookkeeping system as a CSV file. The column names below are required; `email` and `paid` are optional.

| Column | Required? | What to enter |
| --- | --- | --- |
| `invoice_id` | Yes | A unique invoice number. Re-importing this ID updates that invoice. |
| `customer` | Yes | Customer or business name. |
| `invoice_date` | Yes | Invoice date in `YYYY-MM-DD` format. |
| `due_date` | Yes | Payment due date in `YYYY-MM-DD` format. |
| `amount` | Yes | Original invoice total as a number, in South African rand (ZAR). |
| `email` | No | Customer's accounts contact email, used to prefill the reminder draft. |
| `paid` | No | Amount already paid, as a number. If omitted or blank, it is treated as zero. |

Use plain numbers without `R`, currency codes, or thousands separators. For example, enter `12500.50`, not `R12,500.50`. Save the file as UTF-8 CSV. The app includes a template download with the expected headings. The repository also includes `practice-invoices.csv`, which contains fictional data so you can try the import before using your own export.

Example:

```csv
invoice_id,customer,email,invoice_date,due_date,amount,paid
INV-2048,Example Customer,accounts@example.com,2026-10-01,2026-10-21,12500.50,2500
```

## Use it step by step

1. Start the app and open <http://127.0.0.1:8766>.
2. Select **Import receivables CSV** and choose your export. To explore the app first, choose `practice-invoices.csv` from the downloaded project folder.
3. Review the summary cards for total outstanding, past due, oldest overdue invoice, and customers with overdue amounts.
4. Use **All open** or **Past due** to focus the follow-up queue. The age chart and largest balances help you understand where the unpaid amount is concentrated.
5. Select **Prepare email** beside an invoice. Check the address and draft, confirm the customer has not paid, and edit the message before sending it from your email app.
6. Use **Export queue** to download the current open-invoice list and share it with your internal finance team.
7. After making changes in your accounting system, export a fresh CSV and import it again. Rows with matching invoice IDs are updated. Invoices missing from a later export are not automatically removed from the local database.

## How the numbers are calculated

- **Outstanding** = invoice amount minus the paid amount. Negative balances are not shown.
- **Past due** means the due date is before the computer's current local date. The due date itself is not yet overdue.
- **Aging** is based on the number of calendar days since the due date.
- **Oldest overdue** is the highest overdue-days value among currently outstanding invoices.
- Queue order is overdue invoices first, followed by the greatest number of days late, then the largest outstanding balance.
- Only invoices with a positive outstanding balance appear in the queue and totals. Fully paid invoices are stored after import but are not shown in the open-invoice view.

## Privacy and safe use

The app listens on `127.0.0.1` only, so it is intended for use on the computer where it is running. There is no sign-in screen or multi-user access control. Do not expose this server directly to the internet or a shared network. Customer and invoice data stays in the local SQLite database; it is not sent to a hosted service by the app.

Invoice data is sensitive business information. Use the app only on a computer you trust, protect that computer, and follow your organization's rules for customer data. Back up `receivables.sqlite3` securely if you need to retain the records. To reset the local data, stop the app and remove that database file; the app will create an empty one the next time it starts.

## Current limitations

- The app relies on a CSV export; it does not connect directly to accounting systems or bank feeds.
- Invoice IDs must be unique and stable between exports.
- It does not automatically delete invoices that are no longer present in a later export. Reset the local database when you intentionally want to start over.
- Reminder text is a starting point and should be checked and edited by a person.
- It has no user accounts, audit log, team collaboration, payment recording screen, or automatic reminders.
