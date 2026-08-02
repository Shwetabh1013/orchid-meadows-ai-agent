"""
Optional: sync leads to a Google Sheet instead of local JSON.

Setup (do this once):
1. Create a Google Cloud service account, enable the Sheets API.
2. Download the service account JSON key, save as service_account.json
   in this folder (keep it out of git — add to .gitignore).
3. Create a Google Sheet, share it with the service account's email
   (looks like xxx@yyy.iam.gserviceaccount.com) as Editor.
4. Put the sheet's ID (from its URL) into SHEET_ID below.

Then in agent.py, replace the `append_lead_record` local-JSON call with
`append_lead_row(record, call_id)` from this module.
"""
import gspread
from google.oauth2.service_account import Credentials

SHEET_ID = "PUT_YOUR_GOOGLE_SHEET_ID_HERE"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
HEADERS = [
    "call_id", "updated_at", "customer_name", "phone_number", "intent",
    "preferred_location", "property_type", "configuration",
    "budget_range_inr_lakh", "purchase_timeline", "notes",
]


def _get_worksheet():
    creds = Credentials.from_service_account_file("service_account.json", scopes=SCOPES)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID).sheet1
    if sheet.row_values(1) != HEADERS:
        sheet.update("A1", [HEADERS])
    return sheet


def append_lead_row(record: dict, call_id: str):
    sheet = _get_worksheet()
    existing = sheet.get_all_records()
    row_values = [record.get(h, "") for h in HEADERS]
    row_values[0] = call_id

    for idx, row in enumerate(existing, start=2):  # header is row 1
        if row.get("call_id") == call_id:
            sheet.update(f"A{idx}", [row_values])
            return
    sheet.append_row(row_values)
