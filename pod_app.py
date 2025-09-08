import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.figure_factory as ff
from datetime import datetime, timedelta
import os

# ----------------- CONFIG -----------------
st.set_page_config(page_title="Plan of Day Dashboard", layout="wide")

# Global styles
st.markdown("""
    <style>
        body {
            background: linear-gradient(120deg, #fdfbfb 0%, #ebedee 100%);
            font-family: 'Inter', sans-serif;
        }
        .kpi {
            background: white;
            padding: 20px;
            border-radius: 20px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            text-align: center;
            transition: 0.3s ease;
        }
        .kpi:hover {transform: translateY(-4px);}
        .kpi .small-muted {color: #888; font-size: 14px;}
        .kpi .value {font-size: 28px; font-weight: bold; margin-top: 5px;}
    </style>
""", unsafe_allow_html=True)

# ----------------- DATA -----------------
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

def get_file(date):
    return os.path.join(DATA_DIR, f"pod_{date}.csv")

@st.cache_data
def load_data(date):
    file_path = get_file(date)
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    else:
        return pd.DataFrame(columns=["Activity", "Location", "Team", "Start", "End", "Priority", "Tools", "Status"])

def save_data(df, date):
    df.to_csv(get_file(date), index=False)

# ----------------- SIDEBAR -----------------
with st.sidebar:
    st.title("☀️ POD Dashboard")
    selected_date = st.date_input("Select Date", datetime.today())
    st.markdown("---")
    st.markdown("### Quick Add Activity")
    quick_activity = st.text_input("Activity Name")
    quick_team = st.text_input("Assigned Team")
    if st.button("Add Activity"):
        df = load_data(selected_date)
        new_row = {
            "Activity": quick_activity,
            "Location": "",
            "Team": quick_team,
            "Start": "",
            "End": "",
            "Priority": "Medium",
            "Tools": "",
            "Status": "Planned"
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        save_data(df, selected_date)
        st.success("Activity added!")

# ----------------- MAIN LAYOUT -----------------
st.title("🌞 Plan of Day Dashboard")
df = load_data(selected_date)

# KPI Calculation
total_activities = len(df)
completed = len(df[df['Status'] == 'Completed'])
progress = int((completed / total_activities) * 100) if total_activities > 0 else 0

planned_hours = 0
completed_hours = 0
if not df.empty:
    for _, row in df.iterrows():
        try:
            if row['Start'] and row['End']:
                start = datetime.strptime(row['Start'], '%H:%M')
                end = datetime.strptime(row['End'], '%H:%M')
                hours = (end - start).seconds / 3600
                planned_hours += hours
                if row['Status'] == 'Completed':
                    completed_hours += hours
        except:
            pass

# KPI Row
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f'<div class="kpi"><div class="small-muted">Total Activities</div><div class="value">{total_activities}</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="kpi"><div class="small-muted">Completed</div><div class="value">{completed}</div></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="kpi"><div class="small-muted">Planned Hours</div><div class="value">{planned_hours:.1f}</div></div>', unsafe_allow_html=True)
with c4:
    st.markdown(f'<div class="kpi"><div class="small-muted">Progress</div><div class="value">{progress}%</div></div>', unsafe_allow_html=True)

st.markdown("---")

# ----------------- ACTIVITY PLANNER -----------------
st.subheader("📋 Activity Planner")

if not df.empty:
    edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
    if st.button("Save Changes"):
        save_data(edited_df, selected_date)
        st.success("Changes saved!")
else:
    st.info("No activities yet. Use the sidebar to add one!")

# ----------------- VISUALIZATIONS -----------------
st.markdown("---")
col1, col2 = st.columns([2,1])

with col1:
    st.markdown("### 📊 Planned vs Completed")
    status_counts = df['Status'].value_counts().reset_index()
    status_counts.columns = ['Status', 'Count']
    if not status_counts.empty:
        fig = px.bar(status_counts, x='Status', y='Count', color='Status', text='Count', height=300)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("No data yet.")

with col2:
    st.markdown("### 🕑 Progress Pie")
    if total_activities > 0:
        pie_data = pd.DataFrame({
            'Label': ['Completed', 'Remaining'],
            'Value': [completed, total_activities - completed]
        })
        fig2 = px.pie(pie_data, names='Label', values='Value', color='Label')
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.write("No data yet.")

# ----------------- TIMELINE -----------------
st.markdown("---")
st.subheader("📅 Activity Timeline")
if not df.empty and 'Start' in df and 'End' in df:
    try:
        gantt_data = []
        for _, row in df.iterrows():
            if row['Start'] and row['End']:
                start = datetime.combine(selected_date, datetime.strptime(row['Start'], '%H:%M').time())
                end = datetime.combine(selected_date, datetime.strptime(row['End'], '%H:%M').time())
                gantt_data.append(dict(Task=row['Activity'], Start=start, Finish=end, Resource=row['Team']))
        if gantt_data:
            fig_gantt = ff.create_gantt(gantt_data, index_col='Resource', show_colorbar=True, group_tasks=True)
            st.plotly_chart(fig_gantt, use_container_width=True)
    except Exception as e:
        st.warning(f"Could not render Gantt chart: {e}")
else:
    st.write("Add start and end times to see timeline.")
