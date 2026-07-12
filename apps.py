import streamlit as st
import numpy as np
import pandas as pd
import joblib
import sqlite3
import matplotlib.pyplot as plt
from datetime import datetime
from fpdf import FPDF
import random
import os
import bcrypt
import qrcode
import base64
# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="🏥 Hospital AI System",
    page_icon="🏥",
    layout="wide"
)
st.markdown("""
<style>

div[data-testid="stHorizontalBlock"]{
    margin-top:70px;
}
div[data-testid="stVerticalBlock"]:has(div[data-testid="stRadio"]){
    background:rgba(255,255,255,0.88);
    padding:35px;
    border-radius:20px;
    box-shadow:0 0 25px rgba(0,0,0,.35);
}


</style>
""", unsafe_allow_html=True)
def get_base64(file):
    with open(file, "rb") as f:
        return base64.b64encode(f.read()).decode()

img = get_base64("hospital_bg.jpg")

if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:

    st.markdown(f"""
    <style>

    [data-testid="stAppViewContainer"] {{
        background: url("data:image/jpg;base64,{img}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}

    [data-testid="stHeader"] {{
        background: rgba(0,0,0,0);
    }}

    [data-testid="stSidebar"] {{
        display:none;
    }}

    </style>
    """, unsafe_allow_html=True)
# DATABASE
conn = sqlite3.connect("patients.db", check_same_thread=False)
c = conn.cursor()
# =========================
# USERS TABLE
# =========================
c.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password BLOB,
    role TEXT
)
""")
conn.commit()
# =========================
# LOGIN SYSTEM
# =========================
if "username" not in st.session_state:
    st.session_state.username = ""

if "role" not in st.session_state:
    st.session_state.role = ""

if not st.session_state.login:

    left, center, right = st.columns([1,2,1])

    with center:

        st.markdown("<h1 style='text-align:center;'>🏥 Hospital AI</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align:center;'>Breast Cancer Detection System</h3>", unsafe_allow_html=True)

        option = st.radio(
            "Select Option",
            ["Login","Register"],
            horizontal=True
        )

        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if option == "Register":

            role = st.selectbox(
            "Role",
            ["Doctor", "Receptionist"]
            )

            if st.button("Create Account", use_container_width=True):

                try:

                    hashed = bcrypt.hashpw(
                        password.encode(),
                        bcrypt.gensalt()
                    )

                    c.execute(
                        "INSERT INTO users(username,password,role) VALUES(?,?,?)",
                        (username, hashed, role)
                    )

                    conn.commit()

                    st.success("✅ Account Created Successfully")

                except sqlite3.IntegrityError:

                    st.error("❌ Username already exists")

        else:

            if st.button("Login", use_container_width=True):

                c.execute(
                    "SELECT password,role FROM users WHERE username=?",
                    (username,)
                )

                user = c.fetchone()

                if user:

                    stored = user[0]

                    if isinstance(stored, str):
                        stored = stored.encode()

                    if bcrypt.checkpw(password.encode(), stored):

                        st.session_state.login = True
                        st.session_state.username = username
                        st.session_state.role = user[1] if user[1] else "Admin"

                        st.rerun()

                    else:
                        st.error("❌ Wrong Password")

                else:
                    st.error("❌ User Not Found")

    st.stop()

# =========================
# AFTER LOGIN
# =========================

st.sidebar.success(f"👋 Welcome {st.session_state.username}")
st.sidebar.write(f"Role : {st.session_state.role}")
st.sidebar.markdown("---")
# =========================
# LOAD MODEL
# =========================
model = joblib.load("breast_cancer_model.pkl")
scaler = joblib.load("scaler.pkl")
feature_names = joblib.load("feature_names.pkl")


c.execute("""
CREATE TABLE IF NOT EXISTS patients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id TEXT,
    patient_name TEXT,
    age INTEGER,
    gender TEXT,
    doctor_name TEXT,
    mobile TEXT,
    email TEXT,
    address TEXT,
    photo TEXT,
    date TEXT,
    prediction INTEGER,
    probability REAL,
    risk TEXT,
    doctor_notes TEXT
)
""")
conn.commit()
try:
    c.execute("ALTER TABLE patients ADD COLUMN doctor_notes TEXT")
    conn.commit()
except sqlite3.OperationalError:
    pass
# =========================
# MEDICAL RECORDS TABLE
# =========================
c.execute("""
CREATE TABLE IF NOT EXISTS medical_records(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_id TEXT,
    patient_id TEXT,
    visit_date TEXT,
    doctor_name TEXT,
    symptoms TEXT,
    diagnosis TEXT,
    doctor_notes TEXT,
    prescription TEXT,
    lab_tests TEXT,
    treatment_plan TEXT,
    follow_up_date TEXT,
    created_by TEXT
)
""")
conn.commit()
# =========================
# APPOINTMENTS TABLE
# =========================
c.execute("""
CREATE TABLE IF NOT EXISTS appointments(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    appointment_id TEXT UNIQUE,
    patient_id TEXT,
    patient_name TEXT,
    doctor_name TEXT,
    appointment_date TEXT,
    appointment_time TEXT,
    status TEXT
)
""")

# =========================
# BILLING TABLE
# =========================
c.execute("""
CREATE TABLE IF NOT EXISTS billing(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bill_id TEXT UNIQUE,
    patient_id TEXT,
    patient_name TEXT,
    doctor_name TEXT,
    consultation_fee REAL,
    lab_fee REAL,
    medicine_fee REAL,
    other_fee REAL,
    gst REAL,
    discount REAL,
    total REAL,
    bill_date TEXT
)
""")


# =========================
# AUDIT LOG TABLE
# =========================
c.execute("""
CREATE TABLE IF NOT EXISTS audit_logs(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    action TEXT,
    action_time TEXT
)
""")

conn.commit()
# =========================
# AUTO PATIENT ID
# =========================

def generate_patient_id():

    c.execute("SELECT patient_id FROM patients ORDER BY id DESC LIMIT 1")
    last = c.fetchone()

    if last is None or last[0] is None:
        return "P10001"

    try:
        number = int(last[0][1:])
        return f"P{number + 1}"
    except:
        return "P10001"
# =========================
# MENU
# =========================

if st.session_state.role == "Admin":

    menu = st.sidebar.radio(
        "Navigation",
        [
            "🏠 Home",
            "🤖 Prediction",
            "📅 Appointments",
            "👨‍⚕️ Doctor Panel",
            "📊 Dashboard",
            "📋 Patient History",
            "👨‍💼 Admin Panel",
            "👨‍⚕️ Doctor Dashboard"
        ]
    )

elif st.session_state.role == "Doctor":

    menu = st.sidebar.radio(
        "Navigation",
        [
            "🏠 Home",
            "🤖 Prediction",
            "📅 Appointments",
            "👨‍⚕️ Doctor Panel",
            "📊 Dashboard",
            "📋 Patient History",
            "👨‍⚕️ Doctor Dashboard"
        ]
    )

else:

    menu = st.sidebar.radio(
        "Navigation",
        [
            "🏠 Home",
            "🤖 Prediction",
            "📅 Appointments",
            "📋 Patient History"
        ]
    )

st.sidebar.markdown("---")

if st.sidebar.button("🚪 Logout"):
    st.session_state.login = False
    st.session_state.username = ""
    st.session_state.role = ""
    st.rerun()


# =========================
# FEATURE INPUT
# =========================
# =========================
# FEATURE INPUT
# =========================

feature_ranges = {
    "radius_mean": (6.0, 30.0),
    "texture_mean": (9.0, 40.0),
    "perimeter_mean": (40.0, 200.0),
    "area_mean": (100.0, 2500.0),
    "smoothness_mean": (0.05, 0.20),
    "compactness_mean": (0.01, 0.40),
    "concavity_mean": (0.00, 0.50),
    "concave points_mean": (0.00, 0.25),
    "symmetry_mean": (0.10, 0.40),
    "fractal_dimension_mean": (0.04, 0.10),

    "radius_se": (0.1, 3.0),
    "texture_se": (0.3, 5.0),
    "perimeter_se": (0.5, 25.0),
    "area_se": (5.0, 550.0),
    "smoothness_se": (0.001, 0.05),
    "compactness_se": (0.002, 0.15),
    "concavity_se": (0.00, 0.40),
    "concave points_se": (0.00, 0.06),
    "symmetry_se": (0.01, 0.08),
    "fractal_dimension_se": (0.001, 0.03),

    "radius_worst": (7.0, 40.0),
    "texture_worst": (12.0, 50.0),
    "perimeter_worst": (50.0, 260.0),
    "area_worst": (150.0, 4300.0),
    "smoothness_worst": (0.07, 0.25),
    "compactness_worst": (0.02, 1.10),
    "concavity_worst": (0.00, 1.30),
    "concave points_worst": (0.00, 0.35),
    "symmetry_worst": (0.15, 0.70),
    "fractal_dimension_worst": (0.05, 0.25)
}

    
    # =========================
# COMMON DASHBOARD DATA
# =========================

c.execute("SELECT COUNT(*) FROM patients")
total = c.fetchone()[0]

c.execute("SELECT COUNT(*) FROM patients WHERE prediction=1")
malignant = c.fetchone()[0]

c.execute("SELECT COUNT(*) FROM patients WHERE prediction=0")
benign = c.fetchone()[0]

today = datetime.now().strftime("%Y-%m-%d")

c.execute(
    "SELECT COUNT(*) FROM patients WHERE date LIKE ?",
    (today + "%",)
)
today_patients = c.fetchone()[0]
# =========================
# HOME
# =========================
# =========================
# HOME
# =========================

if menu == "🏠 Home":

    st.success(f"Welcome, {st.session_state.username}")

    st.markdown("---")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("👨 Total Patients", total)
    col2.metric("🔴 Cancer", malignant)
    col3.metric("🟢 Benign", benign)
    col4.metric("📅 Today", today_patients)

    st.markdown("---")

    st.subheader("📌 System Features")

    st.write("✅ AI Breast Cancer Prediction")
    st.write("✅ Patient History")
    st.write("✅ Appointment Booking")
    st.write("✅ Doctor Dashboard")
    st.write("✅ Hospital Dashboard")
    st.write("✅ PDF Report Generation")
    st.write("✅ QR Code Generation")
    st.write("✅ Billing System")
    st.sidebar.subheader("🔑 Change Password")

    old_password = st.sidebar.text_input(
      "Current Password",
      type="password",
      key="old_pass"
    )

    new_password = st.sidebar.text_input(
        "New Password",
        type="password",
        key="new_pass"
    )

    if st.sidebar.button("Update Password"):

        c.execute(
            "SELECT password FROM users WHERE username=?",
            (st.session_state.username,)
        )

        user = c.fetchone()

        if user and bcrypt.checkpw(
            old_password.encode("utf-8"),
            user[0]
        ):

            new_hash = bcrypt.hashpw(
                new_password.encode("utf-8"),
                bcrypt.gensalt()
            )

            c.execute(
                "UPDATE users SET password=? WHERE username=?",
                (new_hash, st.session_state.username)
            )

            conn.commit()
            st.sidebar.success("✅ Password Updated Successfully")

        else:
            st.sidebar.error("❌ Current Password Incorrect")


# =========================
# DASHBOARD
# =========================
if menu == "📊 Dashboard":

    st.header("📊 Hospital Dashboard")

    # ---------- Dashboard Cards ----------
    col1, col2, col3, col4 = st.columns(4)

    c.execute("SELECT COUNT(*) FROM patients")
    total = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM patients WHERE prediction=1")
    malignant = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM patients WHERE prediction=0")
    benign = c.fetchone()[0]

    today = datetime.now().strftime("%Y-%m-%d")

    c.execute(
        "SELECT COUNT(*) FROM patients WHERE date LIKE ?",
        (today + "%",)
    )
    today_patients = c.fetchone()[0]

    col1.metric("👨 Patients", total)
    col2.metric("🔴 Cancer", malignant)
    col3.metric("🟢 Benign", benign)
    col4.metric("📅 Today", today_patients)

    # ---------- Daily Trend ----------
    st.markdown("---")
    st.subheader("📈 Daily Patient Trend")

    c.execute("""
        SELECT substr(date,1,10), COUNT(*)
        FROM patients
        GROUP BY substr(date,1,10)
        ORDER BY substr(date,1,10)
    """)

    rows = c.fetchall()

    if rows:

        dates = [row[0] for row in rows]
        counts = [row[1] for row in rows]

        fig, ax = plt.subplots()

        ax.plot(dates, counts, marker="o")

        ax.set_title("Daily Patient Trend")
        ax.set_xlabel("Date")
        ax.set_ylabel("Patients")

        plt.xticks(rotation=45)

        st.pyplot(fig)

    else:
        st.info("No patient data available.")

    # ---------- Risk Summary ----------
    st.markdown("---")
    st.subheader("📊 Risk Summary")

    c.execute("""
        SELECT risk, COUNT(*)
        FROM patients
        GROUP BY risk
    """)

    rows = c.fetchall()

    low = medium = high = 0

    for r in rows:

        if r[0] == "Low":
            low = r[1]

        elif r[0] == "Medium":
            medium = r[1]

        elif r[0] == "High":
            high = r[1]

    col1, col2, col3 = st.columns(3)

    col1.metric("🟢 Low Risk", low)
    col2.metric("🟡 Medium Risk", medium)
    col3.metric("🔴 High Risk", high)

    st.subheader("📈 Risk Distribution")

    fig, ax = plt.subplots()

    ax.pie(
        [low, medium, high],
        labels=["Low", "Medium", "High"],
        autopct="%1.1f%%"
    )

    st.pyplot(fig)

    # ---------- Recent Patients ----------
    st.markdown("---")

    st.subheader("🕒 Recent Patients")

    c.execute("""
        SELECT
        patient_id,
        patient_name,
        prediction,
        risk,
        date
        FROM patients
        ORDER BY id DESC
        LIMIT 5
    """)

    recent = c.fetchall()

    recent_df = pd.DataFrame(
        recent,
        columns=[
            "Patient ID",
            "Name",
            "Prediction",
            "Risk",
            "Date"
        ]
    )

    st.dataframe(recent_df, use_container_width=True)

    # ---------- High Risk Patients ----------
    st.markdown("---")

    st.subheader("🔴 High Risk Patients")

    c.execute("""
        SELECT
        patient_name,
        age,
        doctor_name,
        probability
        FROM patients
        WHERE risk='High'
        ORDER BY probability DESC
    """)

    high = c.fetchall()

    high_df = pd.DataFrame(
        high,
        columns=[
            "Name",
            "Age",
            "Doctor",
            "Probability"
        ]
    )
    st.dataframe(high_df, use_container_width=True)

 # =========================
 # HISTORY
 # =========================
if menu == "📋 Patient History":
      import pandas as pd

      st.header("📋 Patient History")

      col1, col2 = st.columns(2)

      with col1:
                search = st.text_input("🔍 Search Patient ID")

      with col2:
                selected_date = st.date_input("📅 Select Date")

    # ================= QUERY =================
      if search:
            data = c.execute(
                "SELECT * FROM patients WHERE patient_id=?",
                (search,)
            ).fetchall()

      elif selected_date:
            data = c.execute("""
                SELECT * FROM patients
                WHERE date(date)=?
            """, (selected_date.strftime("%Y-%m-%d"),)).fetchall()

      else:
            data = c.execute("SELECT * FROM patients").fetchall()
            print("Total values =", len(data[0]))
            print(data[0])
            exit()
     # ================= DISPLAY =================
      if len(data) == 0:
            st.warning("No records found.")

      else:
            df = pd.DataFrame(
                data,
                columns=[
                    "DB_ID","Patient_ID","Name","Age","Gender",
                    "Doctor","Mobile","Email","Address","Photo",
                    "Date","Prediction","Probability","Risk",
                    "Doctor_Notes"
                ]
            )

            st.dataframe(df, use_container_width=True)

            csv = df.to_csv(index=False).encode("utf-8")

            st.download_button(
                "📥 Download Patient History (CSV)",
                csv,
                "patient_history.csv",
                "text/csv"
            )

            st.markdown("---")

            delete_id = st.text_input("🗑 Enter Patient ID to Delete")

            if st.button("Delete Record"):

                c.execute(
                    "DELETE FROM patients WHERE patient_id=?",
                    (delete_id,)
                )

                conn.commit()
                st.success("✅ Patient record deleted successfully.")
# =========================
# APPOINTMENTS
# =========================
if menu == "📅 Appointments":

    st.success(f"Logged in as : {st.session_state.role}")

    st.header("📅 Appointment Booking")

    appointment_id = "A" + str(random.randint(10000,99999))

    patient_name_app = st.text_input("Patient Name")
    patient_id_app = st.text_input("Patient ID")

    # Doctor Selection
    if st.session_state.role == "Doctor":

        doctor = st.session_state.username
        st.info(f"Doctor : {doctor}")

    else:

        doctor = st.selectbox(
            "Doctor",
            ["Dr. Sharma", "Dr. Gupta", "Dr. Khan", "Dr. Singh"]
        )

    app_date = st.date_input("Appointment Date")

    app_time = st.selectbox(
        "Time",
        [
            "09:00 AM",
            "10:00 AM",
            "11:00 AM",
            "12:00 PM",
            "02:00 PM",
            "03:00 PM",
            "04:00 PM"
        ]
    )

    if st.button("Book Appointment"):

        c.execute("""
        INSERT INTO appointments(
            appointment_id,
            patient_id,
            patient_name,
            doctor_name,
            appointment_date,
            appointment_time,
            status
        )
        VALUES (?,?,?,?,?,?,?)
        """, (
            appointment_id,
            patient_id_app,
            patient_name_app,
            doctor,
            str(app_date),
            app_time,
            "Booked"
        ))

        conn.commit()

        st.success("✅ Appointment Booked")
        st.write("Appointment ID:", appointment_id)

    st.markdown("---")
    st.subheader("📋 Appointment List")

    # Role-wise appointment list
    if st.session_state.role == "Admin":

        c.execute("""
        SELECT appointment_id, patient_name, doctor_name,
               appointment_date, appointment_time, status
        FROM appointments
        ORDER BY id DESC
        """)

    elif st.session_state.role == "Doctor":

        c.execute("""
        SELECT appointment_id, patient_name, doctor_name,
               appointment_date, appointment_time, status
        FROM appointments
        WHERE doctor_name=?
        ORDER BY id DESC
        """, (st.session_state.username,))

    else:

        c.execute("""
        SELECT appointment_id, patient_name, doctor_name,
               appointment_date, appointment_time, status
        FROM appointments
        ORDER BY id DESC
        """)

    df = pd.DataFrame(
        c.fetchall(),
        columns=[
            "Appointment ID",
            "Patient",
            "Doctor",
            "Date",
            "Time",
            "Status"
        ]
    )

    st.dataframe(df, use_container_width=True)   
#==========================
# PREDICTION
# =========================
if menu == "🤖 Prediction":
    # =========================
    # PATIENT DETAILS
    # =========================

    st.sidebar.subheader("👩 Patient Details")

    patient_name = st.sidebar.text_input("Patient Name")

    patient_age = st.sidebar.number_input(
        "Patient Age",
        18,
        100,
        30
    )

    gender = st.sidebar.selectbox(
        "Gender",
        ["Female", "Male"]
    )

    if st.session_state.role == "Doctor":

        doctor_name = st.session_state.username
        st.sidebar.info(f"Doctor : {doctor_name}")

    else:

        doctor_name = st.sidebar.selectbox(
            "Doctor",
            ["Dr. Sharma", "Dr. Gupta", "Dr. Khan", "Dr. Singh"]
        )
    mobile = st.sidebar.text_input("Mobile")

    email = st.sidebar.text_input("Email")

    address = st.sidebar.text_area("Address")
    doctor_notes = st.sidebar.text_area(
    "Doctor Notes",
    placeholder="Enter doctor's notes..."
    )

    photo = st.sidebar.file_uploader(
        "Patient Photo",
        type=["jpg", "jpeg", "png"]
    )
    input_data = []

    for f in feature_names:

        if f in feature_ranges:
            min_v, max_v = feature_ranges[f]
        else:
            min_v, max_v = (0.0, 1.0)

        val = st.sidebar.slider(
            f,
            min_value=float(min_v),
            max_value=float(max_v),
            value=float((min_v + max_v) / 2)
        )

        input_data.append(val)
    st.subheader("🩺 Stage 1 - Risk Assessment")

    age = st.number_input(
    "Age",
    18,
    100,
    35,
    key="risk_age"
    )

    family_history = st.selectbox(
    "Family History of Breast Cancer",
    ["No", "Yes"],
    key="risk_family"
    )
    lump = st.selectbox(
    "Breast Lump",
    ["No", "Yes"],
    key="risk_lump"
    )

    pain = st.selectbox(
        "Breast Pain",
        ["No", "Yes"],
        key="risk_pain"
    )

    nipple = st.selectbox(
        "Nipple Discharge",
        ["No", "Yes"],
        key="risk_nipple"
    )

    skin = st.selectbox(
        "Skin Dimpling / Changes",
        ["No", "Yes"],
        key="risk_skin"
    )

    smoking = st.selectbox(
        "Smoking",
        ["No", "Yes"],
        key="risk_smoking"
    )

    alcohol = st.selectbox(
        "Alcohol Consumption",
        ["No", "Yes"],
        key="risk_alcohol"
    )
    

    risk_score = 0

    if age > 45:
        risk_score += 2
    if family_history == "Yes":
        risk_score += 3
    if lump == "Yes":
        risk_score += 5
    if pain == "Yes":
        risk_score += 2
    if nipple == "Yes":
        risk_score += 3
    if skin == "Yes":
        risk_score += 4
    photo_path = ""

    if photo is not None:
       os.makedirs("patient_photos", exist_ok=True)

       photo_path = os.path.join(
        "patient_photos",
        photo.name
       )
       with open(photo_path, "wb") as f:
         f.write(photo.getbuffer())
 
if st.button("🔍 Predict Now"):

    # =========================
    # INPUT VALIDATION
    # =========================

    if patient_name.strip() == "":
       st.error("❌ Please enter Patient Name.")
       st.stop()

    if mobile.strip() == "":
       st.error("❌ Please enter Mobile Number.")
       st.stop()

    if len(mobile) != 10 or not mobile.isdigit():
       st.error("❌ Mobile Number must be exactly 10 digits.")
       st.stop()

    if doctor_name.strip() == "":
       st.error("❌ Please select Doctor.")
       st.stop()

    # =========================
     # DUPLICATE CHECK
     # =========================

    c.execute("""
        SELECT COUNT(*)
        FROM patients
        WHERE patient_name=? AND mobile=?
    """, (patient_name, mobile))

    exists = c.fetchone()[0]

    if exists > 0:
       st.warning("⚠️ Patient already exists with the same Name and Mobile.")
       st.stop()

    # =========================
    # AI PREDICTION
    # =========================

    patient_id = generate_patient_id()

    X = np.array(input_data).reshape(1, -1)
    X = scaler.transform(X)

    prediction = model.predict(X)
    probability = model.predict_proba(X)

    pred = int(prediction[0])
    if pred == 1:
       prob = float(probability[0][1])   # Malignant probability
    else:
       prob = float(probability[0][0])   # Benign probability

    st.write("Model Classes :", model.classes_)
    st.write("Prediction :", prediction)
    st.write("Probability :", probability)
    st.write("Prediction :", "Malignant" if pred == 1 else "Benign")
    st.write("Confidence :", f"{prob*100:.2f}%")
    risk_score = prob * 10

    if prob < 0.40:
       risk = "Low"
    elif prob < 0.70:
       risk = "Medium"
    else:
        risk = "High"
    # =========================
    # AI RECOMMENDATION
     # =========================

    st.markdown("---")
    st.subheader("📋 Final AI Recommendation")

    if risk_score > 8 and pred == 1:
       st.error("""
    🔴 Very High Risk

    • Immediate Mammography
    • Breast Ultrasound
    • Biopsy (if advised)
    • Consult an Oncologist
    """)

    elif risk_score > 3 or pred == 1:
       st.warning("""
    🟡 Moderate Risk

    • Clinical Breast Examination
    • Mammography Recommended
    • Follow-up with Doctor
    """)

    else:
      st.success("""
    🟢 Low Risk

    • Continue Annual Screening
    • Maintain Healthy Lifestyle
    • Routine Check-up
    """)

    # =========================
    # DATABASE SAVE
    # =========================

    c.execute("""
        INSERT INTO patients (
            patient_id,
            patient_name,
            age,
            gender,
            doctor_name,
            mobile,
            email,
            address,
            photo,
            date,
            prediction,
            probability,
            risk,
            doctor_notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            patient_id,
            patient_name,
            patient_age,
            gender,
            doctor_name,
            mobile,
            email,
            address,
            photo_path,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            int(pred),
            float(prob),
            risk,
            doctor_notes
        ))

    conn.commit()

     # =========================
     # RESULT
     # =========================

    st.subheader("Prediction Result")
    st.markdown("---")
    st.subheader("👤 Patient Summary")

    col1, col2 = st.columns(2)

    with col1:
            st.write(f"**Patient ID:** {patient_id}")
            st.write(f"**Patient Name:** {patient_name}")
            st.write(f"**Age:** {patient_age}")
            st.write(f"**Gender:** {gender}")

    with col2:
            st.write(f"**Doctor:** {doctor_name}")
            st.write(f"**Mobile:** {mobile}")
            st.write(f"**Email:** {email}")
            st.write(f"**Date:** {datetime.now().strftime('%d-%m-%Y %H:%M')}")

    if photo_path and os.path.exists(photo_path):
            st.image(photo_path, width=180)

    if pred == 0:
            st.success("🟢 Benign")
    else:
            st.error("🔴 Malignant")

    st.metric("Probability", f"{prob*100:.2f}%")
    st.progress(float(prob))

    st.subheader("📊 Risk Meter")

    if risk == "Low":
            st.success(f"🟢 Low Risk ({prob*100:.1f}%)")
    elif risk == "Medium":
            st.warning(f"🟡 Medium Risk ({prob*100:.1f}%)")
    else:
            st.error(f"🔴 High Risk ({prob*100:.1f}%)")

    st.markdown("---")

    col1, col2, col3 = st.columns(3)

    col1.metric("Diagnosis", "Malignant" if pred else "Benign")
    col2.metric("Confidence", f"{prob*100:.2f}%")
    col3.metric("Risk Level", risk)
     # ================= AI EXPLANATION =================
    st.markdown("---")
    st.subheader("🧠 AI Explanation")

    if hasattr(model, "feature_importances_"):
            importances = model.feature_importances_
    else:
            importances = np.ones(len(feature_names)) / len(feature_names)

    top = sorted(
            zip(feature_names, importances),
            key=lambda x: x[1],
            reverse=True
        )[:5]

    for f, s in top:
            st.write(f"**{f}** : {s:.3f}")

    st.markdown("---")
    st.subheader("🩺 AI Recommendation")

    if pred == 1:
            st.error("""
        🔴 High Possibility of Breast Cancer Detected

        Recommended Tests:
        • Mammography
        • Breast Ultrasound
        • MRI
        • Biopsy

        Consult an Oncologist Immediately.
        """)
    else:
            st.success("""
        🟢 No Significant Signs of Breast Cancer.

        Recommendation:
        • Regular Screening
        • Healthy Lifestyle
        • Annual Check-up
    """)

    
    # ============================================
     # DOCTOR PRESCRIPTION
     # ============================================

    st.markdown("---")
    st.subheader("💊 Doctor Prescription")

    medicine = st.text_area(
            "Medicines",
            placeholder="Example:\nTab Tamoxifen 20mg - Once Daily\nVitamin D - Once Daily"
        )

    advice = st.text_area(
            "Doctor Advice",
            placeholder="Write doctor's advice..."
        )

    next_visit = st.date_input("Next Visit Date")

    if st.button("💾 Save Prescription"):

            prescription = f"""
        Medicines:
        {medicine}

        Doctor Advice:
        {advice}

        Next Visit:
        {next_visit}
        """

            record_id = "MR" + str(random.randint(10000, 99999))

            c.execute("""
            INSERT INTO medical_records(
                record_id,
                patient_id,
                visit_date,
                doctor_name,
                symptoms,
                diagnosis,
                doctor_notes,
                prescription,
                lab_tests,
                treatment_plan,
                follow_up_date,
                created_by
            )
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                record_id,
                patient_id,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                doctor_name,
                "",
                "Malignant" if pred == 1 else "Benign",
                doctor_notes,
                prescription,
                "",
                advice,
                str(next_visit),
                st.session_state.username
            ))

            conn.commit()

            st.success("✅ Prescription Saved Successfully")
     # ============================================
     # LABORATORY TEST MANAGEMENT
     # ============================================
    st.markdown("---")
    st.subheader("🧪 Laboratory Test Management")

    mammography = st.checkbox("Mammography")
    ultrasound = st.checkbox("Breast Ultrasound")
    mri = st.checkbox("MRI")
    biopsy = st.checkbox("Biopsy")
    cbc = st.checkbox("CBC")
    blood_test = st.checkbox("Blood Test")

    test_status = st.selectbox(
            "Test Status",
            ["Pending", "Completed", "Reviewed"],
            key="lab_status"
        )

    if st.button("🧪 Save Laboratory Tests"):

            tests = []

            if mammography:
                tests.append("Mammography")

            if ultrasound:
                tests.append("Breast Ultrasound")

            if mri:
                tests.append("MRI")

            if biopsy:
                tests.append("Biopsy")

            if cbc:
                tests.append("CBC")

            if blood_test:
                tests.append("Blood Test")

            selected_tests = ", ".join(tests)

            record_id = "LAB" + str(random.randint(10000, 99999))

            c.execute("""
            INSERT INTO medical_records(
                record_id,
                patient_id,
                visit_date,
                doctor_name,
                symptoms,
                diagnosis,
                doctor_notes,
                prescription,
                lab_tests,
                treatment_plan,
                follow_up_date,
                created_by
            )
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                record_id,
                patient_id,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                doctor_name,
                "",
                "Malignant" if pred == 1 else "Benign",
                doctor_notes,
                "",
                selected_tests + " (" + test_status + ")",
                "",
                "",
                st.session_state.username
            ))

            conn.commit()

            st.success("✅ Laboratory Tests Saved Successfully")


    # ============================================
    # BILLING SYSTEM
    # ============================================

    st.markdown("---")
    st.subheader("💰 Hospital Billing")

    consultation_fee = st.number_input(
            "Consultation Fee (₹)",
            min_value=0,
            value=500,
            key="consultation_fee"
        )

    lab_fee = st.number_input(
            "Laboratory Test Charges (₹)",
            min_value=0,
            value=1000,
            key="lab_fee"
        )

    medicine_fee = st.number_input(
            "Medicine Charges (₹)",
            min_value=0,
            value=500,
            key="medicine_fee"
        )

    other_fee = st.number_input(
            "Other Charges (₹)",
            min_value=0,
            value=0,
            key="other_fee"
        )

    discount = st.number_input(
            "Discount (₹)",
            min_value=0,
            value=0,
            key="discount"
        )

    subtotal = (
            consultation_fee +
            lab_fee +
            medicine_fee +
            other_fee
        )

    gst = subtotal * 0.18
    total = subtotal + gst - discount

    st.markdown("### 🧾 Bill Summary")

    col1, col2 = st.columns(2)

    with col1:
            st.write("Consultation :", consultation_fee)
            st.write("Lab Tests :", lab_fee)
            st.write("Medicines :", medicine_fee)
            st.write("Other :", other_fee)

    with col2:
            st.write("GST (18%) :", round(gst, 2))
            st.write("Discount :", discount)
            st.success(f"Total Bill : ₹ {round(total, 2)}")

    if st.button("💳 Generate Bill"):

            bill_id = "BILL" + str(random.randint(10000, 99999))

            st.success("✅ Bill Generated Successfully")

            st.write("Bill ID :", bill_id)
            st.write("Patient :", patient_name)
            st.write("Patient ID :", patient_id)
            st.write("Doctor :", doctor_name)
            st.write("Final Amount : ₹", round(total, 2))
                    
     # ============================================
     # STAGE 3 : AI DOCTOR CONSULTATION
     # ============================================

    st.markdown("---")
    st.header("🔵 Stage 3 : AI Doctor Consultation & Treatment Plan")

    if pred == 1:

            st.error("👨‍⚕️ AI Doctor Opinion")

            st.write("""
        ### Initial Clinical Assessment

        The patient's clinical measurements indicate a high probability of breast cancer.

        ### Recommended Action Plan

        ✅ Consult an Oncologist immediately

        ✅ Mammography

        ✅ Breast Ultrasound

        ✅ Biopsy (if advised)

        ✅ MRI (if required)

        ### Follow-up

        • Book appointment within 24–48 hours

        • Carry previous medical reports

        • Do not delay further investigations

        ⚠️ Final diagnosis must be confirmed by a qualified medical professional.
        """)

    else:

            st.success("👨‍⚕️ AI Doctor Opinion")

            st.write("""
        ### Initial Clinical Assessment

        No significant evidence of breast cancer was detected.

        ### Recommendation

        ✅ Continue Annual Screening

        ✅ Perform Monthly Self Breast Examination

        ✅ Maintain Healthy Lifestyle

        ✅ Visit your doctor if new symptoms develop

        ⚠️ This AI assessment does not replace professional medical advice.
        """)
            
    # =========================
    # QR CODE GENERATION
    # =========================

    qr_data = f"""
        Hospital AI Breast Cancer Report

        Patient ID : {patient_id}

        Patient Name : {patient_name}

        Doctor : {doctor_name}

        Prediction : {"Malignant" if pred else "Benign"}

        Risk : {risk}

        Probability : {prob*100:.2f}%
        """

    qr = qrcode.make(qr_data)

    qr_file = f"{patient_id}_qr.png"

    qr.save(qr_file)
     # ================= PDF REPORT
        
    pdf = FPDF()
    pdf.add_page()
    pdf.image(qr_file, x=155, y=10, w=35)
    pdf.set_font("Arial", "B", 16)
       
    pdf.cell(190, 10, "Hospital AI Breast Cancer Report", ln=True, align="C")

    pdf.ln(5)

    pdf.set_font("Arial", "", 12)

    pdf.cell(190, 8, f"Patient ID : {patient_id}", ln=True)
    pdf.cell(190, 8, f"Patient Name : {patient_name}", ln=True)
    pdf.cell(190, 8, f"Age : {patient_age}", ln=True)
    pdf.cell(190, 8, f"Gender : {gender}", ln=True)
    pdf.cell(190, 8, f"Doctor : {doctor_name}", ln=True)
    pdf.cell(190, 8, f"Mobile : {mobile}", ln=True)
    pdf.cell(190, 8, f"Email : {email}", ln=True)
    pdf.cell(190, 8, f"Date : {datetime.now().strftime('%d-%m-%Y %H:%M')}", ln=True)

    pdf.ln(5)

    pdf.set_font("Arial", "B", 14)
    pdf.cell(190, 10, "Prediction Result", ln=True)

    pdf.set_font("Arial", "", 12)

    diagnosis = "Malignant" if pred == 1 else "Benign"

    pdf.cell(190, 8, f"Diagnosis : {diagnosis}", ln=True)
    pdf.cell(190, 8, f"Cancer Probability : {prob*100:.2f}%", ln=True)
    pdf.cell(190, 8, f"Risk Level : {risk}", ln=True)

    pdf.ln(5)

    pdf.set_font("Arial", "B", 14)
    pdf.cell(190, 10, "AI Recommendation", ln=True)

    pdf.set_font("Arial", "", 12)

    if pred == 1:
        pdf.multi_cell(
            190,
            8,
            "High possibility of breast cancer detected. Please consult an oncologist immediately and perform further clinical investigations."
        )
    else:
        pdf.multi_cell(
            190,
            8,
            "No significant signs of breast cancer detected. Continue regular screening and maintain a healthy lifestyle."
        )

    pdf.ln(5)

    pdf.set_font("Arial", "I", 10)
    pdf.multi_cell(
        190,
        6,
        "Disclaimer: This report is generated by an AI model and should not replace professional medical advice."
    )

    file = f"{patient_id}_report.pdf"
    pdf.output(file)
    if os.path.exists(qr_file):
        os.remove(qr_file)

    with open(file, "rb") as f:
        st.download_button(
            "📄 Download PDF Report",
            f,
            file_name=file
        )    
    st.success("✅ Patient Registered Successfully")
    st.success("✅ AI Analysis Completed")
    # ================= STAGE 4 =================

    st.markdown("---")
    st.header("📅 Stage 4 : Appointment Booking")

    if pred == 1:

        st.warning("High Risk Patient")

        if st.button("📅 Book Appointment"):

            appointment_id = "APT" + str(random.randint(1000,9999))

            appointment_date = datetime.now().strftime("%Y-%m-%d")
            appointment_time = "10:00 AM"

            c.execute("""
            INSERT INTO appointments(
            appointment_id,
            patient_id,
            patient_name,
            doctor_name,
            appointment_date,
            appointment_time,
            status
            )
            VALUES(?,?,?,?,?,?,?)
            """,(
            appointment_id,
            patient_id,
            patient_name,
            doctor_name,
            appointment_date,
            appointment_time,
            "Pending"
            ))

            conn.commit()

            st.success("✅ Appointment Booked Successfully")

            st.write("Appointment ID :", appointment_id)
            st.write("Doctor :", doctor_name)
            st.write("Date :", appointment_date)
            st.write("Time :", appointment_time)

    else:

            st.info("Appointment is not required for this patient.")
            st.success("✅ Report Generated")
    # ============================================
    # STAGE 5 : FOLLOW-UP & PATIENT MONITORING
    # ============================================

    st.markdown("---")
    st.header("🟣 Stage 5 : Follow-up & Patient Monitoring")

    if pred == 1:

        st.error("🔴 High Priority Follow-up")

        st.write("""
    ### Recommended Follow-up Plan

    📅 Follow-up Visit : Within 7 Days

    🩺 Repeat Clinical Examination

    📄 Carry Previous Reports

    💊 Follow Doctor's Advice

    ⚠ Do not ignore any new symptoms.
    """)

    else:

        st.success("🟢 Routine Follow-up")

        st.write("""
    ### Recommended Follow-up Plan

    📅 Annual Health Check-up

    🩺 Monthly Self Breast Examination

    🥗 Healthy Lifestyle

    🏃 Regular Exercise

    ⚠ Visit your doctor if new symptoms appear.
    """)
        st.subheader("📅 Next Follow-up Date")

    from datetime import timedelta

    if pred == 1:
        next_date = datetime.now() + timedelta(days=7)
    else:
        next_date = datetime.now() + timedelta(days=365)

    st.success(next_date.strftime("%d-%m-%Y"))
# ============================================
# DOCTOR PANEL
# ============================================
if menu == "👨‍⚕️ Doctor Panel":
  if st.session_state.role not in ["Doctor", "Admin"]:
    st.error("❌ Access Denied!")
    st.stop()

st.title("👨‍⚕️ Doctor Panel")

st.subheader("🩺 Patient List")

search = st.text_input(
    "🔍 Search Patient ID",
    key="doctor_search"
)

if search:

    c.execute("""
    SELECT
        patient_id,
        patient_name,
        age,
        gender,
        doctor_name,
        prediction,
        probability,
        risk,
        doctor_notes,
        date
    FROM patients
    WHERE patient_id LIKE ?
    """, ('%' + search + '%',))

else:

    if st.session_state.role == "Admin":

       c.execute("""
    SELECT
        patient_id,
        patient_name,
        age,
        gender,
        doctor_name,
        prediction,
        probability,
        risk,
        doctor_notes,
        date
    FROM patients
    ORDER BY id DESC
    """)

    else:

       c.execute("""
    SELECT
        patient_id,
        patient_name,
        age,
        gender,
        doctor_name,
        prediction,
        probability,
        risk,
        doctor_notes,
        date
    FROM patients
    WHERE doctor_name=?
    ORDER BY id DESC
    """, (st.session_state.username,))

patients = c.fetchall()

if patients:

    df = pd.DataFrame(
        patients,
        columns=[
            "Patient ID",
            "Name",
            "Age",
            "Gender",
            "Doctor",
            "Prediction",
            "Probability",
            "Risk",
            "Doctor Notes",
            "Date"
        ]
    )

    st.dataframe(df, use_container_width=True)
    st.markdown("---")
st.subheader("📝 Update Doctor Notes")

patient_id_update = st.text_input(
"Enter Patient ID",
key="update_patient_id"
)

new_notes = st.text_area(
"Doctor Notes",
key="update_notes"
)

if st.button("💾 Update Notes"):

   c.execute(
    "SELECT patient_id FROM patients WHERE patient_id=?",
    (patient_id_update,)
)

patient = c.fetchone()

if patient:

    c.execute("""
    UPDATE patients
    SET doctor_notes=?
    WHERE patient_id=?
    """, (
        new_notes,
        patient_id_update
    ))

    conn.commit()

    st.success("✅ Doctor Notes Updated Successfully")
    st.rerun()

else:
    st.error("❌ Patient ID Not Found")
    st.markdown("---")
st.subheader("👁 View Patient Record")

view_id = st.text_input(
"Enter Patient ID to View",
key="view_patient"
)

if st.button("View Record"):

   c.execute("""
SELECT
    patient_id,
    patient_name,
    age,
    gender,
    doctor_name,
    mobile,
    email,
    prediction,
    probability,
    risk,
    doctor_notes,
    date
FROM patients
WHERE patient_id=?
""", (view_id,))

patient = c.fetchone()

if patient:

    st.success("Patient Record Found")

    st.write("🆔 Patient ID :", patient[0])
    st.write("👤 Name :", patient[1])
    st.write("🎂 Age :", patient[2])
    st.write("⚧ Gender :", patient[3])
    st.write("👨‍⚕️ Doctor :", patient[4])
    st.write("📱 Mobile :", patient[5])
    st.write("📧 Email :", patient[6])
    st.write("🤖 Prediction :", "Malignant" if patient[7] else "Benign")
    st.write(f"📊 Probability : {patient[8]*100:.2f}%")
    st.write("⚠️ Risk :", patient[9])
    st.write("📝 Doctor Notes :", patient[10])
    st.write("📅 Date :", patient[11])

else:

    st.error("❌ Patient Not Found")

# ============================================
# ADMIN PANEL
# ============================================

if menu == "👨‍💼 Admin Panel":

   if st.session_state.role != "Admin":
    st.error("❌ Access Denied! Only Admin can access this panel.")
    st.stop()

st.title("👨‍💼 Admin Panel")

# ---------------- SYSTEM SUMMARY ----------------

st.subheader("📊 System Summary")

col1, col2, col3 = st.columns(3)

c.execute("SELECT COUNT(*) FROM users")
total_users = c.fetchone()[0]

c.execute("SELECT COUNT(*) FROM patients")
total_patients = c.fetchone()[0]

c.execute("SELECT COUNT(*) FROM appointments")
total_appointments = c.fetchone()[0]

col1.metric("Users", total_users)
col2.metric("Patients", total_patients)
col3.metric("Appointments", total_appointments)

st.markdown("---")

# ---------------- USERS ----------------

st.subheader("👥 Users")

c.execute("SELECT username, role FROM users")
users = c.fetchall()

if users:
    st.dataframe(
        pd.DataFrame(users, columns=["Username", "Role"]),
        use_container_width=True
    )
else:
    st.info("No users found.")

st.markdown("---")

# ---------------- HOSPITAL OVERVIEW ----------------

st.subheader("📊 Hospital Overview")

col1, col2, col3, col4 = st.columns(4)

c.execute("SELECT COUNT(*) FROM users")
total_users = c.fetchone()[0]

c.execute("SELECT COUNT(*) FROM patients")
total_patients = c.fetchone()[0]

c.execute("SELECT COUNT(*) FROM appointments")
total_appointments = c.fetchone()[0]

c.execute("SELECT COUNT(*) FROM users WHERE role='Doctor'")
total_doctors = c.fetchone()[0]

col1.metric("👥 Users", total_users)
col2.metric("🩺 Patients", total_patients)
col3.metric("📅 Appointments", total_appointments)
col4.metric("👨‍⚕️ Doctors", total_doctors)

st.markdown("---")

# ---------------- USER MANAGEMENT ----------------

st.subheader("👥 User Management")

search_user = st.text_input("🔍 Search Username")

if search_user:
   c.execute(
    "SELECT id, username, role FROM users WHERE username LIKE ?",
    ('%' + search_user + '%',)
)
else:
   c.execute(
    "SELECT id, username, role FROM users ORDER BY id DESC"
)

users = c.fetchall()

if users:
   df_users = pd.DataFrame(
    users,
    columns=["ID", "Username", "Role"]
)
   st.dataframe(df_users, use_container_width=True)
else:
   st.info("No users found.")

   st.markdown("---")

# ---------------- DELETE USER ----------------

st.markdown("---")
st.subheader("🗑 Delete User")

delete_user = st.text_input("Enter Username to Delete")

if st.button("Delete User"):

   if delete_user == st.session_state.username:
    st.error("❌ You cannot delete your own account.")

else:

    c.execute(
        "SELECT * FROM users WHERE username=?",
        (delete_user,)
    )

    user = c.fetchone()

    if user:

        c.execute(
            "DELETE FROM users WHERE username=?",
            (delete_user,)
        )

        conn.commit()

        st.success("✅ User Deleted Successfully")
        st.rerun()

    else:
        st.error("❌ User Not Found")

st.markdown("---")

# ---------------- PATIENT MANAGEMENT ----------------

st.subheader("🩺 Patient Management")

search_patient = st.text_input(
    "🔍 Search Patient ID",
    key="admin_patient_search"
)

if search_patient:

    c.execute("""
    SELECT
        patient_id,
        patient_name,
        doctor_name,
        risk,
        probability,
        date
    FROM patients
    WHERE patient_id LIKE ?
    """, ('%' + search_patient + '%',))

else:

    c.execute("""
    SELECT
        patient_id,
        patient_name,
        doctor_name,
        risk,
        probability,
        date
    FROM patients
    ORDER BY id DESC
    """)

patients = c.fetchall()

if patients:

    st.dataframe(
        pd.DataFrame(
            patients,
            columns=[
                "Patient ID",
                "Name",
                "Doctor",
                "Risk",
                "Probability",
                "Date"
            ]
        ),
        use_container_width=True
    )

else:

    st.info("No Patient Records Found()")


# ============================================
# DOCTOR DASHBOARD
# ============================================

if menu == "👨‍⚕️ Doctor Dashboard":

   st.title("👨‍⚕️ Doctor Dashboard")

if st.session_state.role == "Admin":

    c.execute("""
    SELECT
        appointment_id,
        patient_name,
        doctor_name,
        appointment_date,
        appointment_time,
        status
    FROM appointments
    ORDER BY appointment_date DESC
    """)

else:

    c.execute("""
    SELECT
        appointment_id,
        patient_name,
        doctor_name,
        appointment_date,
        appointment_time,
        status
    FROM appointments
    WHERE doctor_name=?
    ORDER BY appointment_date DESC
    """, (st.session_state.username,))

appointments = c.fetchall()

if len(appointments) == 0:

    st.info("No appointments found.")

else:

    for appt in appointments:

        with st.expander(f"📅 {appt[0]} | {appt[1]} | {appt[4]}"):

            st.write("**Appointment ID:**", appt[0])
            st.write("**Patient:**", appt[1])
            st.write("**Doctor:**", appt[2])
            st.write("**Date:**", appt[3])
            st.write("**Time:**", appt[4])
            st.write("**Current Status:**", appt[5])

            new_status = st.selectbox(
                "Update Status",
                ["Pending","Approved","Completed","Cancelled"],
                key=appt[0]
            )

            if st.button("Update", key="btn_"+appt[0]):

                c.execute("""
                UPDATE appointments
                SET status=?
                WHERE appointment_id=?
                """, (new_status, appt[0]))

                conn.commit()
                st.success("✅ Status Updated")
                st.rerun()
