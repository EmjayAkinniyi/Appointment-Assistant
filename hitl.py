# hitl.py
# Logging and trace utilities for the appointment assistant

import os
import uuid
import json
import logging
from datetime import datetime

# ─────────────────────────────────────────
# LOGGING SETUP
# ─────────────────────────────────────────

def setup_logging():
    """Set up logging to both console and file."""
    os.makedirs("logs", exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.StreamHandler(),                          # Print to terminal
            logging.FileHandler("logs/run_log.txt", mode="a") # Save to file
        ]
    )

def generate_run_id() -> str:
    """Generate a unique run ID combining timestamp and short UUID."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    short_id  = str(uuid.uuid4())[:8]
    return f"RUN_{timestamp}_{short_id}"


# ─────────────────────────────────────────
# TRACE WRITER
# Saves execution evidence to a JSON file
# ─────────────────────────────────────────

def write_trace(state: dict):
    """
    Writes a trace/log file for the current run.
    Masks any sensitive values before saving.
    """
    os.makedirs("logs", exist_ok=True)

    trace = {
        "run_id":        state.get("run_id", "UNKNOWN"),
        "timestamp":     datetime.now().isoformat(),
        "final_status":  state.get("final_status", "UNKNOWN"),
        "intent":        state.get("intent", "UNKNOWN"),
        "route_taken":   state.get("route_taken", []),
        "tool_calls":    state.get("tool_call_count", 0),
        "pii_in_input":  "[MASKED]" if state.get("clean_input") != state.get("user_input") else "none",
        "appointment_id": state.get("appointment_id", "N/A"),
        "middleware_passed": state.get("middleware_passed", False),
        "hitl_approved":    state.get("hitl_approved", False),
        "final_response":   state.get("hitl_response", "")
    }

    filename = f"logs/trace_{state.get('run_id', 'unknown')}.json"
    with open(filename, "w") as f:
        json.dump(trace, f, indent=2)

    return filename