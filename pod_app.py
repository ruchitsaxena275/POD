import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
from io import BytesIO
import os

# ----------------- PAGE CONFIG -----------------
st.set_page_config(page_title="Solar POD Dashboard", layout="wide")

# ----------------- AUTO-SAVE CONFIG (With Manual Date Option) -----------------
DATA_DIR = "pod_data"
os.makedirs(DATA_DIR, exist_ok=True)

# Default = today's date
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
default_eod = pd.DataFrame(columns=["Type", "Name", "Status", "Remarks", "Resolved Count", "Alert Count Balance"])

# ----------------- HELPERS -----------------
def ensure_columns(df: pd.DataFrame, cols_with_defaults: dict):
    """Ensure dataframe has columns; if missing add with default value. Return df."""
    for col, default in cols_with_defaults.items():
        if col not in df.columns:
            df[col] = default() if callable(default) else default
    return df

def to_numeric_safe(df: pd.DataFrame, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)
    return df

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

def save_data():
    with pd.ExcelWriter(FILE_PATH, engine="openpyxl") as writer:
        st.session_state.manpower.to_excel(writer, sheet_name="Manpower", index=False)
        st.session_state.activities.to_excel(writer, sheet_name="Activities", index=False)
        st.session_state.alerts.to_excel(writer, sheet_name="Alerts", index=False)
        st.session_state.eod.to_excel(writer, sheet_name="EOD", index=False)

# ----------------- LOAD OR INIT SESSION STATE -----------------
if os.path.exists(FILE_PATH):
    mp, act, alr, eod = load_excel_data(FILE_PATH)
    # Ensure columns exist (backwards compatible)
    alr = ensure_columns(alr, {"Alert Activity": "", "Alert Count": 0, "Rectified Count": 0, "Alert Balance": 0})
    alr = to_numeric_safe(alr, ["Alert Count", "Rectified Count", "Alert Balance"])
    eod = ensure_columns(eod, {"Type": "", "Name": "", "Status": "", "Remarks": "", "Resolved Count": 0, "Alert Count Balance": 0})
    eod = to_numeric_safe(eod, ["Resolved Count", "Alert Count Balance"])
    st.session_state.manpower = mp
    st.session_state.activities = act
    st.session_state.alerts = alr
    st.session_state.eod = eod
else:
    st.session_state.manpower = default_manpower.copy()
    st.session_state.activities = default_activities.copy()
    st.session_state.alerts = default_alerts.copy()
    st.session_state.eod = default_eod.copy()

# ----------------- UNDO STACK -----------------
if "undo_stack" not in st.session_state:
    st.session_state.undo_stack = {"manpower": [], "activities": []}

# ----------------- POD DATA FOLDER (for manual load) -----------------
folder = DATA_DIR
os.makedirs(folder, exist_ok=True)

st.sidebar.subheader("📂 Load Previous POD Data")
pod_files = [f for f in os.listdir(folder) if f.startswith("POD_") and f.endswith(".xlsx")]
pod_files.sort(reverse=True)

if pod_files:
    selected_file = st.sidebar.selectbox("Select a date to load", pod_files)
    if st.sidebar.button("Load Selected Data"):
        file_path = os.path.join(folder, selected_file)
        mp, act, alr, eod = load_excel_data(file_path)
        alr = ensure_columns(alr, {"Alert Activity": "", "Alert Count": 0, "Rectified Count": 0, "Alert Balance": 0})
        alr = to_numeric_safe(alr, ["Alert Count", "Rectified Count", "Alert Balance"])
        eod = ensure_columns(eod, {"Type": "", "Name": "", "Status": "", "Remarks": "", "Resolved Count": 0, "Alert Count Balance": 0})
        eod = to_numeric_safe(eod, ["Resolved Count", "Alert Count Balance"])
        st.session_state.manpower = mp
        st.session_state.activities = act
        st.session_state.alerts = alr
        st.session_state.eod = eod
        st.sidebar.success(f"✅ Data loaded from {selected_file}")
else:
    st.sidebar.info("No POD data saved yet.")

# ----------------- SIDEBAR INPUT -----------------
st.sidebar.title("⚙️ POD Input Panel")

# ---- SHIFT MANPOWER ENTRY ----
st.sidebar.subheader("👷 Add Manpower (Shift-wise)")
shifts = ["Shift A (06:30-15:00)", "General Shift (09:00-18:00)", "Shift B (13:00-21:00)", "Shift C (21:00-06:00)"]
shift = st.sidebar.selectbox("Select Shift", shifts)
manpower_count = st.sidebar.number_input("Number of Persons", min_value=0, step=1)
emp_selected = st.sidebar.multiselect("Select Employees", EMPLOYEES)
emp_custom = st.sidebar.text_input("Other Names (comma separated)")
final_employees = emp_selected + ([x.strip() for x in emp_custom.split(",")] if emp_custom else [])

if st.sidebar.button("➕ Add Manpower"):
    new_row = {"Shift": shift, "No. of Persons": manpower_count, "Employees": ", ".join(final_employees)}
    # push to undo stack
    st.session_state.undo_stack["manpower"].append(st.session_state.manpower.copy())
    st.session_state.manpower = pd.concat([st.session_state.manpower, pd.DataFrame([new_row])], ignore_index=True)
    save_data()
    st.sidebar.success("Manpower entry added!")

# ---- DELETE MANPOWER ENTRY ----
if not st.session_state.manpower.empty:
    st.sidebar.subheader("🗑️ Delete Manpower Entry")
    manpower_idx = st.sidebar.selectbox(
        "Select entry", 
        st.session_state.manpower.index,
        format_func=lambda i: f"{st.session_state.manpower.at[i,'Shift']} - {st.session_state.manpower.at[i,'Employees']}"
    )
    if st.sidebar.button("❌ Delete Selected Entry"):
        st.session_state.undo_stack["manpower"].append(st.session_state.manpower.copy())
        st.session_state.manpower = st.session_state.manpower.drop(manpower_idx).reset_index(drop=True)
        save_data()
        st.sidebar.success("Entry deleted!")

# ---- ACTIVITY ENTRY ----
st.sidebar.subheader("📝 Add Activity")
activity = st.sidebar.text_input("Activity Name")
location = st.sidebar.text_input("Location")
activity_shift = st.sidebar.selectbox("Assign Shift", shifts)
activity_people = st.sidebar.number_input("No. of Persons Assigned", min_value=0, step=1)
act_emp_selected = st.sidebar.multiselect("Select Employees for Activity", EMPLOYEES)
act_emp_custom = st.sidebar.text_input("Other Names (comma separated for this activity)")
final_act_employees = act_emp_selected + ([x.strip() for x in act_emp_custom.split(",")] if act_emp_custom else [])

if st.sidebar.button("➕ Add Activity"):
    new_row = {
        "Activity": activity,
        "Location": location,
        "Shift": activity_shift,
        "No. of Persons": activity_people,
        "Employees": ", ".join(final_act_employees)
    }
    st.session_state.undo_stack["activities"].append(st.session_state.activities.copy())
    st.session_state.activities = pd.concat([st.session_state.activities, pd.DataFrame([new_row])], ignore_index=True)
    save_data()
    st.sidebar.success("Activity entry added!")

# ---- ALERT ENTRY ----
st.sidebar.subheader("🚨 Add Alert")
alert_name = st.sidebar.text_input("Alert Activity")
alert_count = st.sidebar.number_input("Alert Count", min_value=0, max_value=100, step=1)
if st.sidebar.button("➕ Add Alert"):
    new_row = {"Alert Activity": alert_name, "Alert Count": int(alert_count), "Rectified Count": 0, "Alert Balance": int(alert_count)}
    # ensure columns exist then append
    st.session_state.alerts = ensure_columns(st.session_state.alerts, {"Alert Activity": "", "Alert Count": 0, "Rectified Count": 0, "Alert Balance": 0})
    st.session_state.alerts = pd.concat([st.session_state.alerts, pd.DataFrame([new_row])], ignore_index=True)
    st.session_state.alerts = to_numeric_safe(st.session_state.alerts, ["Alert Count", "Rectified Count", "Alert Balance"])
    save_data()
    st.sidebar.success("Alert entry added!")

# ---- EOD ENTRY ----
st.sidebar.subheader("📊 End of Day Update")
eod_type = st.sidebar.radio("Update Type", ["Activity", "Alert"])

eod_name = None
alert_count_balance = None
resolved_count = None

if eod_type == "Activity" and not st.session_state.activities.empty:
    eod_name = st.sidebar.selectbox("Select Activity", st.session_state.activities["Activity"].tolist())

elif eod_type == "Alert" and not st.session_state.alerts.empty:
    eod_name = st.sidebar.selectbox("Select Alert", st.session_state.alerts["Alert Activity"].tolist())
    # ensure numeric columns exist
    st.session_state.alerts = ensure_columns(st.session_state.alerts, {"Alert Activity": "", "Alert Count": 0, "Rectified Count": 0, "Alert Balance": 0})
    st.session_state.alerts = to_numeric_safe(st.session_state.alerts, ["Alert Count", "Rectified Count", "Alert Balance"])

    alert_total = int(st.session_state.alerts.loc[st.session_state.alerts["Alert Activity"]==eod_name, "Alert Count"].values[0])
    alert_resolved_so_far = int(st.session_state.alerts.loc[st.session_state.alerts["Alert Activity"]==eod_name, "Rectified Count"].values[0])
    remaining_possible = max(alert_total - alert_resolved_so_far, 0)

    resolved_count = st.sidebar.number_input("Resolved Count (Today)", min_value=0, max_value=remaining_possible, step=1)
    alert_count_balance = alert_total - (alert_resolved_so_far + int(resolved_count))

if eod_name:
    eod_status_options = ["✅ Completed", "❌ Pending"] if eod_type=="Activity" else ["✅ Resolved", "❌ Pending"]
    eod_status = st.sidebar.radio("Status", eod_status_options)
    eod_remarks = st.sidebar.text_area("Remarks")
    if st.sidebar.button("➕ Add EOD Update"):
        if eod_type == "Alert":
            # update the alerts table: add resolved_count cumulatively and update balance
            idx = st.session_state.alerts[st.session_state.alerts["Alert Activity"]==eod_name].index
            if len(idx) > 0:
                i = idx[0]
                prev_rect = int(st.session_state.alerts.at[i, "Rectified Count"]) if "Rectified Count" in st.session_state.alerts.columns else 0
                prev_rect = max(prev_rect, 0)
                add_rect = int(resolved_count) if resolved_count is not None else 0
                new_rect = min(prev_rect + add_rect, int(st.session_state.alerts.at[i, "Alert Count"]))
                new_balance = int(st.session_state.alerts.at[i, "Alert Count"]) - new_rect

                st.session_state.alerts.at[i, "Rectified Count"] = new_rect
                st.session_state.alerts.at[i, "Alert Balance"] = new_balance

            new_row = {
                "Type": "Alert",
                "Name": eod_name,
                "Status": eod_status if add_rect==0 else f"✅ {add_rect} Resolved",
                "Remarks": eod_remarks,
                "Resolved Count": add_rect,
                "Alert Count Balance": new_balance
            }
            st.session_state.eod = ensure_columns(st.session_state.eod, {"Type": "", "Name": "", "Status": "", "Remarks": "", "Resolved Count": 0, "Alert Count Balance": 0})
            st.session_state.eod = pd.concat([st.session_state.eod, pd.DataFrame([new_row])], ignore_index=True)
        else:
            # Activity EOD
            new_row = {
                "Type": eod_type,
                "Name": eod_name,
                "Status": eod_status,
                "Remarks": eod_remarks,
                "Resolved Count": "",
                "Alert Count Balance": ""
            }
            st.session_state.eod = pd.concat([st.session_state.eod, pd.DataFrame([new_row])], ignore_index=True)

        # coerce numeric columns to safe types
        st.session_state.alerts = ensure_columns(st.session_state.alerts, {"Rectified Count": 0, "Alert Balance": 0})
        st.session_state.alerts = to_numeric_safe(st.session_state.alerts, ["Alert Count", "Rectified Count", "Alert Balance"])
        st.session_state.eod = ensure_columns(st.session_state.eod, {"Resolved Count": 0, "Alert Count Balance": 0})
        st.session_state.eod = to_numeric_safe(st.session_state.eod, ["Resolved Count", "Alert Count Balance"])
        save_data()
        st.sidebar.success(f"EOD {eod_type} update added!")

# ---- UNDO BUTTONS ----
st.sidebar.subheader("↩️ Undo Last Action")
if st.sidebar.button("Undo Last Manpower Action") and st.session_state.undo_stack["manpower"]:
    st.session_state.manpower = st.session_state.undo_stack["manpower"].pop()
    save_data()
    st.sidebar.success("Undid last manpower change!")

if st.sidebar.button("Undo Last Activity Action") and st.session_state.undo_stack["activities"]:
    st.session_state.activities = st.session_state.undo_stack["activities"].pop()
    save_data()
    st.sidebar.success("Undid last activity change!")

# ----------------- HEADER -----------------
display_date = selected_date.strftime("%d-%m-%Y")
st.markdown(f"""
    <div style="background:linear-gradient(90deg, #EFEF36, #f44336);padding:15px;border-radius:10px;text-align:center;">
        <h1 style="color:white;margin:0;">☀️ JUNA Plan of Day Dashboard</h1>
        <h3 style="color:white;margin:0;">{display_date}</h3>
    </div>
""", unsafe_allow_html=True)

st.markdown("---")

# ----------------- KPI CARDS -----------------
# make sure alerts columns exist before summing
st.session_state.alerts = ensure_columns(st.session_state.alerts, {"Alert Count": 0, "Rectified Count": 0, "Alert Balance": 0})
st.session_state.alerts = to_numeric_safe(st.session_state.alerts, ["Alert Count", "Rectified Count", "Alert Balance"])

total_shifts = len(st.session_state.manpower)
total_people = int(st.session_state.manpower["No. of Persons"].sum()) if not st.session_state.manpower.empty else 0
total_activities = len(st.session_state.activities)
total_alerts = int(st.session_state.alerts["Alert Count"].sum()) if not st.session_state.alerts.empty else 0

eod_df = st.session_state.get("eod", pd.DataFrame(columns=["Type","Name","Status","Remarks","Resolved Count","Alert Count Balance"]))
completed_activities = len(eod_df[(eod_df.get("Type")=="Activity") & (eod_df.get("Status")=="✅ Completed")])
pending_activities = len(eod_df[(eod_df.get("Type")=="Activity") & (eod_df.get("Status")=="❌ Pending")])

col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("Total Shifts", total_shifts)
col2.metric("Total People", total_people)
col3.metric("Total Activities", total_activities)
col4.metric("Total Alerts", total_alerts)
col5.metric("✅ Completed Activities", completed_activities)
col6.metric("❌ Pending Activities", pending_activities)

# ----------------- DATA EDITORS -----------------
st.subheader("👷 Shift-wise Manpower Details")
edited_manpower = st.data_editor(st.session_state.manpower, use_container_width=True, num_rows="dynamic")
if st.button("💾 Save Manpower Changes"):
    st.session_state.manpower = edited_manpower.copy()
    save_data()
    st.success("✅ Manpower updated!")

st.subheader("📝 Planned Activities")
edited_activities = st.data_editor(st.session_state.activities, use_container_width=True, num_rows="dynamic")
if st.button("💾 Save Activity Changes"):
    st.session_state.activities = edited_activities.copy()
    save_data()
    st.success("✅ Activities updated!")

st.subheader("📊 End of Day Updates")
edited_eod = st.data_editor(eod_df, use_container_width=True, num_rows="dynamic")
if st.button("💾 Save EOD Changes"):
    st.session_state.eod = edited_eod.copy()
    # ensure numeric columns remain consistent
    st.session_state.eod = ensure_columns(st.session_state.eod, {"Resolved Count": 0, "Alert Count Balance": 0})
    st.session_state.eod = to_numeric_safe(st.session_state.eod, ["Resolved Count", "Alert Count Balance"])
    save_data()
    st.success("✅ EOD updated!")

st.subheader("🚨 Alerts Overview (Editable)")
edited_alerts = st.data_editor(st.session_state.alerts, use_container_width=True, num_rows="dynamic")
if st.button("💾 Save Alerts Changes"):
    st.session_state.alerts = edited_alerts.copy()
    st.session_state.alerts = ensure_columns(st.session_state.alerts, {"Rectified Count": 0, "Alert Balance": 0})
    st.session_state.alerts = to_numeric_safe(st.session_state.alerts, ["Alert Count", "Rectified Count", "Alert Balance"])
    save_data()
    st.success("✅ Alerts updated!")

# ----------------- ALERT CHART (HORIZONTAL STACKED) -----------------
if not st.session_state.alerts.empty:
    alert_df = st.session_state.alerts.copy()
    alert_df = ensure_columns(alert_df, {"Alert Count": 0, "Rectified Count": 0, "Alert Balance": 0})
    alert_df = to_numeric_safe(alert_df, ["Alert Count", "Rectified Count", "Alert Balance"])

    # For display order, reverse so largest on top (optional)
    alert_df = alert_df.sort_values("Alert Count", ascending=False)

    # Build horizontal stacked bar chart with px (colors set)
    fig = px.bar(
        alert_df,
        y="Alert Activity",
        x=["Rectified Count", "Alert Balance"],
        orientation="h",
        text_auto=True,
        barmode="stack",
        labels={"value":"Count", "Alert Activity":"Alert Activity"},
        color_discrete_map={"Rectified Count":"green", "Alert Balance":"red"}
    )
    fig.update_layout(
        title="Alert Status Overview (Rectified vs Pending)",
        xaxis_title="Count",
        yaxis_title="Alert Activity",
        legend_title="Status",
        height=500,
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No alerts added yet.")

# ----------------- SAVE & DOWNLOAD POD -----------------
st.subheader("💾 Save & Download POD + EOD Data")
if st.button("Prepare POD for Download"):
    date_str = selected_date.strftime("%d-%m-%Y")
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
