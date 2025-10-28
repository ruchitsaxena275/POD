import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
from io import BytesIO
import os

# ----------------- PAGE CONFIG -----------------
st.set_page_config(page_title="Solar POD Dashboard", layout="wide")

# ----------------- AUTO-SAVE CONFIG (With Manual Date Option) -----------------
DATA_DIR = "pod_data"
os.makedirs(DATA_DIR, exist_ok=True)

# Default = today's date
default_date = date.today()

# Sidebar date selection
st.sidebar.markdown("### 📅 Select POD Date")
selected_date = st.sidebar.date_input("Choose POD Date", value=default_date)
TODAY = selected_date.strftime("%Y-%m-%d")

# Dynamic file path
FILE_PATH = os.path.join(DATA_DIR, f"POD_{TODAY}.xlsx")

# ----------------- EMPLOYEE MASTER LIST -----------------
EMPLOYEES = [
    "Kishan","Narendra","Roop Singh","Dinesh","Devisingh","Kanaram","Laxman",
    "Suresh","Ajay","Narpat","Mahipal","Santosh","Vikram","Navratan",
    "Rajendra","Gotam","Sawai","Hemant"
]

# ----------------- DEFAULT DATAFRAMES -----------------
default_manpower = pd.DataFrame(columns=["Shift", "No. of Persons", "Employees"])
default_activities = pd.DataFrame(columns=["Activity", "Location", "Shift", "No. of Persons", "Employees"])
default_alerts = pd.DataFrame(columns=["Alert Activity", "Alert Count"])
default_eod = pd.DataFrame(columns=[
    "Type", "Name", "Status", "Remarks", "Resolved Count", "Alert Count Balance"
])

# ----------------- LOAD SELECTED DATE DATA IF EXISTS -----------------
if os.path.exists(FILE_PATH):
    try:
        with pd.ExcelFile(FILE_PATH) as xls:
            st.session_state.manpower = pd.read_excel(xls, "Manpower")
            st.session_state.activities = pd.read_excel(xls, "Activities")
            st.session_state.alerts = pd.read_excel(xls, "Alerts")
            st.session_state.eod = pd.read_excel(xls, "EOD")
    except Exception:
        st.session_state.manpower = default_manpower.copy()
        st.session_state.activities = default_activities.copy()
        st.session_state.alerts = default_alerts.copy()
        st.session_state.eod = default_eod.copy()
else:
    st.session_state.manpower = default_manpower.copy()
    st.session_state.activities = default_activities.copy()
    st.session_state.alerts = default_alerts.copy()
    st.session_state.eod = default_eod.copy()

# ----------------- HISTORY STACKS FOR UNDO -----------------
if "undo_stack" not in st.session_state:
    st.session_state.undo_stack = {"manpower": [], "activities": []}

# ----------------- SAVE FUNCTION -----------------
def save_data():
    with pd.ExcelWriter(FILE_PATH, engine="openpyxl") as writer:
        st.session_state.manpower.to_excel(writer, sheet_name="Manpower", index=False)
        st.session_state.activities.to_excel(writer, sheet_name="Activities", index=False)
        st.session_state.alerts.to_excel(writer, sheet_name="Alerts", index=False)
        st.session_state.eod.to_excel(writer, sheet_name="EOD", index=False)

# ----------------- POD DATA FOLDER -----------------
folder = "pod_data"
os.makedirs(folder, exist_ok=True)

# ----------------- LOAD PREVIOUS DATA MANUALLY -----------------
st.sidebar.subheader("📂 Load Previous POD Data")
pod_files = [f for f in os.listdir(folder) if f.startswith("POD_") and f.endswith(".xlsx")]
pod_files.sort(reverse=True)

if pod_files:
    selected_file = st.sidebar.selectbox("Select a date to load", pod_files)
    if st.sidebar.button("Load Selected Data"):
        file_path = os.path.join(folder, selected_file)
        xls = pd.ExcelFile(file_path)
        st.session_state.manpower = pd.read_excel(xls, sheet_name="Manpower")
        st.session_state.activities = pd.read_excel(xls, sheet_name="Activities")
        st.session_state.alerts = pd.read_excel(xls, sheet_name="Alerts")
        st.session_state.eod = pd.read_excel(xls, sheet_name="EOD")
        st.sidebar.success(f"✅ Data loaded from {selected_file}")
else:
    st.sidebar.info("No POD data saved yet.")

# ----------------- SIDEBAR INPUT -----------------
st.sidebar.title("⚙️ POD Input Panel")

# ---- SHIFT MANPOWER ENTRY ----
st.sidebar.subheader("👷 Add Manpower (Shift-wise)")
shifts = ["Shift A (06:30-15:00)", "General Shift (09:00-18:00)", 
          "Shift B (13:00-21:00)", "Shift C (21:00-06:00)"]
shift = st.sidebar.selectbox("Select Shift", shifts)
manpower_count = st.sidebar.number_input("Number of Persons", min_value=0, step=1)
emp_selected = st.sidebar.multiselect("Select Employees", EMPLOYEES)
emp_custom = st.sidebar.text_input("Other Names (comma separated)")
final_employees = emp_selected + ([x.strip() for x in emp_custom.split(",")] if emp_custom else [])

if st.sidebar.button("➕ Add Manpower"):
    new_row = {"Shift": shift, "No. of Persons": manpower_count, "Employees": ", ".join(final_employees)}
    st.session_state.undo_stack["manpower"].append(st.session_state.manpower.copy())
    st.session_state.manpower = pd.concat([st.session_state.manpower, pd.DataFrame([new_row])], ignore_index=True)
    save_data()
    st.sidebar.success("Manpower entry added!")

# ---- DELETE MANPOWER ENTRY ----
if not st.session_state.manpower.empty:
    st.sidebar.subheader("🗑️ Delete Manpower Entry")
    manpower_idx = st.sidebar.selectbox(
        "Select entry", 
        st.session_state.manpower.index,
        format_func=lambda i: f"{st.session_state.manpower.at[i,'Shift']} - {st.session_state.manpower.at[i,'Employees']}"
    )
    if st.sidebar.button("❌ Delete Selected Entry"):
        st.session_state.undo_stack["manpower"].append(st.session_state.manpower.copy())
        st.session_state.manpower = st.session_state.manpower.drop(manpower_idx).reset_index(drop=True)
        save_data()
        st.sidebar.success("Entry deleted!")

# ---- ACTIVITY ENTRY ----
st.sidebar.subheader("📝 Add Activity")
activity = st.sidebar.text_input("Activity Name")
location = st.sidebar.text_input("Location")
activity_shift = st.sidebar.selectbox("Assign Shift", shifts)
activity_people = st.sidebar.number_input("No. of Persons Assigned", min_value=0, step=1)
act_emp_selected = st.sidebar.multiselect("Select Employees for Activity", EMPLOYEES)
act_emp_custom = st.sidebar.text_input("Other Names (comma separated for this activity)")
final_act_employees = act_emp_selected + ([x.strip() for x in act_emp_custom.split(",")] if act_emp_custom else [])

if st.sidebar.button("➕ Add Activity"):
    new_row = {
        "Activity": activity,
        "Location": location,
        "Shift": activity_shift,
        "No. of Persons": activity_people,
        "Employees": ", ".join(final_act_employees)
    }
    st.session_state.undo_stack["activities"].append(st.session_state.activities.copy())
    st.session_state.activities = pd.concat([st.session_state.activities, pd.DataFrame([new_row])], ignore_index=True)
    save_data()
    st.sidebar.success("Activity entry added!")

# ---- ALERT ENTRY ----
st.sidebar.subheader("🚨 Add Alert")
alert_name = st.sidebar.text_input("Alert Activity")
alert_count = st.sidebar.number_input("Alert Count", min_value=0, max_value=100, step=1)
if st.sidebar.button("➕ Add Alert"):
    new_row = {"Alert Activity": alert_name, "Alert Count": alert_count}
    st.session_state.alerts = pd.concat([st.session_state.alerts, pd.DataFrame([new_row])], ignore_index=True)
    save_data()
    st.sidebar.success("Alert entry added!")

# ---- EOD ENTRY ----
st.sidebar.subheader("📊 End of Day Update")
eod_type = st.sidebar.radio("Update Type", ["Activity", "Alert"])

eod_name = None
alert_count_balance = None
resolved_count = None

if eod_type == "Activity" and not st.session_state.activities.empty:
    eod_name = st.sidebar.selectbox("Select Activity", st.session_state.activities["Activity"].tolist())

elif eod_type == "Alert" and not st.session_state.alerts.empty:
    eod_name = st.sidebar.selectbox("Select Alert", st.session_state.alerts["Alert Activity"].tolist())
    alert_total = int(
        st.session_state.alerts.loc[
            st.session_state.alerts["Alert Activity"] == eod_name, "Alert Count"
        ].values[0]
    )

    alert_resolved = (
        st.session_state.eod[
            (st.session_state.eod["Type"] == "Alert")
            & (st.session_state.eod["Name"] == eod_name)
        ]["Resolved Count"].sum()
        if "Resolved Count" in st.session_state.eod.columns
        else 0
    )

    alert_balance = max(alert_total - alert_resolved, 0)

    resolved_count = st.sidebar.number_input(
        "Resolved Count (Today)", min_value=0, max_value=alert_balance, step=1
    )
    alert_count_balance = alert_total - (alert_resolved + resolved_count)

if eod_name:
    eod_status_options = (
        ["✅ Completed", "❌ Pending"]
        if eod_type == "Activity"
        else ["✅ Resolved", "❌ Pending"]
    )
    eod_status = st.sidebar.radio("Status", eod_status_options)
    eod_remarks = st.sidebar.text_area("Remarks")

    if st.sidebar.button("➕ Add EOD Update"):
        new_row = {
            "Type": eod_type,
            "Name": eod_name,
            "Status": eod_status,
            "Remarks": eod_remarks,
            "Resolved Count": resolved_count if eod_type == "Alert" else "",
            "Alert Count Balance": alert_count_balance if eod_type == "Alert" else "",
        }

        for col in ["Resolved Count", "Alert Count Balance"]:
            if col not in st.session_state.eod.columns:
                st.session_state.eod[col] = ""

        st.session_state.eod = pd.concat(
            [st.session_state.eod, pd.DataFrame([new_row])], ignore_index=True
        )
        save_data()
        st.sidebar.success(f"EOD {eod_type} update added!")

# ---- UNDO BUTTONS ----
st.sidebar.subheader("↩️ Undo Last Action")
if st.sidebar.button("Undo Last Manpower Action") and st.session_state.undo_stack["manpower"]:
    st.session_state.manpower = st.session_state.undo_stack["manpower"].pop()
    save_data()
    st.sidebar.success("Undid last manpower change!")

if st.sidebar.button("Undo Last Activity Action") and st.session_state.undo_stack["activities"]:
    st.session_state.activities = st.session_state.undo_stack["activities"].pop()
    save_data()
    st.sidebar.success("Undid last activity change!")

# ----------------- HEADER -----------------
display_date = selected_date.strftime("%d-%m-%Y")
st.markdown(f"""
    <div style="background:linear-gradient(90deg, #EFEF36, #f44336);padding:15px;border-radius:10px;text-align:center;">
        <h1 style="color:white;margin:0;">☀️ JUNA Plan of Day Dashboard</h1>
        <h3 style="color:white;margin:0;">{display_date}</h3>
    </div>
""", unsafe_allow_html=True)

st.markdown("---")

# ----------------- KPI CARDS -----------------
total_shifts = len(st.session_state.manpower)
total_people = st.session_state.manpower["No. of Persons"].sum()
total_activities = len(st.session_state.activities)
total_alerts = st.session_state.alerts["Alert Count"].sum() if not st.session_state.alerts.empty else 0

eod = st.session_state.get("eod", pd.DataFrame(columns=["Type","Name","Status","Remarks","Resolved Count","Alert Count Balance"]))
completed_activities = len(eod[(eod.get("Type")=="Activity") & (eod.get("Status")=="✅ Completed")])
pending_activities = len(eod[(eod.get("Type")=="Activity") & (eod.get("Status")=="❌ Pending")])

col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("Total Shifts", total_shifts)
col2.metric("Total People", int(total_people))
col3.metric("Total Activities", total_activities)
col4.metric("Total Alerts", int(total_alerts))
col5.metric("✅ Completed Activities", completed_activities)
col6.metric("❌ Pending Activities", pending_activities)

# ----------------- MANPOWER TABLE -----------------
st.subheader("👷 Shift-wise Manpower Details")
edited_manpower = st.data_editor(st.session_state.manpower, use_container_width=True, num_rows="dynamic")
if st.button("💾 Save Manpower Changes"):
    st.session_state.manpower = edited_manpower.copy()
    save_data()
    st.success("✅ Manpower updated!")

# ----------------- ACTIVITIES TABLE -----------------
st.subheader("📝 Planned Activities")
edited_activities = st.data_editor(st.session_state.activities, use_container_width=True, num_rows="dynamic")
if st.button("💾 Save Activity Changes"):
    st.session_state.activities = edited_activities.copy()
    save_data()
    st.success("✅ Activities updated!")

# ----------------- EOD TABLE -----------------
st.subheader("📊 End of Day Updates")
edited_eod = st.data_editor(eod, use_container_width=True, num_rows="dynamic")
if st.button("💾 Save EOD Changes"):
    st.session_state.eod = edited_eod.copy()
    save_data()
    st.success("✅ EOD updated!")

# ----------------- ALERTS TABLE + GRAPH -----------------
st.subheader("🚨 Alerts Overview (Editable)")
edited_alerts = st.data_editor(
    st.session_state.alerts, use_container_width=True, num_rows="dynamic"
)
if st.button("💾 Save Alerts Changes"):
    st.session_state.alerts = edited_alerts.copy()
    save_data()
    st.success("✅ Alerts updated!")

if not st.session_state.alerts.empty:
    alert_df = st.session_state.alerts.copy()

    if not st.session_state.eod.empty and "Resolved Count" in st.session_state.eod.columns:
        resolved_data = (
            st.session_state.eod[st.session_state.eod["Type"] == "Alert"]
            .groupby("Name")[["Resolved Count", "Alert Count Balance"]]
            .max()
            .reset_index()
            .rename(columns={"Name": "Alert Activity"})
        )
        alert_df = alert_df.merge(resolved_data, on="Alert Activity", how="left").fillna(0)
    else:
        alert_df["Resolved Count"] = 0
        alert_df["Alert Count Balance"] = alert_df["Alert Count"]

    fig = px.bar(
        alert_df,
        y="Alert Activity",
        x=["Resolved Count", "Alert Count Balance"],
        orientation="h",
        title="Alert Status Overview",
        text_auto=True,
        barmode="stack",
        color_discrete_map={"Resolved Count": "green", "Alert Count Balance": "red"},
    )
    fig.update_layout(
        yaxis_title="Alert Activities",
        xaxis_title="Count",
        xaxis=dict(dtick=10),
        legend_title="Alert Status",
        height=500,
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No alerts added yet.")

# ----------------- SAVE & DOWNLOAD POD -----------------
st.subheader("💾 Save & Download POD + EOD Data")
if st.button("Prepare POD for Download"):
    date_str = selected_date.strftime("%d-%m-%Y")
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        st.session_state.manpower.to_excel(writer, sheet_name="Manpower", index=False)
        st.session_state.activities.to_excel(writer, sheet_name="Activities", index=False)
        st.session_state.alerts.to_excel(writer, sheet_name="Alerts", index=False)
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
