import re
from datetime import datetime

import requests
from django.shortcuts import render

# --- CONFIGURATION ---
MYTHTV_BACKEND_IP = "192.168.2.115"
MYTHTV_PORT = 6744


def split_camel_case(text):
    """Turn status like 'WillRecord' into 'Will Record'"""
    if not text:
        return text
    # This regex finds the boundary between lowercase and uppercase
    return re.sub(r"([a-z])([A-Z])", r"\1 \2", text)


def category_slug(text):
    text = text.lower()

    if "sport" in text:
        # sports, playoff sports
        slug = "sports"
    else:
        # by default, use lowercase category as slug
        # animated, sitcom, animals, movie
        slug = text

    return slug


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


def get_upcoming_recordings(limit=None):
    url = f"http://{MYTHTV_BACKEND_IP}:{MYTHTV_PORT}/Dvr/GetUpcomingList"
    params = {}
    if limit is not None:
        params["Count"] = limit

    response = requests.get(
        url, headers={"Accept": "application/json"}, params=params, timeout=5
    )
    response.raise_for_status()
    data = response.json()
    programs = data.get("ProgramList", {}).get("Programs", [])

    for prog in programs:
        # parse starttime and end time as datetime
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
        # get category code
        prog["category_code"] = category_slug(prog["Category"])

    return programs


def get_recent_recordings(limit=10):
    url = f"http://{MYTHTV_BACKEND_IP}:{MYTHTV_PORT}/Dvr/GetRecordedList"
    params = {"descending": True}
    if limit is not None:
        params["Count"] = limit

    response = requests.get(
        url, headers={"Accept": "application/json"}, params=params, timeout=5
    )
    response.raise_for_status()
    data = response.json()
    programs = data.get("ProgramList", {}).get("Programs", [])
    for prog in programs:
        # parse starttime and end time as datetime
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
        # get category code
        prog["category_code"] = category_slug(prog["Category"])

    return programs


def dashboard(request):
    context = {"upcoming": [], "error": None}
    try:
        context["upcoming"] = get_upcoming_recordings(limit=3)
        context["recorded"] = get_recent_recordings(limit=3)
    except Exception as e:
        context["error"] = f"Could not connect to MythTV: {e}"

    return render(request, "recordings/dashboard.html", context)


def upcoming_list(request):
    context = {"programs": [], "error": None}

    try:
        context["programs"] = get_upcoming_recordings()
    except Exception as e:
        context["error"] = f"Could not connect to MythTV: {e}"

    return render(request, "recordings/upcoming.html", context)
