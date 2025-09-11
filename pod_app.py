import streamlit as st
import pandas as pd
from datetime import datetime
import io

# ----------------- PAGE CONFIG -----------------
st.set_page_config(page_title="Solar Plant POD", layout="wide")

# ----------------- SESSION STATE INIT -----------------
if "shifts" not in st.session_state:
    st.session_state.shifts = pd.DataFrame(columns=["Shift", "People", "Manpower Count"])

if "eod" not in st.session_state:
    st.session_state.eod = pd.DataFrame(columns=["Type", "Name", "Status", "Alert Count Balance"])

# ----------------- SIDEBAR INPUT -----------------
st.sidebar.header("📌 Plan of Day (POD)")

# Shift Entry
st.sidebar.subheader("👷 Shift Entry")
shift_name = st.sidebar.text_input("Shift Name")
people = st.sidebar.text_area("People (comma separated)")
if st.sidebar.button("➕ Add Shift"):
    if shift_name and people:
        ppl_list = [p.strip() for p in people.split(",") if p.strip()]
        new_shift = pd.DataFrame([{
            "Shift": shift_name,
            "People": ", ".join(ppl_list),
            "Manpower Count": len(ppl_list)
        }])
        st.session_state.shifts = pd.concat([st.session_state.shifts, new_shift], ignore_index=True)
        st.sidebar.success("✅ Shift added!")

# EOD Entry
st.sidebar.subheader("📋 End of Day (EOD)")
eod_type = st.sidebar.selectbox("Type", ["Activity", "Alert"])
eod_name = st.sidebar.text_input("Name")
status = st.sidebar.selectbox("Status", ["✅ Completed", "❌ Pending"] if eod_type == "Activity"
                              else ["✅ Resolved", "❌ Pending"])

# Handle alert balance
alert_balance = None
if eod_type == "Alert":
    try:
        # Find unresolved balance for same alert name
        previous_alerts = st.session_state.eod[(st.session_state.eod["Type"] == "Alert") &
                                               (st.session_state.eod["Name"] == eod_name)]
        if not previous_alerts.empty:
            last_balance = previous_alerts.iloc[-1]["Alert Count Balance"]
            alert_balance = last_balance - 1 if status == "✅ Resolved" else last_balance
        else:
            # First entry, assume 1 alert
            alert_balance = 0 if status == "✅ Resolved" else 1
    except Exception:
        alert_balance = 1

if st.sidebar.button("➕ Add EOD Entry"):
    if eod_name:
        new_eod = {
            "Type": eod_type,
            "Name": eod_name,
            "Status": status,
            "Alert Count Balance": alert_balance if eod_type == "Alert" else None
        }
        st.session_state.eod = pd.concat([st.session_state.eod, pd.DataFrame([new_eod])], ignore_index=True)
        st.sidebar.success("✅ EOD entry added!")

# ----------------- DASHBOARD METRICS -----------------
st.title("☀️ Solar Plant - Plan of Day Dashboard")

col1, col2, col3, col4, col5, col6 = st.columns(6)

col1.metric("Total Shifts", len(st.session_state.shifts))
col2.metric("Total People", sum(st.session_state.shifts["Manpower Count"]))
col3.metric("Total Activities", len(st.session_state.eod[st.session_state.eod["Type"] == "Activity"]))
col4.metric("Total Alerts", len(st.session_state.eod[st.session_state.eod["Type"] == "Alert"]))
col5.metric("✅ Completed Activities",
            len(st.session_state.eod[(st.session_state.eod["Type"] == "Activity") &
                                     (st.session_state.eod["Status"] == "✅ Completed")]))
col6.metric("❌ Pending Activities",
            len(st.session_state.eod[(st.session_state.eod["Type"] == "Activity") &
                                     (st.session_state.eod["Status"] == "❌ Pending")]))


# ----------------- TABLE DISPLAY -----------------
st.subheader("👷 Shift Details")
st.dataframe(st.session_state.shifts, use_container_width=True)

st.subheader("📋 End of Day Report")
st.dataframe(st.session_state.eod, use_container_width=True)

# ----------------- EXPORT OPTION -----------------
st.subheader("📂 Export POD Data")
date_str = datetime.now().strftime("%Y-%m-%d")

output = io.BytesIO()
with pd.ExcelWriter(output, engine="openpyxl") as writer:
    st.session_state.shifts.to_excel(writer, sheet_name="Shifts", index=False)
    st.session_state.eod.to_excel(writer, sheet_name="EOD", index=False)

output.seek(0)

st.download_button(
    label=f"📥 Download POD_{date_str}.xlsx",
    data=output,
    file_name=f"POD_{date_str}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
st.success("✅ POD file ready for download!")

# ----------------- FOOTER -----------------
st.markdown(
    "<div style='text-align:center;color:gray;'>⚡ Designed by Acciona for Solar Plant Daily Operations</div>",
    unsafe_allow_html=True
)
