# Streamlit POD (Plan of Day) – Solar Plant Dashboard
# ---------------------------------------------------
# Author: ChatGPT (GPT-5 Thinking)
# Description:
#   A premium-looking Streamlit web app to plan and monitor day-wise activities
#   for a solar power plant: activities, manpower, resources, timeline, and reports.
#   Built with clean UI/UX, soft shadows, gradient headers, and interactive widgets.
#
# ✅ Highlights
#   - Activity Planner (add/edit/delete, status, priority, notes, tools)
#   - Manpower Allocation (roles/teams, auto team counts, pie chart)
#   - Resource Tracker (tools/vehicles/equipment, overbooking warnings)
#   - Timeline (Gantt-style via Plotly)
#   - Daily Summary cards + KPIs + progress bars
#   - Filters (Block/Team/Status) + Search + Quick Add form
#   - Data persistence to CSV (per-day) + optional Google Sheets hooks
#   - Exports: PDF (ReportLab) + Excel (multi-sheet)
#   - Optional Dark Mode styling
#
# ⚠️ Note on libraries: Streamlit is Python-first; React libraries like shadcn/ui,
#   lucide-react, recharts, and Framer Motion are not directly usable here. We
#   emulate a modern SaaS look with custom CSS and Plotly animations.
#
# Requirements (add to requirements.txt):
#   streamlit
#   pandas
#   plotly
#   reportlab
#   pillow
#
# Optional (for Google Sheets persistence; requires credentials):
#   gspread
#   oauth2client

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, time, timedelta
from io import BytesIO
import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image

APP_TITLE = "POD – Plan of Day (Solar)"
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# -------------------- Theming & CSS --------------------
PRIMARY_GRADIENT = "linear-gradient(135deg, #ffb703 0%, #fb8500 40%, #219ebc 100%)"
CARD_CSS = """
<style>
:root {
  --card-bg: rgba(255,255,255,0.75);
  --card-border: rgba(0,0,0,0.06);
  --text: #0f172a;
  --muted: #475569;
  --accent: #fb8500;
}

html.dark-mode {
  --card-bg: rgba(15,23,42,0.65);
  --card-border: rgba(255,255,255,0.08);
  --text: #e2e8f0;
  --muted: #94a3b8;
  --accent: #ffd166;
}

/***** App base *****/
.main > div {padding-top: 0 !important;}
.block-container {padding-top: 1.2rem;}

/***** Header *****/
.pod-hero {
  background: %s;
  color: white;
  padding: 18px 20px;
  border-radius: 18px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.25);
  position: relative;
  overflow: hidden;
}
.pod-hero h1 {margin: 0; font-size: 1.9rem; letter-spacing: .2px;}
.pod-hero p {margin: 2px 0 0; opacity: .95}
.pod-hero .sun {position:absolute; right:-40px; top:-40px; width:160px; height:160px; border-radius:9999px; background:rgba(255,255,255,0.2); filter: blur(6px);}

/***** Cards *****/
.pod-card {
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: 16px;
  padding: 14px 14px 8px 14px;
  box-shadow: 0 8px 26px rgba(2,8,23,0.06);
  backdrop-filter: blur(8px);
}
.pod-card h3 {margin-top: 0;}
.small-muted {color: var(--muted); font-size: 0.88rem}

/***** KPIs *****/
.kpi {display:flex; align-items:center; gap:10px;}
.kpi .dot {width:10px; height:10px; border-radius:9999px; background:var(--accent);}
.kpi .value {font-weight:700; font-size:1.25rem; color:var(--text)}

/***** Buttons *****/
.stButton>button {
  border-radius: 12px; padding: 8px 14px; border: 1px solid rgba(0,0,0,.08);
  box-shadow: 0 6px 16px rgba(2,8,23,0.06); font-weight:600;
}

/***** Data Editor tweaks *****/
.stDataFrame, .stDataEditor {border-radius: 12px; overflow:hidden;}

</style>
""" % PRIMARY_GRADIENT

st.set_page_config(page_title=APP_TITLE, page_icon="☀️", layout="wide")
st.markdown(CARD_CSS, unsafe_allow_html=True)

# -------------------- State & Storage Helpers --------------------

def _date_key(d: date) -> str:
    return d.strftime("%Y-%m-%d")

@st.cache_data(show_spinner=False)
def _path(prefix: str, day: date) -> str:
    return os.path.join(DATA_DIR, f"{prefix}_{_date_key(day)}.csv")

DEFAULT_ACTIVITIES = pd.DataFrame([
    {
        "Activity Name": "String testing – Block A",
        "Location": "Block A / Array 12",
        "Assigned Team": "Team Alpha",
        "Start Time": "09:00",
        "End Time": "12:30",
        "Priority": "High",
        "Required Tools": "Clamp meter, IR camera",
        "Notes": "Focus on low-current strings",
        "Status": "Planned",
        "Progress %": 0,
        "Hours": 3.5,
    }
])

DEFAULT_MANPOWER = pd.DataFrame([
    {"Name": "Ravi Kumar", "Role": "Technician", "Team": "Team Alpha"},
    {"Name": "Nisha Patel", "Role": "Engineer", "Team": "Team Alpha"},
    {"Name": "Amit Singh", "Role": "Supervisor", "Team": "Team Beta"},
])

DEFAULT_RESOURCES = pd.DataFrame([
    {"Resource": "IR camera #2", "Type": "Equipment", "Assigned To": "String testing – Block A"},
    {"Resource": "Pick-up #7", "Type": "Vehicle", "Assigned To": "String testing – Block A"},
])

COLUMNS_ACT = [
    "Activity Name", "Location", "Assigned Team", "Start Time", "End Time",
    "Priority", "Required Tools", "Notes", "Status", "Progress %", "Hours"
]

COLUMNS_MP = ["Name", "Role", "Team"]
COLUMNS_RES = ["Resource", "Type", "Assigned To"]

PRIORITY_OPTIONS = ["Low", "Medium", "High", "Critical"]
STATUS_OPTIONS = ["Planned", "In-Progress", "Completed", "On-Hold"]
ROLE_OPTIONS = ["Technician", "Engineer", "Supervisor", "Operator", "Helper"]


def load_or_seed(day: date):
    ap = _path("activities", day)
    mp = _path("manpower", day)
    rs = _path("resources", day)

    if os.path.exists(ap):
        activities = pd.read_csv(ap)
    else:
        activities = DEFAULT_ACTIVITIES.copy()

    if os.path.exists(mp):
        manpower = pd.read_csv(mp)
    else:
        manpower = DEFAULT_MANPOWER.copy()

    if os.path.exists(rs):
        resources = pd.read_csv(rs)
    else:
        resources = DEFAULT_RESOURCES.copy()

    # Ensure columns exist
    activities = activities.reindex(columns=COLUMNS_ACT, fill_value="")
    manpower = manpower.reindex(columns=COLUMNS_MP, fill_value="")
    resources = resources.reindex(columns=COLUMNS_RES, fill_value="")

    return activities, manpower, resources


def persist(day: date, activities: pd.DataFrame, manpower: pd.DataFrame, resources: pd.DataFrame):
    activities.to_csv(_path("activities", day), index=False)
    manpower.to_csv(_path("manpower", day), index=False)
    resources.to_csv(_path("resources", day), index=False)

# -------------------- Topbar / Global Controls --------------------

with st.container():
    st.markdown('<div class="pod-hero">', unsafe_allow_html=True)
    colh1, colh2 = st.columns([4, 3])
    with colh1:
        st.markdown(f"<h1>{APP_TITLE}</h1>", unsafe_allow_html=True)
        st.markdown("<p class='small-muted'>Plan, allocate, and track your solar plant operations — fast.</p>", unsafe_allow_html=True)
    with colh2:
        st.write("")
        st.write("")
        with st.container():
            cc1, cc2, cc3 = st.columns([1.2,1,1])
            with cc1:
                selected_date = st.date_input("Date", value=date.today(), format="DD-MM-YYYY")
            with cc2:
                dark_mode = st.toggle("Dark Mode", value=False)
            with cc3:
                st.session_state.setdefault("_export_click", False)
                export_clicked = st.button("Export Summary")
    st.markdown('<div class="sun"></div></div>', unsafe_allow_html=True)

# Apply dark mode class
if dark_mode:
    st.markdown("""
        <script>
        const htmlEl = window.parent.document.querySelector('html');
        if (htmlEl && !htmlEl.classList.contains('dark-mode')) { htmlEl.classList.add('dark-mode'); }
        </script>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
        <script>
        const htmlEl = window.parent.document.querySelector('html');
        if (htmlEl && htmlEl.classList.contains('dark-mode')) { htmlEl.classList.remove('dark-mode'); }
        </script>
    """, unsafe_allow_html=True)

activities, manpower, resources = load_or_seed(selected_date)

# -------------------- Sidebar Navigation --------------------
st.sidebar.title("☀️ POD Navigation")
nav = st.sidebar.radio("Go to", [
    "Dashboard", "Activity Planner", "Manpower", "Resources", "Timeline", "Reports", "Settings"
], index=0)

# Quick Add form
with st.sidebar.expander("⚡ Quick Add Activity", expanded=False):
    with st.form("quick_add"):
        qa_name = st.text_input("Activity Name")
        qa_loc = st.text_input("Location (Block/Array/Transformer)")
        qa_team = st.text_input("Assigned Team", value="Team Alpha")
        qa_st = st.time_input("Start", value=time(9,0))
        qa_et = st.time_input("End", value=time(11,0))
        qa_pr = st.selectbox("Priority", PRIORITY_OPTIONS, index=1)
        qa_status = st.selectbox("Status", STATUS_OPTIONS, index=0)
        qa_tools = st.text_input("Required Tools")
        qa_notes = st.text_area("Notes")
        add_now = st.form_submit_button("Add to Plan")
    if add_now and qa_name:
        new_row = {
            "Activity Name": qa_name,
            "Location": qa_loc,
            "Assigned Team": qa_team,
            "Start Time": qa_st.strftime('%H:%M'),
            "End Time": qa_et.strftime('%H:%M'),
            "Priority": qa_pr,
            "Required Tools": qa_tools,
            "Notes": qa_notes,
            "Status": qa_status,
            "Progress %": 0,
            "Hours": round((datetime.combine(date.today(), qa_et) - datetime.combine(date.today(), qa_st)).seconds/3600, 2)
        }
        activities = pd.concat([activities, pd.DataFrame([new_row])], ignore_index=True)
        persist(selected_date, activities, manpower, resources)
        st.success("Activity added.")

# -------------------- Filters & Search --------------------
with st.container():
    st.markdown('<div class="pod-card">', unsafe_allow_html=True)
    cf1, cf2, cf3, cf4 = st.columns([1.2,1.2,1.2,2])
    with cf1:
        blocks = sorted({b.split('/')[0].strip() for b in activities['Location'].astype(str) if b})
        f_block = st.multiselect("Filter: Block", options=blocks, default=[])
    with cf2:
        teams = sorted(activities['Assigned Team'].dropna().unique())
        f_team = st.multiselect("Filter: Team", options=teams, default=[])
    with cf3:
        f_status = st.multiselect("Filter: Status", options=STATUS_OPTIONS, default=[])
    with cf4:
        f_search = st.text_input("Search activity or notes…")
    st.markdown('</div>', unsafe_allow_html=True)

# Apply filters
mask = pd.Series([True]*len(activities))
if f_block:
    mask &= activities['Location'].astype(str).str.contains('|'.join([f"^{b.strip()}" for b in f_block]), case=False, regex=True)
if f_team:
    mask &= activities['Assigned Team'].isin(f_team)
if f_status:
    mask &= activities['Status'].isin(f_status)
if f_search:
    s = f_search.strip().lower()
    mask &= activities.apply(lambda r: s in str(r['Activity Name']).lower() or s in str(r['Notes']).lower(), axis=1)

filtered_activities = activities[mask].reset_index(drop=True)

# -------------------- Dashboard --------------------
if nav == "Dashboard":
    st.markdown('<div class="pod-card">', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    total_acts = len(activities)
    total_mp = len(manpower)
    planned_hours = round(activities['Hours'].fillna(0).sum(), 2)
    completed_hours = round(activities.query("Status=='Completed'")['Hours'].fillna(0).sum(), 2)
    progress = 0 if total_acts==0 else int(100*len(activities.query("Status=='Completed'")) / total_acts)

    with c1:
        st.markdown('<div class="kpi"><div class="dot"></div><div><div class="small-muted">Total Activities</div><div class="value">%d</div></div></div>' % total_acts, unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="kpi"><div class="dot"></div><div><div class="small-muted">Manpower Deployed</div><div class="value">%d</div></div></div>' % total_mp, unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="kpi"><div class="small-muted">Hours Planned</div><div class="value">%.2f</div>' % planned_hours, unsafe_allow_html=True)
    with c4:
        st.markdown(
        f'<div class="kpi"><div class="small-muted">% Progress</div>'
        f'<div class="value">{progress}%</div></div>',
        unsafe_allow_html=True
    )



    # Charts row
    st.write("")
    colA, colB = st.columns([1.2, 1])

    with colA:
        status_counts = activities['Status'].value_counts().reindex(STATUS_OPTIONS, fill_value=0)
        bar = px.bar(status_counts, title="Planned vs In-Progress vs Completed", labels={"value":"Activities", "index":"Status"})
        bar.update_layout(margin=dict(l=10,r=10,t=40,b=10), height=360)
        st.plotly_chart(bar, use_container_width=True)

    with colB:
        role_counts = manpower['Role'].value_counts()
        pie = px.pie(values=role_counts.values, names=role_counts.index, title="Manpower by Role", hole=0.45)
        pie.update_layout(margin=dict(l=10,r=10,t=40,b=10), height=360)
        st.plotly_chart(pie, use_container_width=True)

    # Activity list with progress
    st.write("")
    st.markdown('<div class="pod-card">', unsafe_allow_html=True)
    st.subheader("Activity Progress")
    for i, row in filtered_activities.iterrows():
        with st.expander(f"{row['Activity Name']} — {row['Status']} ({row['Priority']})"):
            cols = st.columns([1,1,1,1])
            cols[0].markdown(f"**Team**: {row['Assigned Team']}")
            cols[1].markdown(f"**Location**: {row['Location']}")
            cols[2].markdown(f"**Start**: {row['Start Time']}")
            cols[3].markdown(f"**End**: {row['End Time']}")
            st.progress(int(row.get('Progress %', 0)))
            st.caption(row.get('Notes', ''))
    st.markdown('</div>', unsafe_allow_html=True)

# -------------------- Activity Planner --------------------
if nav == "Activity Planner":
    st.markdown('<div class="pod-card">', unsafe_allow_html=True)
    st.subheader("Plan Activities")

    edited = st.data_editor(
        activities,
        num_rows="dynamic",
        column_config={
            "Priority": st.column_config.SelectboxColumn(options=PRIORITY_OPTIONS),
            "Status": st.column_config.SelectboxColumn(options=STATUS_OPTIONS),
            "Progress %": st.column_config.NumberColumn(min_value=0, max_value=100, step=1),
            "Hours": st.column_config.NumberColumn(min_value=0.0, max_value=24.0, step=0.25),
        },
        key="act_editor",
        use_container_width=True,
    )

    st.caption("Tip: Use the + below to add rows. Use dropdowns for Priority/Status.")
    c1, c2 = st.columns([1,1])
    with c1:
        if st.button("💾 Save Activities"):
            activities = edited
            persist(selected_date, activities, manpower, resources)
            st.success("Saved.")
    with c2:
        if st.button("🗑️ Clear All Activities"):
            activities = pd.DataFrame(columns=COLUMNS_ACT)
            persist(selected_date, activities, manpower, resources)
            st.warning("All activities cleared for the day.")
    st.markdown('</div>', unsafe_allow_html=True)

# -------------------- Manpower --------------------
if nav == "Manpower":
    st.markdown('<div class="pod-card">', unsafe_allow_html=True)
    st.subheader("Manpower Allocation")

    mp_edit = st.data_editor(
        manpower,
        num_rows="dynamic",
        column_config={
            "Role": st.column_config.SelectboxColumn(options=ROLE_OPTIONS),
        },
        key="mp_editor",
        use_container_width=True,
    )

    c1, c2 = st.columns([1,1])
    with c1:
        if st.button("💾 Save Manpower"):
            manpower = mp_edit
            persist(selected_date, activities, manpower, resources)
            st.success("Saved.")
    with c2:
        team_counts = mp_edit['Team'].fillna('Unknown').value_counts()
        team_pie = px.pie(values=team_counts.values, names=team_counts.index, title="Team Distribution", hole=0.5)
        st.plotly_chart(team_pie, use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

# -------------------- Resources --------------------
if nav == "Resources":
    st.markdown('<div class="pod-card">', unsafe_allow_html=True)
    st.subheader("Resource Tracker")

    res_edit = st.data_editor(
        resources,
        num_rows="dynamic",
        key="res_editor",
        use_container_width=True,
    )

    # Overbooking detection: same resource assigned to multiple activities
    overbook = res_edit.groupby('Resource')['Assigned To'].nunique()
    overbooked = overbook[overbook > 1]
    if not overbooked.empty:
        st.error("Overbooked resources detected: " + ", ".join(overbooked.index.tolist()))

    c1, c2 = st.columns([1,1])
    with c1:
        if st.button("💾 Save Resources"):
            resources = res_edit
            persist(selected_date, activities, manpower, resources)
            st.success("Saved.")
    with c2:
        type_counts = res_edit['Type'].fillna('Unknown').value_counts()
        res_pie = px.pie(values=type_counts.values, names=type_counts.index, title="Resources by Type", hole=0.5)
        st.plotly_chart(res_pie, use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

# -------------------- Timeline --------------------
if nav == "Timeline":
    st.markdown('<div class="pod-card">', unsafe_allow_html=True)
    st.subheader("Gantt Timeline")

    def _to_dt(tstr: str):
        try:
            hh, mm = map(int, str(tstr).split(":"))
            return datetime.combine(selected_date, time(hh, mm))
        except Exception:
            return None

    gantt_df = filtered_activities.copy()
    gantt_df['Start'] = gantt_df['Start Time'].apply(_to_dt)
    gantt_df['Finish'] = gantt_df['End Time'].apply(_to_dt)
    gantt_df = gantt_df.dropna(subset=['Start','Finish'])

    if not gantt_df.empty:
        fig = px.timeline(
            gantt_df,
            x_start="Start", x_end="Finish",
            y="Assigned Team", color="Status",
            hover_data=["Activity Name", "Location", "Priority"],
        )
        fig.update_yaxes(autorange="reversed")
        fig.update_layout(height=500, margin=dict(l=10,r=10,t=30,b=10))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Add activities with Start/End times to view the timeline.")

    st.markdown('</div>', unsafe_allow_html=True)

# -------------------- Reports / Export --------------------
if nav == "Reports" or export_clicked:
    st.markdown('<div class="pod-card">', unsafe_allow_html=True)
    st.subheader("Daily Summary & Export")

    total_acts = len(activities)
    total_mp = len(manpower)
    hours_planned = round(activities['Hours'].fillna(0).sum(), 2)
    hours_completed = round(activities.query("Status=='Completed'")['Hours'].fillna(0).sum(), 2)
    pct_prog = 0 if total_acts==0 else int(100*len(activities.query("Status=='Completed'"))/total_acts)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Activities", total_acts)
    c2.metric("Manpower Deployed", total_mp)
    c3.metric("Hours Planned", hours_planned)
    c4.metric("% Progress", f"{pct_prog}%")

    # Bar + Pie images for PDF
    status_counts = activities['Status'].value_counts().reindex(STATUS_OPTIONS, fill_value=0)
    bar = px.bar(status_counts, title="Activities by Status", labels={"value":"Count", "index":"Status"})
    role_counts = manpower['Role'].value_counts()
    pie = px.pie(values=role_counts.values, names=role_counts.index, title="Manpower by Role", hole=0.45)

    # Save figures to PNG in-memory
    bar_bytes = bar.to_image(format="png") if hasattr(bar, 'to_image') else None
    pie_bytes = pie.to_image(format="png") if hasattr(pie, 'to_image') else None

    # Excel export (multi-sheet)
    excel_io = BytesIO()
    with pd.ExcelWriter(excel_io, engine='xlsxwriter') as writer:
        activities.to_excel(writer, index=False, sheet_name='Activities')
        manpower.to_excel(writer, index=False, sheet_name='Manpower')
        resources.to_excel(writer, index=False, sheet_name='Resources')
    excel_io.seek(0)

    st.download_button(
        "⬇️ Download Excel (Activities/Manpower/Resources)",
        data=excel_io,
        file_name=f"POD_{_date_key(selected_date)}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

    # PDF export
    def build_pdf() -> bytes:
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        W, H = A4

        def HLine(y):
            c.setStrokeColorRGB(0.9,0.9,0.9)
            c.setLineWidth(0.6)
            c.line(32, y, W-32, y)

        # Cover / Header
        c.setFillColorRGB(0.99, 0.62, 0.0)
        c.rect(0, H-120, W, 120, fill=1, stroke=0)
        c.setFillColorRGB(1,1,1)
        c.setFont("Helvetica-Bold", 20)
        c.drawString(32, H-50, "POD – Plan of Day (Solar)")
        c.setFont("Helvetica", 12)
        c.drawString(32, H-72, f"Date: {_date_key(selected_date)}")

        # KPIs
        c.setFillColorRGB(0,0,0)
        c.setFont("Helvetica-Bold", 13)
        c.drawString(32, H-150, "Daily Summary")
        c.setFont("Helvetica", 11)
        c.drawString(32, H-170, f"Total Activities: {total_acts}")
        c.drawString(200, H-170, f"Manpower Deployed: {total_mp}")
        c.drawString(32, H-190, f"Hours Planned: {hours_planned}")
        c.drawString(200, H-190, f"% Progress: {pct_prog}%")
        HLine(H-205)

        # Charts
        y = H-430
        if bar_bytes:
            c.drawImage(ImageReader(BytesIO(bar_bytes)), 32, y, width=W/2-40, height=200, preserveAspectRatio=True, mask='auto')
        if pie_bytes:
            c.drawImage(ImageReader(BytesIO(pie_bytes)), W/2+8, y, width=W/2-40, height=200, preserveAspectRatio=True, mask='auto')

        # Activities table (first 20 rows)
        y2 = y-30
        c.setFont("Helvetica-Bold", 12)
        c.drawString(32, y2, "Activities (top 20)")
        y2 -= 16
        c.setFont("Helvetica", 9)
        cols = ["Activity Name","Location","Assigned Team","Start Time","End Time","Status","Priority"]
        head = " | ".join(cols)
        c.drawString(32, y2, head[:110])
        y2 -= 12
        HLine(y2+6)
        for _, r in activities.head(20).iterrows():
            line = " | ".join(str(r[k]) for k in cols)
            c.drawString(32, y2, line[:110])
            y2 -= 12
            if y2 < 64:
                c.showPage(); y2 = H-64
        c.showPage()
        c.save()
        pdf = buffer.getvalue()
        buffer.close()
        return pdf

    pdf_bytes = build_pdf()
    st.download_button(
        "⬇️ Download PDF Summary",
        data=pdf_bytes,
        file_name=f"POD_{_date_key(selected_date)}.pdf",
        mime="application/pdf",
        use_container_width=True,
    )

    st.info("Optional: WhatsApp/Email integrations can be wired using Twilio SendGrid / WhatsApp API. Add credentials and call on export.")
    st.markdown('</div>', unsafe_allow_html=True)

# -------------------- Settings --------------------
if nav == "Settings":
    st.markdown('<div class="pod-card">', unsafe_allow_html=True)
    st.subheader("Settings & Integrations")

    st.markdown("**Data Storage**")
    st.caption("By default, your plans are saved as CSV in ./data per date. Enable Google Sheets to sync remotely.")

    use_gs = st.toggle("Enable Google Sheets (requires credentials)")
    if use_gs:
        st.text_input("Google Sheet URL (or key)")
        st.file_uploader("Service account JSON", type=["json"])
        st.caption("Add your credentials and wire up the gspread client in the placeholder below.")

    st.markdown("**Notifications**")
    st.toggle("Enable Email (SendGrid)")
    st.toggle("Enable WhatsApp (Twilio)")
    st.caption("Enter API keys in your Streamlit secrets and call the providers after Export.")

    st.markdown("**Appearance**")
    st.toggle("High-contrast status colors", value=True)

    st.code(
        """
# Placeholder for Google Sheets wiring (add inside persist with guards)
# import gspread
# from oauth2client.service_account import ServiceAccountCredentials
# def push_to_gs(sheet_url, df, tab):
#     scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
#     creds = ServiceAccountCredentials.from_json_keyfile_name('service.json', scope)
#     client = gspread.authorize(creds)
#     sh = client.open_by_url(sheet_url)
#     ws = sh.worksheet(tab)
#     ws.clear()
#     ws.update([df.columns.values.tolist()] + df.values.tolist())
        """
    )

    st.markdown('</div>', unsafe_allow_html=True)

# Persist if user navigated and made changes via editors (already handled on save buttons)
