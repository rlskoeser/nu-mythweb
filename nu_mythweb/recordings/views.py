import re
from datetime import datetime

import requests
from django.shortcuts import render

# --- CONFIGURATION ---
MYTHTV_BACKEND_IP = "192.168.2.115"
MYTHTV_PORT = 6744


def split_camel_case(text):
    """Turns 'WillRecord' into 'Will Record'"""
    if not text:
        return text
    # This regex finds the boundary between lowercase and uppercase
    return re.sub(r"([a-z])([A-Z])", r"\1 \2", text)


def get_status_class(code):
    """Map MythTV numeric status codes to CSS class."""
    # 0: Recording, -2: Will Record
    if code in [0, -2]:
        return "status-recording"
    # -3: Conflict, -5: Offline/Error
    elif code in [-3, -5]:
        return "status-conflict"
    # Default for Previous, Don't Record, etc.
    else:
        return "status-default"


def upcoming_list(request):
    url = f"http://{MYTHTV_BACKEND_IP}:{MYTHTV_PORT}/Dvr/GetUpcomingList"
    context = {"programs": [], "error": None}

    try:
        response = requests.get(url, headers={"Accept": "application/json"}, timeout=5)
        response.raise_for_status()
        data = response.json()
        context["programs"] = data.get("ProgramList", {}).get("Programs", [])
        # parse starttime and end time as datetime
        for prog in context["programs"]:
            prog["dt_start"] = datetime.fromisoformat(prog["StartTime"])
            prog["dt_end"] = datetime.fromisoformat(prog["EndTime"])
            # get recording status
            recording_data = prog.get("Recording", {})
            prog["status_display"] = split_camel_case(
                recording_data.get("StatusName", "Unknown")
            )
            # convert numeric status to css class for display
            prog["status_code_class"] = get_status_class(
                int(recording_data.get("Status", 99))
            )
    except Exception as e:
        context["error"] = f"Could not connect to MythTV: {e}"

    return render(request, "recordings/upcoming.html", context)
