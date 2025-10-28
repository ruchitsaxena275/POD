import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, date
from io import BytesIO
import os

# ----------------- PAGE CONFIG -----------------
st.set_page_config(page_title="Solar POD Dashboard", layout="wide")

# ----------------- AUTO-SAVE CONFIG -----------------
DATA_DIR = "pod_data"
os.makedirs(DATA_DIR, exist_ok=True)

default_date = date.today()
st.sidebar.markdown("### 📅 Select POD Date")
selected_date = st.sidebar.date_input("Choose POD Date", value=default_date)
TODAY = selected_date.strftime("%Y-%m-%d")
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
default_alerts = pd.DataFrame(columns=["Alert Activity", "Alert Count", "Rectified Count", "Alert Balance"])
default_eod = pd.DataFrame(columns=["Type", "Name", "Status", "Remarks", "Alert Count Balance"])

# ----------------- LOAD DATA -----------------
def load_excel_data(path):
    try:
        with pd.ExcelFile(path) as xls:
            manpower = pd.read_excel(xls, "Manpower")
            activities = pd.read_excel(xls, "Activities")
            alerts = pd.read_excel(xls, "Alerts")
            eod = pd.read_excel(xls, "EOD")
        return manpower, activities, alerts, eod
    except Exception:
        return default_manpower.copy(), default_activities.copy(), default_alerts.copy(), default_eod.copy()

if os.path.exists(FILE_PATH):
    st.session_state.manpower, st.session_state.activities, st.session_state.alerts, st.session_state.eod = load_excel_data(FILE_PATH)
else:
    st.session_state.manpower = default_manpower.copy()
    st.session_state.activities = default_activities.copy()
    st.session_state.alerts = default_alerts.copy()
    st.session_state.eod = default_eod.copy()

# ----------------- SAVE FUNCTION -----------------
def save_data():
    with pd.ExcelWriter(FILE_PATH, engine="openpyxl") as writer:
        st.session_state.manpower.to_excel(writer, "Manpower", index=False)
        st.session_state.activities.to_excel(writer, "Activities", index=False)
        st.session_state.alerts.to_excel(writer, "Alerts", index=False)
        st.session_state.eod.to_excel(writer, "EOD", index=False)

# ----------------- SIDEBAR INPUT -----------------
st.sidebar.title("⚙️ POD Input Panel")

# ---- MANPOWER ENTRY ----
st.sidebar.subheader("👷 Add Manpower (Shift-wise)")
shifts = ["Shift A (06:30-15:00)", "General Shift (09:00-18:00)", "Shift B (13:00-21:00)", "Shift C (21:00-06:00)"]
shift = st.sidebar.selectbox("Select Shift", shifts)
count = st.sidebar.number_input("No. of Persons", min_value=0, step=1)
emp_sel = st.sidebar.multiselect("Select Employees", EMPLOYEES)
emp_custom = st.sidebar.text_input("Other Names (comma separated)")
final_emp = emp_sel + ([x.strip() for x in emp_custom.split(",")] if emp_custom else [])

if st.sidebar.button("➕ Add Manpower"):
    new_row = {"Shift": shift, "No. of Persons": count, "Employees": ", ".join(final_emp)}
    st.session_state.manpower = pd.concat([st.session_state.manpower, pd.DataFrame([new_row])], ignore_index=True)
    save_data()
    st.sidebar.success("Manpower entry added!")

# ---- ALERT ENTRY ----
st.sidebar.subheader("🚨 Add Alert")
alert_name = st.sidebar.text_input("Alert Activity")
alert_count = st.sidebar.number_input("Alert Count", min_value=0, max_value=100, step=1)
if st.sidebar.button("➕ Add Alert"):
    new_row = {"Alert Activity": alert_name, "Alert Count": alert_count, "Rectified Count": 0, "Alert Balance": alert_count}
    st.session_state.alerts = pd.concat([st.session_state.alerts, pd.DataFrame([new_row])], ignore_index=True)
    save_data()
    st.sidebar.success("Alert entry added!")

# ---- EOD ENTRY ----
st.sidebar.subheader("📊 End of Day (EOD) Update")
eod_type = st.sidebar.radio("Update Type", ["Activity", "Alert"])
if eod_type == "Activity" and not st.session_state.activities.empty:
    name = st.sidebar.selectbox("Select Activity", st.session_state.activities["Activity"].tolist())
    status = st.sidebar.radio("Status", ["✅ Completed", "❌ Pending"])
    remarks = st.sidebar.text_area("Remarks")
    if st.sidebar.button("➕ Add EOD Activity"):
        new_row = {"Type": "Activity", "Name": name, "Status": status, "Remarks": remarks, "Alert Count Balance": ""}
        st.session_state.eod = pd.concat([st.session_state.eod, pd.DataFrame([new_row])], ignore_index=True)
        save_data()
        st.sidebar.success("EOD activity added!")
elif eod_type == "Alert" and not st.session_state.alerts.empty:
    alert_name = st.sidebar.selectbox("Select Alert", st.session_state.alerts["Alert Activity"].tolist())
    rectified = st.sidebar.number_input("Rectified Count", min_value=0, step=1)
    remarks = st.sidebar.text_area("Remarks for Alert")
    if st.sidebar.button("➕ Add EOD Alert Update"):
        alert_idx = st.session_state.alerts[st.session_state.alerts["Alert Activity"] == alert_name].index[0]
        total_alert = int(st.session_state.alerts.at[alert_idx, "Alert Count"])
        rectified = min(rectified, total_alert)
        balance = total_alert - rectified
        st.session_state.alerts.at[alert_idx, "Rectified Count"] = rectified
        st.session_state.alerts.at[alert_idx, "Alert Balance"] = balance
        new_row = {"Type": "Alert", "Name": alert_name, "Status": f"✅ {rectified} Rectified", "Remarks": remarks, "Alert Count Balance": balance}
        st.session_state.eod = pd.concat([st.session_state.eod, pd.DataFrame([new_row])], ignore_index=True)
        save_data()
        st.sidebar.success("EOD alert update added!")

# ----------------- HEADER -----------------
st.markdown(f"""
    <div style="background:linear-gradient(90deg,#EFEF36,#f44336);padding:15px;border-radius:10px;text-align:center;">
        <h1 style="color:white;margin:0;">☀️ JUNA Plan of Day Dashboard</h1>
        <h3 style="color:white;margin:0;">{selected_date.strftime('%d-%m-%Y')}</h3>
    </div>
""", unsafe_allow_html=True)
st.markdown("---")

# ----------------- KPI CARDS -----------------
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Manpower", len(st.session_state.manpower))
col2.metric("Total Alerts", int(st.session_state.alerts["Alert Count"].sum()) if not st.session_state.alerts.empty else 0)
col3.metric("Rectified Alerts", int(st.session_state.alerts["Rectified Count"].sum()) if not st.session_state.alerts.empty else 0)
col4.metric("Pending Alerts", int(st.session_state.alerts["Alert Balance"].sum()) if not st.session_state.alerts.empty else 0)

# ----------------- DATA EDITORS -----------------
st.subheader("👷 Manpower Details")
st.session_state.manpower = st.data_editor(st.session_state.manpower, use_container_width=True, num_rows="dynamic")

st.subheader("🚨 Alert Overview")
st.session_state.alerts = st.data_editor(st.session_state.alerts, use_container_width=True, num_rows="dynamic")

st.subheader("📊 EOD Updates")
st.session_state.eod = st.data_editor(st.session_state.eod, use_container_width=True, num_rows="dynamic")

if st.button("💾 Save All Changes"):
    save_data()
    st.success("✅ All data saved!")

# ----------------- ALERT GRAPH -----------------
if not st.session_state.alerts.empty:
    df = st.session_state.alerts.copy()
    df["Alert Count"] = pd.to_numeric(df["Alert Count"], errors="coerce").fillna(0)
    df["Rectified Count"] = pd.to_numeric(df["Rectified Count"], errors="coerce").fillna(0)
    df["Alert Balance"] = pd.to_numeric(df["Alert Balance"], errors="coerce").fillna(0)

    fig = go.Figure()
    fig.add_trace(go.Bar(x=df["Alert Activity"], y=df["Alert Balance"], name="Active Alerts", marker_color="red"))
    fig.add_trace(go.Bar(x=df["Alert Activity"], y=df["Rectified Count"], name="Rectified Alerts", marker_color="green"))
    fig.update_layout(barmode="stack", title="Alert Rectification Progress", xaxis_title="Alert Activity", yaxis_title="Count")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No alerts available for chart.")

# ----------------- DOWNLOAD -----------------
st.subheader("📥 Download POD File")
if st.button("Prepare Download"):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        st.session_state.manpower.to_excel(writer, "Manpower", index=False)
        st.session_state.activities.to_excel(writer, "Activities", index=False)
        st.session_state.alerts.to_excel(writer, "Alerts", index=False)
        st.session_state.eod.to_excel(writer, "EOD", index=False)
    output.seek(0)
    st.download_button("📥 Download POD File", data=output, file_name=f"POD_{TODAY}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    st.success("✅ File ready for download!")

st.markdown("<div style='text-align:center;color:gray;'>⚡ Designed by Acciona for Solar Plant Daily Operations</div>", unsafe_allow_html=True)
