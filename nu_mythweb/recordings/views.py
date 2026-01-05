from datetime import datetime

import requests
from django.shortcuts import render

# --- CONFIGURATION ---
MYTHTV_BACKEND_IP = "192.168.2.115"
MYTHTV_PORT = 6544


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
    except Exception as e:
        context["error"] = f"Could not connect to MythTV: {e}"

    return render(request, "recordings/upcoming.html", context)
