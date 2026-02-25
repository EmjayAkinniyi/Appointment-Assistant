# tools.py
# All tools (actions) the appointment assistant can perform

from data import (
    APPOINTMENTS,
    get_appointment,
    get_prep,
    get_available_slots,
    get_slot
)

import uuid
from datetime import datetime


def lookup_appointment(apt_id: str) -> dict:
    """Look up a specific appointment by ID."""
    apt = get_appointment(apt_id)
    if apt:
        return {
            "success": True,
            "appointment_id": apt_id.upper(),
            "details": apt,
            "message": (
                f"Appointment {apt_id.upper()} found.\n"
                f"  Patient  : {apt['patient_name']}\n"
                f"  Type     : {apt['type']}\n"
                f"  Doctor   : {apt['doctor']}\n"
                f"  Date     : {apt['date']} at {apt['time']}\n"
                f"  Status   : {apt['status'].upper()}"
            )
        }
    return {
        "success": False,
        "message": f"No appointment found with ID '{apt_id.upper()}'. Please check the ID and try again."
    }


def view_all_appointments() -> dict:
    """Return all appointments in the system."""
    if not APPOINTMENTS:
        return {
            "success": False,
            "message": "No appointments found in the system."
        }

    summary = []
    for apt_id, apt in APPOINTMENTS.items():
        summary.append(
            f"  [{apt_id}] {apt['type']} with {apt['doctor']} "
            f"on {apt['date']} at {apt['time']} — STATUS: {apt['status'].upper()}"
        )

    return {
        "success": True,
        "appointments": APPOINTMENTS,
        "message": "Here are all appointments on file:\n" + "\n".join(summary)
    }


def view_available_slots() -> dict:
    """Return all available appointment slots for booking."""
    slots = get_available_slots()
    if not slots:
        return {
            "success": False,
            "message": "No available slots at this time. Please call the clinic."
        }

    lines = []
    for slot in slots:
        lines.append(
            f"  [{slot['slot_id']}] {slot['type']} with {slot['doctor']} "
            f"({slot['department']}) — {slot['date']} at {slot['time']}"
        )

    return {
        "success": True,
        "slots": slots,
        "message": "Available appointment slots:\n" + "\n".join(lines)
    }


def book_appointment(
    patient_name: str,
    slot_id: str
) -> dict:
    """Book a new appointment for a patient using an available slot."""
    slot = get_slot(slot_id)

    if not slot:
        return {
            "success": False,
            "message": f"Slot '{slot_id.upper()}' not found. Please check the slot ID."
        }

    # Generate a new appointment ID
    new_id = f"APT{str(len(APPOINTMENTS) + 1).zfill(3)}"

    # Add to appointments database
    APPOINTMENTS[new_id] = {
        "patient_name": patient_name,
        "patient_id": f"P{uuid.uuid4().hex[:6].upper()}",
        "date": slot["date"],
        "time": slot["time"],
        "doctor": slot["doctor"],
        "department": slot["department"],
        "type": slot["type"],
        "status": "confirmed",
        "phone": "***-***-****",
        "email": "***@***.***",
        "booked_at": datetime.now().isoformat()
    }

    return {
        "success": True,
        "appointment_id": new_id,
        "patient_name": patient_name,
        "type": slot["type"],
        "doctor": slot["doctor"],
        "date": slot["date"],
        "time": slot["time"],
        "message": (
            f"Appointment successfully booked!\n"
            f"  Appointment ID : {new_id}\n"
            f"  Patient        : {patient_name}\n"
            f"  Type           : {slot['type']}\n"
            f"  Doctor         : {slot['doctor']}\n"
            f"  Date & Time    : {slot['date']} at {slot['time']}\n"
            f"  Status         : CONFIRMED"
        )
    }


def reschedule_appointment(apt_id: str, new_date: str, new_time: str) -> dict:
    """Reschedule an existing appointment to a new date and time."""
    apt_id = apt_id.upper()
    apt = get_appointment(apt_id)

    if not apt:
        return {
            "success": False,
            "message": f"Cannot reschedule: Appointment '{apt_id}' not found."
        }

    if apt["status"] == "cancelled":
        return {
            "success": False,
            "message": f"Cannot reschedule: Appointment '{apt_id}' has already been cancelled."
        }

    old_date = apt["date"]
    old_time = apt["time"]

    APPOINTMENTS[apt_id]["date"] = new_date
    APPOINTMENTS[apt_id]["time"] = new_time
    APPOINTMENTS[apt_id]["status"] = "rescheduled"

    return {
        "success": True,
        "appointment_id": apt_id,
        "patient_name": apt["patient_name"],
        "old_date": old_date,
        "old_time": old_time,
        "new_date": new_date,
        "new_time": new_time,
        "message": (
            f"Appointment {apt_id} successfully rescheduled.\n"
            f"  Patient  : {apt['patient_name']}\n"
            f"  Old slot : {old_date} at {old_time}\n"
            f"  New slot : {new_date} at {new_time}"
        )
    }


def cancel_appointment(apt_id: str, reason: str = "Not provided") -> dict:
    """Cancel an appointment by ID."""
    apt_id = apt_id.upper()
    apt = get_appointment(apt_id)

    if not apt:
        return {
            "success": False,
            "message": f"Cannot cancel: Appointment '{apt_id}' not found."
        }

    if apt["status"] == "cancelled":
        return {
            "success": False,
            "message": f"Appointment '{apt_id}' is already cancelled."
        }

    APPOINTMENTS[apt_id]["status"] = "cancelled"

    return {
        "success": True,
        "appointment_id": apt_id,
        "patient_name": apt["patient_name"],
        "cancelled_date": apt["date"],
        "reason": reason,
        "message": (
            f"Appointment {apt_id} successfully cancelled.\n"
            f"  Patient : {apt['patient_name']}\n"
            f"  Date    : {apt['date']} at {apt['time']}\n"
            f"  Reason  : {reason}"
        )
    }


def get_prep_instructions(apt_id: str) -> dict:
    """Get preparation instructions for a patient's appointment type."""
    apt_id = apt_id.upper()
    apt = get_appointment(apt_id)

    if not apt:
        return {
            "success": False,
            "message": f"Cannot find prep instructions: Appointment '{apt_id}' not found."
        }

    apt_type = apt["type"]
    instructions = get_prep(apt_type)

    return {
        "success": True,
        "appointment_id": apt_id,
        "patient_name": apt["patient_name"],
        "appointment_type": apt_type,
        "instructions": instructions,
        "message": (
            f"Preparation instructions for {apt['patient_name']}'s {apt_type} "
            f"with {apt['doctor']} on {apt['date']}:\n\n{instructions}"
        )
    }