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
if st.sidebar.button("➕ Add Activity"):
    st.session_state.activities = pd.concat(
        [st.session_state.activities, pd.DataFrame([{"Activity": activity, "Location": location}])],
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
col4.metric("Alerts", int(total_alerts))

# ----------------- MAIN DASHBOARD -----------------
col_left, col_right = st.columns([1, 1])

with col_left:
    st.markdown("#### 👷 Manpower")
    if not st.session_state.manpower.empty:
        st.dataframe(st.session_state.manpower, height=180)
    else:
        st.info("No manpower data.")

    st.markdown("#### 📝 Activities")
    if not st.session_state.activities.empty:
        st.dataframe(st.session_state.activities, height=180)
    else:
        st.info("No activities.")

with col_right:
    st.markdown("#### 🚨 Alerts")
    if not st.session_state.alerts.empty:
        fig = px.bar(
            st.session_state.alerts,
            x="Alert Activity",
            y="Alert Count",
            text="Alert Count",
            color="Alert Count",
            height=300,
            color_continuous_scale="reds"
        )
        fig.update_layout(margin=dict(l=10, r=10, t=30, b=10), yaxis=dict(range=[0, 100]))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No alerts yet.")

# ----------------- FOOTER -----------------
st.markdown("<div style='text-align:center;font-size:12px;color:gray;'>⚡ Designed with ❤️ for Solar Plant Operations</div>", unsafe_allow_html=True)
