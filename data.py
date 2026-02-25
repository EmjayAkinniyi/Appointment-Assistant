# data.py
# Appointment database and available slots for the Appointment Assistant System

APPOINTMENTS = {
    "APT001": {
        "patient_name": "John Davis",
        "patient_id": "P1001",
        "date": "2026-03-05",
        "time": "10:00 AM",
        "doctor": "Dr. Emily Carter",
        "department": "Radiology",
        "type": "MRI Scan",
        "status": "confirmed",
        "phone": "555-***-1234",
        "email": "m***@email.com"
    },
    "APT002": {
        "patient_name": "John Davis",
        "patient_id": "P1002",
        "date": "2026-03-07",
        "time": "2:30 PM",
        "doctor": "Dr. James Lee",
        "department": "Pathology",
        "type": "Blood Test",
        "status": "confirmed",
        "phone": "555-***-5678",
        "email": "m***@email.com"
    },
    "APT003": {
        "patient_name": "John Davis",
        "patient_id": "P1003",
        "date": "2026-03-10",
        "time": "9:00 AM",
        "doctor": "Dr. Sarah Patel",
        "department": "Radiology",
        "type": "X-Ray",
        "status": "confirmed",
        "phone": "555-***-9012",
        "email": "m***@email.com"
    },
}

# Available slots for booking new appointments
AVAILABLE_SLOTS = [
    {"slot_id": "SLT001", "date": "2026-03-12", "time": "9:00 AM",  "doctor": "Dr. Emily Carter", "department": "Radiology",    "type": "MRI Scan"},
    {"slot_id": "SLT002", "date": "2026-03-12", "time": "11:00 AM", "doctor": "Dr. James Lee",    "department": "Pathology",    "type": "Blood Test"},
    {"slot_id": "SLT003", "date": "2026-03-13", "time": "2:00 PM",  "doctor": "Dr. Sarah Patel",  "department": "Radiology",    "type": "X-Ray"},
    {"slot_id": "SLT004", "date": "2026-03-14", "time": "10:00 AM", "doctor": "Dr. Kevin Marsh",  "department": "Cardiology",   "type": "ECG"},
    {"slot_id": "SLT005", "date": "2026-03-15", "time": "3:00 PM",  "doctor": "Dr. Lisa Nguyen",  "department": "Neurology",    "type": "Consultation"},
    {"slot_id": "SLT006", "date": "2026-03-17", "time": "8:30 AM",  "doctor": "Dr. Emily Carter", "department": "Radiology",    "type": "MRI Scan"},
    {"slot_id": "SLT007", "date": "2026-03-18", "time": "1:00 PM",  "doctor": "Dr. Kevin Marsh",  "department": "Cardiology",   "type": "ECG"},
]

PREP_INSTRUCTIONS = {
    "MRI Scan": (
        "1. Remove all metal objects (jewelry, piercings, hearing aids).\n"
        "2. Avoid eating 4 hours before the scan.\n"
        "3. Wear comfortable, loose-fitting clothing with no metal.\n"
        "4. Inform staff of any implants, pacemakers, or claustrophobia.\n"
        "5. Arrive 15 minutes early to complete paperwork."
    ),
    "Blood Test": (
        "1. Fast for at least 8-12 hours before the test (water is allowed).\n"
        "2. Avoid strenuous exercise the night before.\n"
        "3. Take prescribed medications as normal unless told otherwise.\n"
        "4. Bring your insurance card, photo ID, and referral letter.\n"
        "5. Stay hydrated — drink plenty of water before your visit."
    ),
    "X-Ray": (
        "1. No special preparation is needed in most cases.\n"
        "2. Remove metal objects, jewelry, and clothing with zippers.\n"
        "3. Inform staff immediately if you are or may be pregnant.\n"
        "4. Wear comfortable, easy-to-remove clothing.\n"
        "5. Bring any previous imaging results if available."
    ),
    "ECG": (
        "1. Avoid applying lotions or oils to your chest area on the day.\n"
        "2. Wear a two-piece outfit for easy access to the chest.\n"
        "3. Avoid caffeine and cigarettes for at least 3 hours before.\n"
        "4. Continue all prescribed medications unless told otherwise.\n"
        "5. Arrive 10 minutes early to rest before the procedure."
    ),
    "Consultation": (
        "1. Bring a list of all current medications and dosages.\n"
        "2. Prepare a summary of your symptoms and when they started.\n"
        "3. Bring previous test results, scans, or medical records.\n"
        "4. Write down any questions you want to ask the doctor.\n"
        "5. Bring your insurance card and a valid photo ID."
    ),
}

# Emergency keywords that trigger immediate safety escalation
EMERGENCY_KEYWORDS = [
    "chest pain", "heart attack", "can't breathe", "cannot breathe",
    "difficulty breathing", "stroke", "unconscious", "not breathing",
    "severe bleeding", "overdose", "poisoning", "seizure", "choking",
    "emergency", "dying", "collapsed", "fainted", "suicidal", "suicide"
]

# Keywords indicating the user wants medical advice (which we must decline)
MEDICAL_ADVICE_KEYWORDS = [
    "diagnose", "diagnosis", "do i have", "what disease", "what condition",
    "is it cancer", "should i take", "what medication", "what medicine",
    "treat my", "treatment for", "cure for", "symptoms of", "medical advice",
    "what is wrong with me", "what's wrong with me"
]

# ─────────────────────────────────────────
# DATABASE HELPER FUNCTIONS
# ─────────────────────────────────────────

def get_appointment(apt_id: str):
    return APPOINTMENTS.get(apt_id.upper(), None)

def get_all_appointment_ids():
    return list(APPOINTMENTS.keys())

def get_prep(appointment_type: str):
    return PREP_INSTRUCTIONS.get(
        appointment_type,
        "No specific preparation instructions found. Please contact the clinic for details."
    )

def get_available_slots():
    return AVAILABLE_SLOTS

def get_slot(slot_id: str):
    for slot in AVAILABLE_SLOTS:
        if slot["slot_id"].upper() == slot_id.upper():
            return slot
    return None

def is_emergency(text: str) -> bool:
    text_lower = text.lower()
    return any(kw in text_lower for kw in EMERGENCY_KEYWORDS)

def is_medical_advice_request(text: str) -> bool:
    text_lower = text.lower()
    return any(kw in text_lower for kw in MEDICAL_ADVICE_KEYWORDS)