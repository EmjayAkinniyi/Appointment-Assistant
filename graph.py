# graph.py
# LangGraph workflow — core orchestration engine for the Appointment Assistant

import os
import json
import logging
from typing import TypedDict, Literal
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END

from tools import (
    lookup_appointment,
    view_all_appointments,
    view_available_slots,
    book_appointment,
    reschedule_appointment,
    cancel_appointment,
    get_prep_instructions
)
from middleware import run_middleware_checks
from data import is_emergency, is_medical_advice_request

load_dotenv()
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────
# 1. STATE DEFINITION
# ─────────────────────────────────────────

class AppointmentState(TypedDict):
    user_input: str
    clean_input: str
    intent: str
    appointment_id: str
    slot_id: str
    patient_name: str
    extra_info: dict
    tool_result: dict
    middleware_passed: bool
    middleware_reason: str
    hitl_approved: bool
    hitl_response: str
    final_status: str
    route_taken: list
    tool_call_count: int
    run_id: str


# ─────────────────────────────────────────
# 2. LLM SETUP
# ─────────────────────────────────────────

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    api_key=os.getenv("OPENAI_API_KEY")
)


# ─────────────────────────────────────────
# 3. NODE: INPUT PROCESSING
# ─────────────────────────────────────────

def input_node(state: AppointmentState) -> AppointmentState:
    logger.info("[Node: input] Processing user input")
    state["route_taken"].append("input_node")

    # Check for emergency first — highest priority
    if is_emergency(state["user_input"]):
        state["middleware_passed"] = False
        state["middleware_reason"] = "EMERGENCY_DETECTED"
        state["clean_input"] = state["user_input"]
        return state

    # Check for medical advice request
    if is_medical_advice_request(state["user_input"]):
        state["middleware_passed"] = False
        state["middleware_reason"] = "MEDICAL_ADVICE_REQUEST"
        state["clean_input"] = state["user_input"]
        return state

    # Run standard middleware checks
    result = run_middleware_checks(
        user_input=state["user_input"],
        tool_call_count=state["tool_call_count"]
    )

    state["middleware_passed"] = result["passed"]
    state["clean_input"] = result["clean_input"]
    state["middleware_reason"] = result.get("reason", "")

    if result["passed"] and result.get("pii_detected"):
        logger.info(f"[Node: input] PII masked: {result['pii_types']}")

    return state


# ─────────────────────────────────────────
# 4. NODE: EMERGENCY RESPONSE
# Bypasses all processing — immediate safety
# ─────────────────────────────────────────

def emergency_node(state: AppointmentState) -> AppointmentState:
    logger.warning("[Node: emergency] Emergency situation detected")
    state["route_taken"].append("emergency_node")
    state["final_status"] = "ESCALATE"
    state["hitl_response"] = (
        "\nEMERGENCY ALERT\n"
        "-----------------------------------------------\n"
        "This system is not equipped to handle medical emergencies.\n\n"
        "Please take immediate action:\n"
        "  -> Call 911 (or your local emergency number) NOW\n"
        "  -> Go to your nearest Emergency Room immediately\n"
        "  -> If in Canada, call 911 or visit the nearest ER\n\n"
        "Do not wait. Please seek immediate professional care.\n"
        "-----------------------------------------------"
    )
    return state


# ─────────────────────────────────────────
# 5. NODE: MEDICAL ADVICE DECLINE
# Politely declines and refers to a doctor
# ─────────────────────────────────────────

def medical_advice_node(state: AppointmentState) -> AppointmentState:
    logger.info("[Node: medical_advice] Medical advice request declined")
    state["route_taken"].append("medical_advice_node")
    state["final_status"] = "ESCALATE"
    state["hitl_response"] = (
        "Thank you for reaching out to Mojisola Akinniyi Medical Office.\n\n"
        "I am an appointment assistant and I am not able to provide "
        "medical diagnoses, clinical advice, or treatment recommendations. "
        "Providing such advice without a proper clinical assessment could "
        "be harmful to your health.\n\n"
        "What I recommend:\n"
        "  -> Book a consultation with one of our doctors\n"
        "  -> Contact your family physician directly\n"
        "  -> For urgent concerns, visit a walk-in clinic\n"
        "  -> For emergencies, call 911 immediately\n\n"
        "I am happy to help you book or manage an appointment right now.\n\n"
        "Best regards,\nMichelle Mary\nMojisola Akinniyi Medical Office"
    )
    return state


# ─────────────────────────────────────────
# 6. NODE: INTENT CLASSIFICATION
# ─────────────────────────────────────────

def intent_node(state: AppointmentState) -> AppointmentState:
    logger.info("[Node: intent] Classifying user intent")
    state["route_taken"].append("intent_node")

    system_prompt = """You are an appointment assistant classifier.
Analyze the user message and extract the following fields as a JSON object:

- intent: one of [reschedule, cancel, prep, book, view_appointment, view_slots, unknown]
- appointment_id: appointment ID if mentioned (e.g. APT001), else null
- slot_id: slot ID if mentioned (e.g. SLT001), else null
- patient_name: patient name if mentioned, else null
- new_date: new date if rescheduling, else null
- new_time: new time if rescheduling, else null
- reason: reason if cancelling, else null

Intent guide:
- reschedule: user wants to change date/time of existing appointment
- cancel: user wants to cancel an existing appointment
- prep: user wants preparation instructions for an appointment
- book: user wants to book a new appointment
- view_appointment: user wants to see their existing appointment(s)
- view_slots: user wants to see available appointment slots
- unknown: cannot determine intent

Respond ONLY with a valid JSON object. No explanation or extra text.
Example:
{"intent": "book", "appointment_id": null, "slot_id": "SLT002", "patient_name": "Jane Doe", "new_date": null, "new_time": null, "reason": null}
"""

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=state["clean_input"])
    ])

    try:
        parsed = json.loads(response.content)
    except Exception:
        parsed = {"intent": "unknown"}

    state["intent"]          = parsed.get("intent", "unknown")
    state["appointment_id"]  = parsed.get("appointment_id") or ""
    state["slot_id"]         = parsed.get("slot_id") or ""
    state["patient_name"]    = parsed.get("patient_name") or ""
    state["extra_info"] = {
        "new_date": parsed.get("new_date"),
        "new_time": parsed.get("new_time"),
        "reason":   parsed.get("reason")
    }

    logger.info(
        f"[Node: intent] Intent={state['intent']} | "
        f"APT={state['appointment_id']} | "
        f"Slot={state['slot_id']}"
    )
    return state


# ─────────────────────────────────────────
# 7. NODE: ACTION EXECUTION
# ─────────────────────────────────────────

def action_node(state: AppointmentState) -> AppointmentState:
    logger.info("[Node: action] Executing tool")
    state["route_taken"].append("action_node")
    state["tool_call_count"] += 1

    intent   = state["intent"]
    apt_id   = state["appointment_id"]
    slot_id  = state["slot_id"]
    name     = state["patient_name"]
    extra    = state["extra_info"]

    if intent == "view_appointment":
        if apt_id:
            state["tool_result"] = lookup_appointment(apt_id)
        else:
            state["tool_result"] = view_all_appointments()

    elif intent == "view_slots":
        state["tool_result"] = view_available_slots()

    elif intent == "book":
        if not slot_id:
            # Show available slots first
            state["tool_result"] = {
                "success": False,
                "needs_slot": True,
                "message": (
                    "To book an appointment, please choose a slot ID "
                    "from the list below and tell me your name.\n\n" +
                    view_available_slots()["message"]
                )
            }
        elif not name:
            state["tool_result"] = {
                "success": False,
                "message": "Please provide your full name to complete the booking."
            }
        else:
            state["tool_result"] = book_appointment(name, slot_id)

    elif intent == "reschedule":
        if not apt_id:
            state["tool_result"] = {
                "success": False,
                "message": "Please provide your appointment ID to reschedule (e.g. APT001)."
            }
        elif not extra.get("new_date") or not extra.get("new_time"):
            state["tool_result"] = {
                "success": False,
                "message": (
                    "To reschedule, I need both a new date and a new time.\n"
                    "Example: 'Reschedule APT001 to 2026-03-20 at 11:00 AM'"
                )
            }
        else:
            state["tool_result"] = reschedule_appointment(
                apt_id, extra["new_date"], extra["new_time"]
            )

    elif intent == "cancel":
        if not apt_id:
            state["tool_result"] = {
                "success": False,
                "message": "Please provide your appointment ID to cancel (e.g. APT002)."
            }
        else:
            state["tool_result"] = cancel_appointment(
                apt_id, reason=extra.get("reason") or "Not provided"
            )

    elif intent == "prep":
        if not apt_id:
            state["tool_result"] = {
                "success": False,
                "message": "Please provide your appointment ID to get prep instructions (e.g. APT003)."
            }
        else:
            state["tool_result"] = get_prep_instructions(apt_id)

    else:
        state["tool_result"] = {
            "success": False,
            "message": (
                "I am sorry, I did not understand your request.\n"
                "I can help you with:\n"
                "  -> Book a new appointment\n"
                "  -> View your existing appointments\n"
                "  -> Reschedule an appointment\n"
                "  -> Cancel an appointment\n"
                "  -> Get preparation instructions\n"
                "  -> View available appointment slots"
            )
        }

    return state


# ─────────────────────────────────────────
# 8. NODE: NEEDS INFO
# ─────────────────────────────────────────

def needs_info_node(state: AppointmentState) -> AppointmentState:
    logger.info("[Node: needs_info] Missing information")
    state["route_taken"].append("needs_info_node")
    state["final_status"] = "NEED_INFO"
    state["hitl_response"] = state["tool_result"].get(
        "message",
        "I need more information to complete your request. Could you please provide more details?"
    )
    return state


# ─────────────────────────────────────────
# 9. NODE: ESCALATION
# ─────────────────────────────────────────

def escalate_node(state: AppointmentState) -> AppointmentState:
    reason = state.get("middleware_reason", "")

    if reason == "EMERGENCY_DETECTED":
        return emergency_node(state)
    if reason == "MEDICAL_ADVICE_REQUEST":
        return medical_advice_node(state)

    logger.info("[Node: escalate] Escalating to human agent")
    state["route_taken"].append("escalate_node")
    state["final_status"] = "ESCALATE"
    state["hitl_response"] = (
        "Your request has been escalated to a human agent who will "
        "contact you shortly.\n"
        f"Reason: {reason or 'Policy or safety limit reached.'}\n\n"
        "Best regards,\nMichelle Mary\nMojisola Akinniyi Medical Office"
    )
    return state


# ─────────────────────────────────────────
# 10. NODE: HUMAN-IN-THE-LOOP (HITL)
# ─────────────────────────────────────────

def hitl_node(state: AppointmentState) -> AppointmentState:
    logger.info("[Node: hitl] Awaiting human review")
    state["route_taken"].append("hitl_node")

    draft_prompt = (
        f"You are a polite medical appointment assistant at Mojisola Akinniyi Medical Office.\n"
        f"Write a short, friendly, professional response to the patient based on this result:\n"
        f"{json.dumps(state['tool_result'], indent=2)}\n"
        f"Keep it under 9 sentences. Be warm and professional.\n"
        f"Do NOT include any sign-off or closing — that will be added separately."
    )

    draft = llm.invoke([HumanMessage(content=draft_prompt)])
    draft_response = draft.content.strip()

    # Remove any AI-generated sign-offs
    for placeholder in [
        "Best regards,", "Sincerely,", "Kind regards,",
        "Warm regards,", "Yours sincerely,"
    ]:
        if placeholder in draft_response:
            draft_response = draft_response[:draft_response.index(placeholder)].strip()

    # Add the official sign-off
    draft_response += "\n\nBest regards,\nMichelle Mary\nMojisola Akinniyi Medical Office"

    print("\n" + "="*55)
    print("  HUMAN-IN-THE-LOOP REVIEW REQUIRED")
    print("="*55)
    print(f"\nDraft response for patient:\n\n{draft_response}\n")
    print("-"*55)
    print("Options:")
    print("  [1] Approve this response")
    print("  [2] Edit this response")
    print("  [3] Reject and escalate")
    print("-"*55)

    choice = input("Your choice (1/2/3): ").strip()

    if choice == "1":
        state["hitl_approved"] = True
        state["hitl_response"] = draft_response
        state["final_status"]  = "READY"
        print("Response approved.")

    elif choice == "2":
        print("Enter your revised response (press Enter twice when done):")
        lines = []
        while True:
            line = input()
            if line == "":
                break
            lines.append(line)
        edited = "\n".join(lines).strip()
        edited += "\n\nBest regards,\nMichelle Mary\nMojisola Akinniyi Medical Office"
        state["hitl_response"] = edited
        state["hitl_approved"] = True
        state["final_status"]  = "READY"
        print("Edited response saved.")

    else:
        state["hitl_approved"] = False
        state["final_status"]  = "ESCALATE"
        state["hitl_response"] = (
            "Your request has been escalated to a senior agent for review.\n\n"
            "Best regards,\nMichelle Mary\nMojisola Akinniyi Medical Office"
        )
        print("Escalated to senior agent.")

    return state


# ─────────────────────────────────────────
# 11. ROUTING FUNCTIONS
# ─────────────────────────────────────────

def route_after_input(state: AppointmentState) -> Literal["escalate_node", "intent_node"]:
    if not state["middleware_passed"]:
        return "escalate_node"
    return "intent_node"

def route_after_intent(state: AppointmentState) -> Literal["action_node"]:
    return "action_node"

def route_after_action(state: AppointmentState) -> Literal["needs_info_node", "hitl_node"]:
    if not state["tool_result"].get("success", False):
        return "needs_info_node"
    return "hitl_node"


# ─────────────────────────────────────────
# 12. BUILD THE GRAPH
# ─────────────────────────────────────────

def build_graph():
    graph = StateGraph(AppointmentState)

    graph.add_node("input_node",        input_node)
    graph.add_node("intent_node",       intent_node)
    graph.add_node("action_node",       action_node)
    graph.add_node("needs_info_node",   needs_info_node)
    graph.add_node("escalate_node",     escalate_node)
    graph.add_node("hitl_node",         hitl_node)

    graph.set_entry_point("input_node")

    graph.add_conditional_edges(
        "input_node",
        route_after_input,
        {"escalate_node": "escalate_node", "intent_node": "intent_node"}
    )
    graph.add_conditional_edges(
        "intent_node",
        route_after_intent,
        {"action_node": "action_node"}
    )
    graph.add_conditional_edges(
        "action_node",
        route_after_action,
        {"needs_info_node": "needs_info_node", "hitl_node": "hitl_node"}
    )

    graph.add_edge("hitl_node",       END)
    graph.add_edge("needs_info_node", END)
    graph.add_edge("escalate_node",   END)

    return graph.compile()