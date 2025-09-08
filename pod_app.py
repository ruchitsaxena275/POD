import streamlit as st
import pandas as pd
from datetime import datetime

# ----------------- PAGE CONFIG -----------------
st.set_page_config(page_title="Plan of Day Dashboard", layout="wide")

# ----------------- DATA STRUCTURE -----------------
# Sample Data (You can connect this to a CSV or database)
shift_data = [
    ["Shift-A", "06:30 TO 15:00", 4, "Sawai, Hemant", "Kishna, Goutam, Ajay, Narendra"],
    ["General Shift", "09:00 TO 18:00", 6, "Sawai, Hemant", "Devisingh, Kanaram, Laxman, Suresh"],
    ["Shift-B", "13:00 TO 21:00", 2, "-", "Narpat, Dinesh"],
    ["Shift-C", "21:00 TO 06:00", 3, "-", "Santosh, Vikram, Navratan"],
    ["Leave", "-", "-", "W/off: Roop Singh, Rajendra", "-"]
]

activity_data = [
    ["Scada monitoring & operations, F&S -A", "Narpat", 1, "33 alarms today"],
    ["Scada monitoring & operations, F&S -B", "Kishna", 1, ""],
    ["Scada monitoring & operations, F&S -C", "Santosh", 1, ""],
    ["Tracker alarm rectification & actuator replacement", "Suresh, Devi", 5, ""],
    ["220kV Lead & dump", "Kanaram", 1, ""],
    ["Trafo WTI & OTI monitoring", "Kanaram, Navratan, Vikram", 2, ""],
    ["Project support", "Kanaram, Dinesh", 2, ""]
]

# Convert to DataFrames
shift_df = pd.DataFrame(shift_data, columns=["Shift Wise Team", "Shift Timing", "Number of Persons", "Roll Employee", "Off Roll Employee"])
activity_df = pd.DataFrame(activity_data, columns=["Daily Routine Activity", "Team Name", "Total Count", "Tracker Alarm"])

# ----------------- HEADER -----------------
today = datetime.today().strftime("%d-%m-%Y")
st.markdown(f"""
    <div style="background:#d32f2f;padding:20px;border-radius:10px;text-align:center;">
        <h1 style="color:white;margin:0;">PLAN OF THE DAY</h1>
        <h3 style="color:white;margin:0;">JUNA Renewable Energy Pvt Ltd</h3>
        <h4 style="color:white;margin:0;">{today}</h4>
    </div>
""", unsafe_allow_html=True)

st.markdown("---")

# ----------------- SHIFT TEAM TABLE -----------------
st.subheader("👷 Shift Wise Team Overview")
st.dataframe(shift_df, use_container_width=True, height=230)

# ----------------- PLAN OF THE DAY -----------------
st.subheader("📋 Plan of The Day Activities")
st.dataframe(activity_df, use_container_width=True, height=280)

# ----------------- KPI SUMMARY -----------------
total_activities = len(activity_df)
total_people = shift_df["Number of Persons"].replace("-", 0).astype(str).str.extract('(\d+)').dropna().astype(int).sum()[0]
alarms = sum(activity_df["Tracker Alarm"].str.extract('(\d+)').dropna()[0].astype(int)) if not activity_df["Tracker Alarm"].isnull().all() else 0

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Activities", total_activities)
with col2:
    st.metric("Total People Deployed", int(total_people))
with col3:
    st.metric("Tracker Alarms Today", int(alarms))

st.markdown("---")

# ----------------- FOOTER -----------------
st.markdown(
    "<div style='text-align:center;color:gray;'>Designed for Solar Plant Daily Ops</div>",
    unsafe_allow_html=True
)
