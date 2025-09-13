import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO

# ----------------- PAGE CONFIG -----------------
st.set_page_config(page_title="Solar POD Dashboard", layout="wide")

# ----------------- INIT SESSION STATE -----------------
if "manpower" not in st.session_state:
    st.session_state.manpower = pd.DataFrame(columns=["Name", "Role", "Shift"])

if "activities" not in st.session_state:
    st.session_state.activities = []

if "alerts" not in st.session_state:
    st.session_state.alerts = []

if "eod" not in st.session_state:
    st.session_state.eod = pd.DataFrame(columns=["Type", "Name", "Status", "Alert Count Balance"])

# ----------------- SIDEBAR -----------------
st.sidebar.header("Plan of Day (POD)")

# --- Manpower Section ---
st.sidebar.subheader("👷 Manpower Entry")

with st.sidebar.form("manpower_form", clear_on_submit=True):
    name = st.text_input("Name")
    role = st.text_input("Role")
    shift = st.selectbox("Shift", ["Morning", "Evening", "Night"])
    submit_manpower = st.form_submit_button("➕ Add Manpower")

if submit_manpower and name and role and shift:
    new_row = pd.DataFrame([[name, role, shift]], columns=["Name", "Role", "Shift"])
    st.session_state.manpower = pd.concat([st.session_state.manpower, new_row], ignore_index=True)

# --- Edit/Delete Manpower ---
if not st.session_state.manpower.empty:
    st.sidebar.markdown("### ✏️ Edit / ❌ Delete Manpower")
    manpower_idx = st.sidebar.selectbox("Select entry", st.session_state.manpower.index, format_func=lambda i: f"{st.session_state.manpower.at[i,'Name']} ({st.session_state.manpower.at[i,'Shift']})")

    # Prefill edit form
    edit_name = st.sidebar.text_input("Edit Name", st.session_state.manpower.at[manpower_idx, "Name"])
    edit_role = st.sidebar.text_input("Edit Role", st.session_state.manpower.at[manpower_idx, "Role"])
    edit_shift = st.sidebar.selectbox("Edit Shift", ["Morning", "Evening", "Night"], index=["Morning", "Evening", "Night"].index(st.session_state.manpower.at[manpower_idx, "Shift"]))

    if st.sidebar.button("💾 Save Changes"):
        st.session_state.manpower.at[manpower_idx, "Name"] = edit_name
        st.session_state.manpower.at[manpower_idx, "Role"] = edit_role
        st.session_state.manpower.at[manpower_idx, "Shift"] = edit_shift
        st.sidebar.success("Manpower updated ✅")

    if st.sidebar.button("🗑️ Delete Entry"):
        st.session_state.manpower = st.session_state.manpower.drop(manpower_idx).reset_index(drop=True)
        st.sidebar.warning("Manpower entry deleted ❌")

# --- Activities Section ---
st.sidebar.subheader("📝 Activities")
activity = st.sidebar.text_input("Add Activity")
if st.sidebar.button("➕ Add Activity") and activity:
    st.session_state.activities.append(activity)

# --- Alerts Section ---
st.sidebar.subheader("🚨 Alerts")
alert = st.sidebar.text_input("Add Alert")
alert_count = st.sidebar.number_input("Alert Count", min_value=1, step=1)
if st.sidebar.button("➕ Add Alert") and alert:
    st.session_state.alerts.append((alert, alert_count))

# --- EOD Section ---
st.sidebar.subheader("📌 End of Day (EOD)")
eod_name = st.sidebar.text_input("EOD Name")
eod_type = st.sidebar.selectbox("Type", ["Activity", "Alert"])
eod_status = st.sidebar.selectbox("Status", ["✅ Completed", "❌ Pending", "✅ Resolved"])
alert_balance = st.sidebar.number_input("Alert Count Balance", min_value=0, step=1, value=0)

if st.sidebar.button("📥 Add to EOD") and eod_name:
    new_row = pd.DataFrame([[eod_type, eod_name, eod_status, alert_balance]],
                           columns=["Type", "Name", "Status", "Alert Count Balance"])
    st.session_state.eod = pd.concat([st.session_state.eod, new_row], ignore_index=True)

# ----------------- MAIN PAGE -----------------
st.title("📊 Solar POD Dashboard")

col1, col2, col3, col4 = st.columns(4)

# Metrics
col1.metric("Manpower", len(st.session_state.manpower))
col2.metric("Activities Planned", len(st.session_state.activities))
col3.metric("Alerts Raised", sum(c for _, c in st.session_state.alerts))
completed_activities = len(st.session_state.eod[(st.session_state.eod["Type"]=="Activity") & (st.session_state.eod["Status"]=="✅ Completed")])
col4.metric("Activities Completed", completed_activities)

# ----------------- DATA TABLES -----------------
st.subheader("👷 Manpower Allocation")
st.dataframe(st.session_state.manpower, use_container_width=True)

st.subheader("📝 Activities")
st.table(pd.DataFrame(st.session_state.activities, columns=["Activity"]))

st.subheader("🚨 Alerts")
st.table(pd.DataFrame(st.session_state.alerts, columns=["Alert", "Count"]))

st.subheader("📌 End of Day (EOD)")
st.dataframe(st.session_state.eod, use_container_width=True)

# ----------------- EXPORT TO EXCEL -----------------
def convert_df_to_excel():
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        st.session_state.manpower.to_excel(writer, index=False, sheet_name="Manpower")
        pd.DataFrame(st.session_state.activities, columns=["Activity"]).to_excel(writer, index=False, sheet_name="Activities")
        pd.DataFrame(st.session_state.alerts, columns=["Alert", "Count"]).to_excel(writer, index=False, sheet_name="Alerts")
        st.session_state.eod.to_excel(writer, index=False, sheet_name="EOD")
    return output.getvalue()

date_str = datetime.now().strftime("%Y-%m-%d")
excel_data = convert_df_to_excel()
st.download_button(
    label="📥 Download POD Report",
    data=excel_data,
    file_name=f"POD_{date_str}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
