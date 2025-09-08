import streamlit as st
import pandas as pd
from datetime import datetime

# ----------------- PAGE CONFIG -----------------
st.set_page_config(page_title="Plan of Day Dashboard", layout="wide")

# ----------------- SESSION STATE -----------------
if "shift_df" not in st.session_state:
    st.session_state.shift_df = pd.DataFrame(columns=["Shift Wise Team", "Shift Timing", "Number of Persons", "Roll Employee", "Off Roll Employee"])

if "activity_df" not in st.session_state:
    st.session_state.activity_df = pd.DataFrame(columns=["Daily Routine Activity", "Team Name", "Total Count", "Tracker Alarm"])

shift_df = st.session_state.shift_df
activity_df = st.session_state.activity_df

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

# ----------------- SHIFT ENTRY FORM -----------------
st.subheader("👷 Add/Update Shift Details")
with st.expander("➕ Add New Shift Entry"):
    with st.form("shift_form", clear_on_submit=True):
        shift = st.text_input("Shift Wise Team")
        timing = st.text_input("Shift Timing (e.g., 06:30 TO 15:00)")
        persons = st.number_input("Number of Persons", min_value=0, step=1)
        roll_emp = st.text_area("Roll Employee Names")
        off_roll_emp = st.text_area("Off Roll Employee Names")
        submitted = st.form_submit_button("Add Shift Entry")
        if submitted:
            new_entry = {"Shift Wise Team": shift, "Shift Timing": timing,
                         "Number of Persons": persons, "Roll Employee": roll_emp,
                         "Off Roll Employee": off_roll_emp}
            st.session_state.shift_df = pd.concat([shift_df, pd.DataFrame([new_entry])], ignore_index=True)
            st.success("✅ Shift entry added!")

# ----------------- ACTIVITY ENTRY FORM -----------------
st.subheader("📋 Add/Update Daily Activities")
with st.expander("➕ Add New Activity Entry"):
    with st.form("activity_form", clear_on_submit=True):
        activity = st.text_input("Daily Routine Activity")
        team = st.text_input("Team Name")
        count = st.number_input("Total Count", min_value=0, step=1)
        alarm = st.text_input("Tracker Alarm (e.g., 33 alarms today)")
        submitted_act = st.form_submit_button("Add Activity")
        if submitted_act:
            new_activity = {"Daily Routine Activity": activity, "Team Name": team,
                            "Total Count": count, "Tracker Alarm": alarm}
            st.session_state.activity_df = pd.concat([activity_df, pd.DataFrame([new_activity])], ignore_index=True)
            st.success("✅ Activity entry added!")

# ----------------- DISPLAY TABLES -----------------
st.subheader("📊 Shift Wise Team Overview")
st.dataframe(st.session_state.shift_df, use_container_width=True, height=230)

st.subheader("📊 Plan of The Day Activities")
st.dataframe(st.session_state.activity_df, use_container_width=True, height=280)

# ----------------- KPI SUMMARY -----------------
total_activities = len(activity_df)
total_people = activity_df["Total Count"].sum()
alarms = sum(activity_df["Tracker Alarm"].str.extract('(\d+)').dropna()[0].astype(int)) if not activity_df["Tracker Alarm"].isnull().all() else 0

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Activities", total_activities)
with col2:
    st.metric("Total People Deployed", int(total_people))
with col3:
    st.metric("Tracker Alarms Today", int(alarms))

# ----------------- EXPORT BUTTONS -----------------
st.markdown("---")
col1, col2 = st.columns(2)
with col1:
    st.download_button(
        "📥 Download Shift Data (CSV)",
        data=st.session_state.shift_df.to_csv(index=False),
        file_name=f"shift_data_{today}.csv",
        mime="text/csv"
    )
with col2:
    st.download_button(
        "📥 Download Activity Data (CSV)",
        data=st.session_state.activity_df.to_csv(index=False),
        file_name=f"activity_data_{today}.csv",
        mime="text/csv"
    )

# ----------------- FOOTER -----------------
st.markdown(
    "<div style='text-align:center;color:gray;'>Designed with ❤️ for Solar Plant Daily Ops</div>",
    unsafe_allow_html=True
)
