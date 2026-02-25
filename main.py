# main.py
# CLI entry point for the Appointment Assistant System
# Mojisola Akinniyi Medical Office

from hitl import setup_logging, generate_run_id, write_trace
from graph import build_graph


def print_banner():
    print("\n" + "="*55)
    print("   MOJISOLA AKINNIYI MEDICAL OFFICE")
    print("   Appointment Assistant System")
    print("   Powered by LangGraph + OpenAI")
    print("="*55)
    print("\nWelcome! I can help you with:")
    print("  -> Book a new appointment")
    print("  -> View your existing appointments")
    print("  -> Reschedule an appointment")
    print("  -> Cancel an appointment")
    print("  -> Get preparation instructions")
    print("  -> View available appointment slots")
    print("\nType 'exit' or 'quit' at any time to leave.")
    print("="*55)


def print_final_output(state: dict, trace_file: str):
    print("\n" + "="*55)
    print("  PATIENT RESPONSE SENT")
    print("="*55)
    print(f"\n{state['hitl_response']}\n")
    print("="*55)
    print("  EXECUTION SUMMARY")
    print("="*55)

    # Human-friendly status message
    status = state['final_status']
    intent = state['intent']
    apt_id = state.get('appointment_id', '')
    name   = state.get('patient_name', '')

    if status == "READY":
        if intent == "cancel":
            print(f"  Action   : Appointment {apt_id} has been cancelled.")
        elif intent == "reschedule":
            print(f"  Action   : Appointment {apt_id} has been rescheduled.")
        elif intent == "book":
            print(f"  Action   : New appointment booked for {name}.")
        elif intent == "view_slots":
            print(f"  Action   : Available slots shown to patient.")
        elif intent == "view_appointment":
            print(f"  Action   : Appointment details retrieved and shared.")
        elif intent == "prep":
            print(f"  Action   : Preparation instructions sent for {apt_id}.")
        else:
            print(f"  Action   : Request handled successfully.")

    elif status == "NEED_INFO":
        print(f"  Action   : More information needed from patient.")
        print(f"  Next Step: Patient must provide missing details to proceed.")

    elif status == "ESCALATE":
        print(f"  Action   : Request escalated — human agent will follow up.")

    print(f"  Status   : {status}")
    print(f"  Intent   : {intent}")
    print(f"  HITL     : {'Approved' if state.get('hitl_approved') else 'Not required / Escalated'}")
    print(f"  Run ID   : {state['run_id']}")
    print(f"  Route    : {' -> '.join(state['route_taken'])}")
    print(f"  Trace    : {trace_file}")
    print("="*55)

def run_single_request(user_input: str, graph):
    """Run one request through the graph and return the final state."""
    run_id = generate_run_id()

    initial_state = {
        "user_input":        user_input,
        "clean_input":       "",
        "intent":            "",
        "appointment_id":    "",
        "slot_id":           "",
        "patient_name":      "",
        "extra_info":        {},
        "tool_result":       {},
        "middleware_passed": False,
        "middleware_reason": "",
        "hitl_approved":     False,
        "hitl_response":     "",
        "final_status":      "",
        "route_taken":       [],
        "tool_call_count":   0,
        "run_id":            run_id
    }

    print(f"\n[Run ID: {run_id}]")
    final_state = graph.invoke(initial_state)
    trace_file  = write_trace(final_state)
    print_final_output(final_state, trace_file)
    return final_state


def main():
    setup_logging()
    print_banner()

    # Build the graph once and reuse it
    graph = build_graph()

    print("\nExample requests you can try:")
    print("  'Show me my appointments'")
    print("  'What slots are available?'")
    print("  'Book slot SLT002 for Mojisola Akinniyi'")
    print("  'Reschedule APT001 to 2026-03-20 at 11:00 AM'")
    print("  'Cancel appointment APT002'")
    print("  'Get prep instructions for APT003'")
    print("  'I have chest pain' (tests emergency handling)")
    print("  'What medication should I take?' (tests safety)")
    print("-"*55)

    # Interactive loop
    while True:
        try:
            user_input = input("\nYour request: ").strip()

            if not user_input:
                print("Please enter a request or type 'exit' to quit.")
                continue

            if user_input.lower() in ["exit", "quit", "bye", "goodbye"]:
                print("\nThank you for using Mojisola Akinniyi Medical Office.")
                print("Goodbye and stay healthy!")
                print("="*55)
                break

            run_single_request(user_input, graph)

        except KeyboardInterrupt:
            print("\n\nSession ended. Goodbye!")
            break


if __name__ == "__main__":
    main()