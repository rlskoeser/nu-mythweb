import re
from datetime import datetime

import requests
from django.shortcuts import render

from nu_mythweb.recordings.api_models import MythProgram
from nu_mythweb.recordings.mythtv_service import MythTVService

# --- CONFIGURATION ---
MYTHTV_BACKEND_IP = "192.168.2.115"
MYTHTV_PORT = 6744


def dashboard(request):
    context = {"upcoming": [], "error": None}
    mythtv_service = MythTVService()
    try:
        # Fetch detailed Backend Status
        status = mythtv_service.get_backend_status()
        machine = status.get("MachineInfo", {})

        # Extract 'total' storage group for summary
        total_storage = next(
            (
                item
                for item in machine.get("StorageGroups", [])
                if item["Id"] == "total"
            ),
            {},
        )

        # Clean up data for the dashboard
        backend_info = {
            "load": machine.get("LoadAvg1"),
            "guide": {
                "status": machine.get("GuideStatus"),
                "days": machine.get("GuideDays"),
                "thru": datetime.fromisoformat(machine.get("GuideThru")),
            },
            "storage": {
                "total": total_storage.get("Total") * 1024 * 1024,
                "used": total_storage.get("Used") * 1024 * 1024,
                "free": total_storage.get("Free") * 1024 * 1024,
                "percent_used": total_storage.get("Used", 0)
                / total_storage.get("Total", 1)
                * 100,
            },
            "encoders": status.get("Encoders", []),
        }

        # display next 3 upcoming recordings included in backend info
        context["upcoming"] = [
            MythProgram.from_json(prog) for prog in status.get("Scheduled", [])[:3]
        ]
        context["recorded"] = mythtv_service.get_recent_recordings(limit=3)
        context["backend"] = backend_info

    except Exception as e:
        context["error"] = f"Error connecting to MythTV: {e}"

    return render(request, "recordings/dashboard.html", context)


def upcoming_list(request):
    context = {"programs": [], "error": None}

    try:
        context["programs"] = MythTVService().get_upcoming_recordings()
    except Exception as e:
        context["error"] = f"Could not connect to MythTV: {e}"

    return render(request, "recordings/upcoming.html", context)
