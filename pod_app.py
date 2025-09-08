import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os

# ----------------- CONFIG -----------------
st.set_page_config(page_title="Plan of Day Dashboard", layout="wide")

DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# ----------------- HELPER FUNCTIONS -----------------
def load_data(date):
    path = os.path.join(DATA_DIR, f"activities_{date}.csv")
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame(columns=[
        "Activity Name", "Location", "Team", "Start Time", "End Time",
        "Priority", "Tools", "Status", "Notes"
    ])

def save_data(date, df):
    path = os.path.join(DATA_DIR, f"activities_{date}.csv")
    df.to_csv(path, index=False)

# ----------------- SIDEBAR -----------------
st.sidebar.title("Plan of Day")
selected_date = st.sidebar.date_input("Select Date", datetime.today())
selected_date_str = selected_date.strftime("%Y-%m-%d")

# ----------------- LOAD DATA -----------------
df = load_data(selected_date_str)

# ----------------- DASHBOARD METRICS -----------------
st.markdown(f"## 📅 Plan of Day - {selected_date_str}")

if not df.empty:
    total_activities = len(df)
    completed = len(df[df["Status"] == "Completed"])
    progress = round((completed / total_activities) * 100, 1) if total_activities > 0 else 0

    # KPI Cards
    kpi1, kpi2, kpi3 = st.columns(3)
    with kpi1:
        st.markdown(
            f'<div style="background:#f9f9f9;padding:20px;border-radius:12px;box-shadow:0 2px 5px rgba(0,0,0,0.1);">'
            f'<h4>Total Activities</h4><h2>{total_activities}</h2></div>',
            unsafe_allow_html=True
        )
    with kpi2:
        st.markdown(
            f'<div style="background:#f9f9f9;padding:20px;border-radius:12px;box-shadow:0 2px 5px rgba(0,0,0,0.1);">'
            f'<h4>Completed</h4><h2>{completed}</h2></div>',
            unsafe_allow_html=True
        )
    with kpi3:
        st.markdown(
            f'<div style="background:#f9f9f9;padding:20px;border-radius:12px;box-shadow:0 2px 5px rgba(0,0,0,0.1);">'
            f'<h4>Progress</h4><h2>{progress}%</h2></div>',
            unsafe_allow_html=True
        )

    st.markdown("---")

    # ----------------- TABLE DASHBOARD -----------------
    st.subheader("📋 Activities Overview")
    st.dataframe(df, use_container_width=True)

    # ----------------- VISUALS -----------------
    st.subheader("📊 Visual Summary")

    # Pie chart for Status
    if not df["Status"].isnull().all():
        pie_fig = px.pie(df, names="Status", title="Activity Status Distribution", hole=0.4)
        st.plotly_chart(pie_fig, use_container_width=True)

else:
    st.info("No activities planned for this day yet. Use the form below to add activities.")

# ----------------- ACTIVITY PLANNER FORM -----------------
st.markdown("## ➕ Add / Edit Activities")

with st.form("activity_form"):
    c1, c2 = st.columns(2)
    with c1:
        activity_name = st.text_input("Activity Name")
        location = st.text_input("Location (Block/Array/Transformer Bay)")
        team = st.text_input("Assigned Team")
        priority = st.selectbox("Priority", ["Low", "Medium", "High"])
    with c2:
        start_time = st.time_input("Start Time", value=datetime.now().time())
        end_time = st.time_input("End Time", value=datetime.now().time())
        status = st.selectbox("Status", ["Planned", "In-Progress", "Completed"])
        tools = st.text_input("Required Tools")
    notes = st.text_area("Notes")

    submitted = st.form_submit_button("Save Activity")
    if submitted:
        new_data = pd.DataFrame([{
            "Activity Name": activity_name,
            "Location": location,
            "Team": team,
            "Start Time": start_time.strftime("%H:%M"),
            "End Time": end_time.strftime("%H:%M"),
            "Priority": priority,
            "Tools": tools,
            "Status": status,
            "Notes": notes
        }])
        df = pd.concat([df, new_data], ignore_index=True)
        save_data(selected_date_str, df)
        st.success("Activity saved successfully!")
        st.experimental_rerun()
