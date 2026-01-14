import time
from datetime import datetime

from django.shortcuts import render
from django.views.decorators.http import require_POST

from nu_mythweb.recordings.api_models import MythProgram
from nu_mythweb.recordings.mythtv_service import MythTVService


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


def guide_search(request):
    query = request.GET.get("q", "")
    search_type = request.GET.get("search-filter", "keyword")
    chan_id = request.GET.get("channel_id")
    results = []

    # don't allow empty searches; require either keyword or filter
    if query or chan_id:
        results = MythTVService().search_guide(query, search_type, channel_id=chan_id)

    return render(
        request,
        "recordings/guide_search.html",
        {
            "results": results,
            "query": query,
            "search_filter": search_type,
            "channel_id": chan_id,
        },
    )


@require_POST
def schedule_recording(request):
    record_id = request.POST.get("record_id")  # available when existing rule
    chan_id = request.POST.get("chan_id")
    start_time = request.POST.get("start_time")
    record_type = request.POST.get("record_type")
    myth_api = MythTVService()
    if record_type == "cancel" and record_id:
        success = myth_api.remove_record_schedule(record_id)
    else:
        success = myth_api.update_record_schedule(
            chan_id, start_time, record_type=record_type, record_id=record_id
        )

    # get updated program
    time.sleep(0.3)  # program details are not refreshed immediately...
    program = myth_api.get_program_details(chan_id, start_time)

    if success:
        # make sure program details has updated recording information
        # TODO: should probably set a limit here...
        while 1:
            if (record_type == "cancel" and program.recording) or (
                record_type != "cancel" and program.recording is None
            ):
                program = myth_api.get_program_details(chan_id, start_time)
            else:
                break

    # re-render the record form portion of the recording status
    return render(
        request,
        "recordings/partials/program_record_status.html",
        {
            "program": program,
            "updated": success,
        },
    )
