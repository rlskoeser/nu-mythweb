from datetime import timedelta

import requests
from django.utils import timezone

from nu_mythweb.recordings.api_models import MythProgram


class MythTVService:
    def __init__(self, host="192.168.2.115", port=6744):
        self.base_url = f"http://{host}:{port}"
        self.headers = {"Accept": "application/json"}

    def _get(self, endpoint, params=None):
        """Internal helper for GET requests with error handling."""
        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.get(url, params=params, headers=self.headers, timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"MythTV API Error ({endpoint}): {e}")
            return {}

    def get_backend_status(self):
        """Fetch the backend status information."""
        data = self._get("Status/GetBackendStatus")
        return data.get("BackendStatus", {})

    def get_upcoming_recordings(self, limit=None):
        params = {}
        if limit is not None:
            params["Count"] = limit

        data = self._get("Dvr/GetUpcomingList", params=params)
        return [
            MythProgram.from_json(prog)
            for prog in data.get("ProgramList", {}).get("Programs", [])
        ]

    def get_recent_recordings(self, limit=10):
        params = {}
        if limit is not None:
            params["Count"] = limit

        data = self._get("Dvr/GetRecordedList", params=params)
        return [
            MythProgram.from_json(prog)
            for prog in data.get("ProgramList", {}).get("Programs", [])
        ]

    def search_guide(self, keyword, days=7):
        """Searches guide data for a specific keyword."""
        start_time = timezone.now()
        end_time = start_time + timedelta(days=days)

        params = {
            "StartTime": start_time.isoformat(),
            "EndTime": end_time.isoformat(),
            "Keyword": keyword,
            "Details": "true",
        }

        data = self._get("Guide/GetProgramList", params=params)
        raw_programs = data.get("ProgramList", {}).get("Programs", [])

        return [MythProgram.from_json(p) for p in raw_programs]

    def get_program_details(self, chan_id, start_time):
        """Fetches specific details for a single program."""
        params = {"ChanId": chan_id, "StartTime": start_time}
        data = self._get("Guide/GetProgramDetails", params=params)
        program_data = data.get("Program", {})
        return MythProgram.from_json(program_data) if program_data else None
