import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from io import BytesIO
import os

# ----------------- PAGE CONFIG -----------------
st.set_page_config(page_title="Solar POD Dashboard", layout="wide")

# ----------------- AUTO-SAVE CONFIG -----------------
TODAY = datetime.now().strftime("%Y-%m-%d")
DATA_DIR = "pod_data"
os.makedirs(DATA_DIR, exist_ok=True)
FILE_PATH = os.path.join(DATA_DIR, f"POD_{TODAY}.xlsx")

# ----------------- EMPLOYEE LIST -----------------
EMPLOYEE_LIST = [
    "Kishan","Narendra","Roop Singh","Dinesh","Devisingh","Kanaram","Laxman",
    "Suresh","Ajay","Narpat","Mahipal","Santosh","Vikram","Navratan",
    "Rajendra","Gotam","Sawai","Hemant"
]

# ----------------- DEFAULT DATAFRAMES -----------------
default_manpower = pd.DataFrame(columns=["Shift", "No. of Persons", "Employees"])
default_activities = pd.DataFrame(columns=["Activity", "Location", "Shift", "No. of Persons", "Employees"])
default_alerts = pd.DataFrame(columns=["Alert Activity", "Alert Count"])
default_eod = pd.DataFrame(columns=["Type", "Name", "Status", "Remarks", "Alert Count Balance"])

# ----------------- LOAD TODAY'S DATA IF EXISTS -----------------
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

# NEW: Multi-select employee names
selected_employees = st.sidebar.multiselect("Select Employees", EMPLOYEE_LIST)
extra_employees = st.sidebar.text_area("Additional Names (if not in list, comma separated)")
employees = ", ".join(selected_employees + ([extra_employees] if extra_employees else []))

if st.sidebar.button("➕ Add Manpower"):
    new_row = {"Shift": shift, "No. of Persons": manpower_count, "Employees": employees}
    st.session_state.manpower = pd.concat([st.session_state.manpower, pd.DataFrame([new_row])], ignore_index=True)
    save_data()
    st.sidebar.success("Manpower entry added!")

# ---- ACTIVITY ENTRY ----
st.sidebar.subheader("📝 Add Activity")
activity = st.sidebar.text_input("Activity Name")
location = st.sidebar.text_input("Location")
activity_shift = st.sidebar.selectbox("Assign Shift", shifts)
activity_people = st.sidebar.number_input("No. of Persons Assigned", min_value=0, step=1)

# NEW: Multi-select employee names for activity
activity_selected_employees = st.sidebar.multiselect("Select Employees for Activity", EMPLOYEE_LIST)
activity_extra_employees = st.sidebar.text_area("Additional Names (if not in list, comma separated for this activity)")
activity_employees = ", ".join(activity_selected_employees + ([activity_extra_employees] if activity_extra_employees else []))

if st.sidebar.button("➕ Add Activity"):
    new_row = {
        "Activity": activity,
        "Location": location,
        "Shift": activity_shift,
        "No. of Persons": activity_people,
        "Employees": activity_employees
    }
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
if eod_type == "Activity" and not st.session_state.activities.empty:
    eod_name = st.sidebar.selectbox("Select Activity", st.session_state.activities["Activity"].tolist())
elif eod_type == "Alert" and not st.session_state.alerts.empty:
    eod_name = st.sidebar.selectbox("Select Alert", st.session_state.alerts["Alert Activity"].tolist())
    alert_total = int(st.session_state.alerts.loc[st.session_state.alerts["Alert Activity"]==eod_name, "Alert Count"].values[0])
    
    if "Alert Count Balance" in st.session_state.eod.columns and not st.session_state.eod.empty:
        alert_resolved = st.session_state.eod[
            (st.session_state.eod["Type"]=="Alert") &
            (st.session_state.eod["Name"]==eod_name) &
            (st.session_state.eod["Status"]=="✅ Resolved")
        ]["Alert Count Balance"].sum()
    else:
        alert_resolved = 0

    alert_count_balance = max(alert_total - alert_resolved, 0)

if eod_name:
    eod_status_options = ["✅ Completed", "❌ Pending"] if eod_type=="Activity" else ["✅ Resolved", "❌ Pending"]
    eod_status = st.sidebar.radio("Status", eod_status_options)
    eod_remarks = st.sidebar.text_area("Remarks")
    if st.sidebar.button("➕ Add EOD Update"):
        new_row = {
            "Type": eod_type,
            "Name": eod_name,
            "Status": eod_status,
            "Remarks": eod_remarks,
            "Alert Count Balance": alert_count_balance if eod_type=="Alert" else ""
        }
        st.session_state.eod = pd.concat([st.session_state.eod, pd.DataFrame([new_row])], ignore_index=True)
        save_data()
        st.sidebar.success(f"EOD {eod_type} update added!")

# ----------------- HEADER -----------------
today = datetime.today().strftime("%d-%m-%Y")
st.markdown(f"""
    <div style="background:linear-gradient(90deg, #EFEF36, #f44336);padding:15px;border-radius:10px;text-align:center;">
        <h1 style="color:white;margin:0;">☀️ JUNA Plan of Day Dashboard</h1>
        <h3 style="color:white;margin:0;">{today}</h3>
    </div>
""", unsafe_allow_html=True)

st.markdown("---")

# ----------------- KPI CARDS -----------------
total_shifts = len(st.session_state.manpower)
total_people = st.session_state.manpower["No. of Persons"].sum()
total_activities = len(st.session_state.activities)
total_alerts = st.session_state.alerts["Alert Count"].sum() if not st.session_state.alerts.empty else 0

eod = st.session_state.get("eod", pd.DataFrame(columns=["Type","Name","Status","Remarks","Alert Count Balance"]))

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
st.dataframe(st.session_state.manpower, use_container_width=True)

# ----------------- ACTIVITIES TABLE -----------------
st.subheader("📝 Planned Activities")
st.dataframe(st.session_state.activities, use_container_width=True)

# ----------------- EOD TABLE -----------------
st.subheader("📊 End of Day Updates")
st.dataframe(eod, use_container_width=True)

# ----------------- ALERTS BAR CHART -----------------
st.subheader("🚨 Alerts Overview")
if not st.session_state.alerts.empty:
    fig = px.bar(
        st.session_state.alerts,
        x="Alert Activity",
        y="Alert Count",
        text="Alert Count",
        color="Alert Count",
        color_continuous_scale="reds"
    )
    fig.update_layout(yaxis=dict(range=[0, 100], dtick=10), xaxis_title="Alert Activities", yaxis_title="Count")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No alerts added yet.")

# ----------------- SAVE & DOWNLOAD POD -----------------
st.subheader("💾 Save & Download POD + EOD Data")
if st.button("Prepare POD for Download"):
    date_str = datetime.today().strftime("%d-%m-%Y")
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
