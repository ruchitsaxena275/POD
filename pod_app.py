
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
    st.session_state.activities = pd.DataFrame(columns=["Activity", "Location"])

if "alerts" not in st.session_state:
    st.session_state.alerts = pd.DataFrame(columns=["Alert Activity", "Alert Count"])

# ----------------- SIDEBAR -----------------
st.sidebar.title("⚙️ POD Input Panel")

# ---- SHIFT MANPOWER ENTRY ----
st.sidebar.subheader("👷 Add Manpower (Shift-wise)")
shifts = ["Shift A (06:30-15:00)", "General Shift (09:00-18:00)", 
          "Shift B (13:00-21:00)", "Shift C (21:00-06:00)"]
shift = st.sidebar.selectbox("Select Shift", shifts)
manpower_count = st.sidebar.number_input("Number of Persons", min_value=0, step=1)
employees = st.sidebar.text_area("Employee Names (comma separated)")
if st.sidebar.button("➕ Add Manpower"):
    new_row = {"Shift": shift, "No. of Persons": manpower_count, "Employees": employees}
    st.session_state.manpower = pd.concat([st.session_state.manpower, pd.DataFrame([new_row])], ignore_index=True)
    st.sidebar.success("Manpower entry added!")

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
        "Employees": activity_employees}
        
# ---- ALERT ENTRY ----
st.sidebar.subheader("🚨 Add Alert")
alert_name = st.sidebar.text_input("Alert Activity")
alert_count = st.sidebar.number_input("Alert Count", min_value=0, max_value=100, step=1)
if st.sidebar.button("➕ Add Alert"):
    new_row = {"Alert Activity": alert_name, "Alert Count": alert_count}
    st.session_state.alerts = pd.concat([st.session_state.alerts, pd.DataFrame([new_row])], ignore_index=True)
    st.sidebar.success("Alert entry added!")

st.sidebar.markdown("---")
st.sidebar.info("Use the panel to add manpower, activities, and alerts. Dashboard updates live!")

# ----------------- HEADER -----------------
today = datetime.today().strftime("%d-%m-%Y")
st.markdown(f"""
    <div style="background:linear-gradient(90deg, #ff9800, #f44336);padding:20px;border-radius:05px;text-align:center;">
        <h1 style="color:white;margin:0;">☀️ Solar Plant Plan of Day Dashboard</h1>
        <h3 style="color:white;margin:0;">{today}</h3>
    </div>
""", unsafe_allow_html=True)

st.markdown("---")

# ----------------- KPI CARDS -----------------
total_shifts = len(st.session_state.manpower)
total_people = st.session_state.manpower["No. of Persons"].sum()
total_activities = len(st.session_state.activities)
total_alerts = st.session_state.alerts["Alert Count"].sum() if not st.session_state.alerts.empty else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Shifts", total_shifts)
col2.metric("Total People", int(total_people))
col3.metric("Total Activities", total_activities)
col4.metric("Total Alerts", int(total_alerts))

# ----------------- MANPOWER TABLE -----------------
st.subheader("👷 Shift-wise Manpower Details")
if not st.session_state.manpower.empty:
    st.dataframe(st.session_state.manpower, use_container_width=True)
else:
    st.info("No manpower data added yet.")

# ----------------- ACTIVITIES TABLE -----------------
st.subheader("📝 Planned Activities")
if not st.session_state.activities.empty:
    st.dataframe(st.session_state.activities, use_container_width=True)
else:
    st.info("No activity data added yet.")

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

# ----------------- FOOTER -----------------
st.markdown(
    "<div style='text-align:center;color:gray;'>⚡ Designed by Acciona for Solar Plant Daily Operations</div>",
    unsafe_allow_html=True
)

