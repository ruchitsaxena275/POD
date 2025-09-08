# Restored the original app structure with fixes for string formatting and enhanced dashboard KPIs.

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.figure_factory as ff
from datetime import datetime, timedelta
import os

# ----------------- CONFIG -----------------
st.set_page_config(page_title="Plan of Day Dashboard", layout="wide")

# ----------------- HELPER FUNCTIONS -----------------
def load_data(file):
    if os.path.exists(file):
        return pd.read_csv(file)
    else:
        return pd.DataFrame()

def save_data(df, file):
    df.to_csv(file, index=False)

# ----------------- SIDEBAR -----------------
st.sidebar.title("Navigation")
menu = st.sidebar.radio("Go to:", ["Dashboard", "Activity Planner", "Manpower", "Reports", "Settings"])

selected_date = st.sidebar.date_input("Select Date", datetime.today())

# ----------------- DATA FILES -----------------
data_dir = "data"
os.makedirs(data_dir, exist_ok=True)

activity_file = f"{data_dir}/activities_{selected_date}.csv"
manpower_file = f"{data_dir}/manpower_{selected_date}.csv"

# ----------------- DASHBOARD -----------------
if menu == "Dashboard":
    st.title("🌞 Plan of Day Dashboard")

    activities = load_data(activity_file)
    manpower = load_data(manpower_file)

    total_acts = len(activities)
    total_mp = len(manpower)
    planned_hours = activities['Planned Hours'].sum() if 'Planned Hours' in activities else 0
    completed_hours = activities['Completed Hours'].sum() if 'Completed Hours' in activities else 0
    progress = int((completed_hours / planned_hours * 100) if planned_hours > 0 else 0)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="kpi"><div class="small-muted">Total Activities</div><div class="value">{total_acts}</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="kpi"><div class="small-muted">Manpower Deployed</div><div class="value">{total_mp}</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="kpi"><div class="small-muted">Hours Planned</div><div class="value">{planned_hours}</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="kpi"><div class="small-muted">Progress</div><div class="value">{progress}%</div></div>', unsafe_allow_html=True)

    st.subheader("Activity Status Chart")
    if not activities.empty and 'Status' in activities:
        status_counts = activities['Status'].value_counts()
        fig = px.bar(status_counts, x=status_counts.index, y=status_counts.values, color=status_counts.index,
                     labels={'x': 'Status', 'y': 'Count'}, title="Planned vs Completed Activities")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Manpower Distribution")
    if not manpower.empty and 'Role' in manpower:
        role_counts = manpower['Role'].value_counts()
        fig = px.pie(values=role_counts.values, names=role_counts.index, title="Manpower Allocation by Role")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Timeline View")
    if not activities.empty and all(col in activities for col in ['Activity Name', 'Start Time', 'End Time']):
        timeline_df = activities.copy()
        timeline_df['Start Time'] = pd.to_datetime(timeline_df['Start Time'])
        timeline_df['End Time'] = pd.to_datetime(timeline_df['End Time'])
        fig = ff.create_gantt(timeline_df[['Activity Name', 'Start Time', 'End Time']], index_col=None, show_colorbar=True, group_tasks=True)
        st.plotly_chart(fig, use_container_width=True)

# ----------------- PLACEHOLDER SECTIONS -----------------
if menu == "Activity Planner":
    st.title("Activity Planner")
    st.info("This section allows adding and editing daily activities.")

if menu == "Manpower":
    st.title("Manpower Allocation")
    st.info("This section will show manpower details.")

if menu == "Reports":
    st.title("Reports")
    st.info("This section will export reports in PDF/Excel.")

if menu == "Settings":
    st.title("Settings")
    st.info("Configure app settings here.")
