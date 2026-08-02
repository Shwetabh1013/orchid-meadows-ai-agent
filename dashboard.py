"""
Streamlit demo dashboard — shows captured leads and call summaries live.
This is the deliverable that answers "show where the collected lead
information is stored" during the interview.

Run: streamlit run dashboard.py
"""
import json
from pathlib import Path

import streamlit as st

LEADS_FILE = Path(__file__).parent / "data" / "leads.json"

st.set_page_config(page_title="Orchid Meadows — Lead Dashboard", layout="wide")
st.title("Orchid Meadows — AI Calling Agent Dashboard")
st.caption("Live view of leads captured by the calling agent during customer calls.")

if not LEADS_FILE.exists():
    st.info("No leads captured yet. Run agent.py and have a test conversation first.")
else:
    leads = json.loads(LEADS_FILE.read_text())
    st.metric("Total calls with captured data", len(leads))

    for lead in reversed(leads):
        with st.container(border=True):
            cols = st.columns([2, 2, 2, 2])
            cols[0].markdown(f"**Call ID**\n\n{lead.get('call_id', '—')}")
            cols[1].markdown(f"**Name**\n\n{lead.get('customer_name', '—')}")
            cols[2].markdown(f"**Phone**\n\n{lead.get('phone_number', '—')}")
            cols[3].markdown(f"**Intent**\n\n{lead.get('intent', '—')}")

            cols2 = st.columns([2, 2, 2, 2])
            cols2[0].markdown(f"**Location**\n\n{lead.get('preferred_location', '—')}")
            cols2[1].markdown(f"**Configuration**\n\n{lead.get('configuration', '—')}")
            cols2[2].markdown(f"**Budget (INR lakh)**\n\n{lead.get('budget_range_inr_lakh', '—')}")
            cols2[3].markdown(f"**Timeline**\n\n{lead.get('purchase_timeline', '—')}")

            if lead.get("call_summary"):
                st.markdown("**Call summary**")
                st.json(lead["call_summary"])

st.divider()
st.caption(
    "Data source: data/leads.json for this local demo. "
    "Swap in lead_store_sheets.py to persist to Google Sheets instead."
)
