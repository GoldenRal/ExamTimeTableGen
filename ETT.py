import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io
import os

st.set_page_config(page_title="📘 Exam Timetable Generator", layout="wide")

# --- Custom Glossy Light Green Theme ---
st.markdown("""
    <style>
        /* Add top padding to prevent clipping */
        .main > div:first-child {
            padding-top: 30px;
        }
        /* Logo alignment fix */
        .block-container {
            padding-top: 5rem !important;
        }
        body {
            background-color: #e6ffe6;
            background-image: linear-gradient(145deg, #d9fdd3 0%, #ccffcc 100%);
        }
        .block-container {
            background: linear-gradient(135deg, #eaffea, #d9fdd3);
            border-radius: 12px;
            padding: 20px;
        }
        /* Bold Labels */
        .stSelectbox label, .stDateInput label, .stNumberInput label,
        .stTextInput label, .stRadio label, .stMarkdown, .stFileUploader label {
            font-weight: bold !important;
        }
        /* Black Border + Shadow for Inputs */
        .stSelectbox, .stTextInput, .stNumberInput, .stDateInput, .stRadio, .stFileUploader {
            /*border: 1px solid black !important;*/
            /*border-radius: 8px !important;*/
            box-shadow: 2px 2px 5px rgba(0,0,0,0.2) !important;
            padding: 2px !important;
        }
        /* Input fields and dropdown inside */
        .stSelectbox div[data-baseweb="select"], .stTextInput input, .stNumberInput input, .stDateInput input {
            border: 1px solid black !important;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.2) !important;
            border-radius: 6px !important;
        }
        /* Buttons Styling */
        .stButton > button, .stDownloadButton > button {
            border: 1px solid black !important;
            border-radius: 8px !important;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.3) !important;
            font-weight: bold !important;
        }
        /* File uploader box shadow */
        section[data-testid="stFileUploader"] > div {
            border: 1px solid black !important;
            border-radius: 8px !important;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.2) !important;
        }
        /* Sidebar sections */
        .stSidebarContent {
            border: 1px solid black !important;
            border-radius: 10px !important;
            box-shadow: 3px 3px 6px rgba(0,0,0,0.25) !important;
            padding: 10px;
        }
        /* Fix image overflow in logo column */
        .element-container:has(img) {
            display: flex;
            align-items: center;
            justify-content: center;
        }
    </style>
""", unsafe_allow_html=True)


# --- Sidebar Config ---
st.sidebar.markdown("## ⚙️ Configuration")
logo_file = st.sidebar.file_uploader("🖼️ Upload Logo", type=["png", "jpg", "jpeg"])
excel_file = st.sidebar.file_uploader("📂 Upload Excel File", type=["xlsx"])
institute_name = st.sidebar.text_input("🏫 Institution Name", value="Step to Success Higher Secondary School")

if not excel_file:
    st.sidebar.warning("⚠️ Please upload the Excel file to continue.")
    st.stop()

# --- Load Subjects from Excel ---
@st.cache_data
def load_subjects(file_data):
    df = pd.read_excel(file_data, sheet_name="Subjects")
    subject_dict = {}
    for _, row in df.iterrows():
        standard = str(row["Standard"]).strip()
        subjects = [s.strip() for s in str(row["Subjects"]).split(",") if s.strip()]
        subject_dict[standard] = subjects
    return subject_dict

subject_data = load_subjects(excel_file)

# --- Header Section ---
col_logo, col_title = st.columns([1, 4])
with col_logo:
    if logo_file:
        st.image(logo_file, width=100)
    else:
        st.warning("🖼️ No logo uploaded.")
with col_title:
    st.markdown(f"<h1 style='margin-bottom: 0;'>{institute_name}</h1>", unsafe_allow_html=True)
    st.markdown("<h3>📘 Examination Timetable Generator</h3>", unsafe_allow_html=True)

st.markdown("---")

# --- Exam Configuration ---
st.subheader("🗓️ Configure Examination Details")
selected_class = st.selectbox("🎓 Select Class", sorted(subject_data.keys()))
exam_type = st.selectbox("📝 Exam Type", [
    "Unit Test", "Terminal Exam", "Final Exam", "Practice Test", "Internal Oral", "Board Mock"
])
num_timetables = st.number_input("🔢 Number of Different Timetables to Generate", min_value=1, max_value=3, value=1)

start_date = st.date_input("📅 Start Date", value=datetime.today())
end_date = st.date_input("📅 End Date (optional)", value=start_date + timedelta(days=20))

# --- Subject Configuration ---
subjects = subject_data.get(selected_class, [])
subjects = list(dict.fromkeys(subjects))

subject_gaps = {}
subject_durations = {}
subject_sessions = {}
subject_start_times = {}

if subjects:
    st.markdown("### 📚 Subject-wise Session, Time, Duration and Gap Configuration")
    for subject in subjects:
        st.markdown(f"#### 📖 {subject}")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            session = st.radio("🕰️ Session", ["Morning", "Afternoon"], key=f"session_{subject}")
        with col2:
            start_time = st.text_input("⏱️ Start Time (HH:MM)", value="09:00", key=f"time_{subject}")
        with col3:
            duration = st.selectbox("⌛ Duration", ["1 hour", "2 hours", "3 hours"], key=f"dur_{subject}")
        with col4:
            gap = st.selectbox("📴 Gap days before", [0, 1, 2, 3], key=f"gap_{subject}")
        subject_sessions[subject] = session
        subject_start_times[subject] = start_time
        subject_durations[subject] = duration
        subject_gaps[subject] = gap

# --- Mapping ---
SUBJECT_MAPPING = {
    "Marathi": ("01", "मराठी"), "Hindi": ("02", "हिंदी"), "English": ("03", "इंग्रजी"),
    "Math": ("04", "गणित"), "Math I": ("05", "गणित - I"), "Math II": ("06", "गणित - II"),
    "Science": ("07", "विज्ञान"), "Science I": ("08", "विज्ञान - I"), "Science II": ("09", "विज्ञान - II"),
    "History": ("10", "इतिहास"), "Geography": ("11", "भूगोल"), "Civics": ("12", "नागरिकशास्त्र"),
    "EVS": ("13", "पर्यावरण"), "Drawing": ("14", "चित्रकला"), "Sanskrit": ("15", "संस्कृत"),
    "Vocational": ("16", "व्यावसायिक"), "Urdu": ("17", "उर्दू"), "German": ("34", "जर्मन"),
    "French": ("35", "फ्रेंच")
}
HOLIDAYS = [datetime.strptime(d, "%Y-%m-%d").date() for d in ["2025-08-15", "2025-10-02", "2025-01-26", "2025-03-29"]]

if 'timetables' not in st.session_state:
    st.session_state['timetables'] = {}

if st.button("🎯Generate Timetable"):
    st.session_state['📋Timetables'] = {}  # Reset old data
    import random
    for table_num in range(1, num_timetables + 1):
        timetable = []
        current_date = start_date
        subjects_shuffled = subjects.copy()
        random.shuffle(subjects_shuffled)

        for subject in subjects_shuffled:
            if current_date > end_date:
                st.warning(f"📌End date reached before finishing all subjects in Timetable {table_num}.")
                break

            # Apply gap before the subject
            gap_days = subject_gaps[subject]
            days_inserted = 0
            while days_inserted < gap_days:
                if current_date.weekday() != 6 and current_date not in HOLIDAYS:
                    timetable.append({
                        "Date": current_date.strftime("%A, %d-%m-%Y"),
                        "Subject": "Gap Day",
                        "Session": "-",
                        "Duration": "-",
                        "Start Time": "-",
                        "End Time": "-"
                    })
                    days_inserted += 1
                else:
                    timetable.append({
                        "Date": current_date.strftime("%A, %d-%m-%Y"),
                        "Subject": "Holiday/Sunday",
                        "Session": "-",
                        "Duration": "-",
                        "Start Time": "-",
                        "End Time": "-"
                    })
                current_date += timedelta(days=1)

            # Skip holidays and Sundays
            while current_date.weekday() == 6 or current_date in HOLIDAYS:
                timetable.append({
                    "Date": current_date.strftime("%A, %d-%m-%Y"),
                    "Subject": "Holiday/Sunday",
                    "Session": "-",
                    "Duration": "-",
                    "Start Time": "-",
                    "End Time": "-"
                })
                current_date += timedelta(days=1)

            # Schedule subject
            start_time_str = subject_start_times[subject]
            try:
                start_time_obj = datetime.strptime(start_time_str, "%H:%M").time()
            except:
                st.error(f"❌Invalid time format for {subject}. Use HH:MM.")
                st.stop()

            duration_hours = int(subject_durations[subject].split()[0])
            end_time = (datetime.combine(datetime.today(), start_time_obj) + timedelta(hours=duration_hours)).time()
            index, marathi_name = SUBJECT_MAPPING.get(subject, ("", subject))

            timetable.append({
                "Date": current_date.strftime("%A, %d-%m-%Y"),
                "Subject": subject,
                "Subject Index": index,
                "Subject (MR)": marathi_name,
                "Session": subject_sessions[subject],
                "Duration": subject_durations[subject],
                "Start Time": start_time_obj.strftime("%H:%M"),
                "End Time": end_time.strftime("%H:%M")
            })

            current_date += timedelta(days=1)

        df_timetable = pd.DataFrame(timetable)
        st.session_state['timetables'][f"Timetable {table_num}"] = df_timetable
        
if st.session_state.get('timetables'):
    for name, df_timetable in st.session_state['timetables'].items():
        st.markdown(f"## {name}")

        def highlight_rows(row):
            if row["Subject"] in ["Holiday/Sunday", "Gap Day"]:
                return ['font-weight: bold; background-color: #ffe6ea'] * len(row)
            elif row.name % 2 == 0:
                return ['background-color: #f9f9f9'] * len(row)
            else:
                return [''] * len(row)

        st.success(f"{name} Generated:")
        st.dataframe(df_timetable.style.apply(highlight_rows, axis=1), use_container_width=True)

        def convert_df(df):
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name=name)
            output.seek(0)
            return output

        st.download_button(
            label=f"📥 Download {name} as Excel",
            data=convert_df(df_timetable),
            file_name=f"{selected_class}_{name.lower().replace(' ', '_')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    

