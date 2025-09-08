import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# ----------------- PAGE CONFIG -----------------
st.set_page_config(page_title="Solar POD Dashboard", layout="wide")

# ----------------- SESSION STATE -----------------
if "manpower" not in st.session_state:
    st.session_state.manpower = pd.DataFrame(columns=["Shift", "No. of Persons", "Employees"])
if "activities" not in st.session_state:
    st.session_state.activities = pd.DataFrame(columns=["Activity", "Location", "Shift", "No. of Persons", "Employees"])
if "alerts" not in st.session_state:
    st.session_state.alerts = pd.DataFrame(columns=["Alert Activity", "Alert Count"])

# ----------------- SIDEBAR -----------------
st.sidebar.title("⚙️ POD Input Panel")

# ---- SHIFT MANPOWER ENTRY ----
shifts = ["Shift A (06:30-15:00)", "General Shift (09:00-18:00)", 
          "Shift B (13:00-21:00)", "Shift C (21:00-06:00)"]
shift = st.sidebar.selectbox("Select Shift", shifts)
manpower_count = st.sidebar.number_input("Number of Persons", min_value=0, step=1)
employees = st.sidebar.text_area("Employee Names (comma separated)")
if st.sidebar.button("➕ Add Manpower"):
    st.session_state.manpower = pd.concat(
        [st.session_state.manpower, pd.DataFrame([{"Shift": shift, "No. of Persons": manpower_count, "Employees": employees}])],
        ignore_index=True
    )

# ---- ACTIVITY ENTRY ----
activity = st.sidebar.text_input("Activity Name")
location = st.sidebar.text_input("Location")
activity_shift = st.sidebar.selectbox("Assign Shift", shifts)
activity_people = st.sidebar.number_input("No. of Persons Assigned", min_value=0, step=1)
activity_employees = st.sidebar.text_area("Employee Names (comma separated for this activity)")
if st.sidebar.button("➕ Add Activity"):
    new_row = {
        "Activity": activity,
        "Location": location,
        "Shift": activity_shift,
        "No. of Persons": activity_people,
        "Employees": activity_employees
    }
    st.session_state.activities = pd.concat(
        [st.session_state.activities, pd.DataFrame([new_row])],
        ignore_index=True
    )

# ---- ALERT ENTRY ----
alert_name = st.sidebar.text_input("Alert Activity")
alert_count = st.sidebar.number_input("Alert Count", min_value=0, max_value=100, step=1)
if st.sidebar.button("➕ Add Alert"):
    st.session_state.alerts = pd.concat(
        [st.session_state.alerts, pd.DataFrame([{"Alert Activity": alert_name, "Alert Count": alert_count}])],
        ignore_index=True
    )

# ----------------- HEADER -----------------
today = datetime.today().strftime("%d-%m-%Y")
st.markdown(f"""
    <div style="background:linear-gradient(90deg, #ff9800, #f44336);padding:10px;border-radius:8px;text-align:center;">
        <h2 style="color:white;margin:0;">☀️ Solar Plant Plan of Day Dashboard</h2>
        <p style="color:white;margin:0;font-size:14px;">{today}</p>
    </div>
""", unsafe_allow_html=True)

# ----------------- KPI CARDS -----------------
total_shifts = len(st.session_state.manpower)
total_people = st.session_state.manpower["No. of Persons"].sum()
total_activities = len(st.session_state.activities)
total_alerts = st.session_state.alerts["Alert Count"].sum() if not st.session_state.alerts.empty else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Shifts", total_shifts)
col2.metric("People", int(total_people))
col3.metric("Activities", total_activities)
col4.metric("Alerts", int(total_alerts)
