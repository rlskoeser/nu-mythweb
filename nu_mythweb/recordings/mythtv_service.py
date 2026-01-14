from datetime import timedelta

import requests
from django.conf import settings
from django.utils import timezone

from nu_mythweb.recordings.api_models import MythProgram


class MythTVService:
    def __init__(self, host=settings.MYTHTV_HOST, port=settings.MYTHTV_PORT):
        self.base_url = f"http://{host}:{port}"
        self.headers = {"Accept": "application/json"}

    def _get(self, endpoint, params=None):
        """Internal helper for GET requests with error handling."""
        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.get(
                url, params=params, headers=self.headers, timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"MythTV API Error ({endpoint}): {e}")
            return {}

    def _post(self, endpoint, params=None, data=None):
        """Internal helper for POST requests with error handling."""
        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.post(
                url, data=data, params=params, headers=self.headers, timeout=10
            )
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
        params = {"descending": True}
        if limit is not None:
            params["Count"] = limit

        data = self._get("Dvr/GetRecordedList", params=params)
        return [
            MythProgram.from_json(prog)
            for prog in data.get("ProgramList", {}).get("Programs", [])
        ]

    def search_guide(self, query, filter="Keyword", channel_id=None, days=20):
        """Searches guide data for a specific keyword."""
        start_time = timezone.now()
        end_time = start_time + timedelta(days=days)

        params = {
            "StartTime": start_time.isoformat(),
            "EndTime": end_time.isoformat(),
            "Details": "true",
            "count": 100,
        }
        if query:
            if filter.lower() in ["title", "category", "person", "keyword"]:
                # uppercase first letter in filter
                params[f"{filter.title()}Filter"] = query
            else:
                raise ValueError(f"Invalid guide search filter: {filter}")
        if channel_id is not None:
            params["ChanId"] = channel_id
        data = self._get("Guide/GetProgramList", params=params)
        raw_programs = data.get("ProgramList", {}).get("Programs", [])

        return [MythProgram.from_json(p) for p in raw_programs]

    def get_program_details(self, chan_id, start_time):
        """Fetches specific details for a single program."""
        params = {"ChanId": chan_id, "StartTime": start_time}
        data = self._get("Guide/GetProgramDetails", params=params)
        program_data = data.get("Program", {})
        return MythProgram.from_json(program_data) if program_data else None

    def get_record_id(self, chan_id, start_time):
        """Get the recording rule for this showing and returns the ID."""
        params = {"ChanId": chan_id, "StartTime": start_time}
        # This endpoint checks for a rule covering this specific time/channel
        data = self._get("Dvr/GetRecordSchedule", params=params)

        # MythTV returns 'RecRule' if found
        rule = data.get("RecRule", {})
        return rule.get("Id") if rule else None

    def remove_record_schedule(self, record_id: int) -> bool:
        """Remove a scheduled recording rule by RecordId."""
        params = {"RecordId": record_id}
        api_endpoint = "Dvr/RemoveRecordSchedule"
        try:
            # post the request
            response = self._post(api_endpoint, params=params)
            return response["bool"]
        except Exception:
            return False

    def update_record_schedule(
        self, chan_id, start_time, record_type="one", record_id: int = None
    ):
        """
        Add or update a recording schedule.
        """
        # First, get record schedule to add or update.
        # If record id is valid, that will be used. Otherwise, channel id and
        # start time are used to get a recording rule (existing or new), which can then
        # be added or updated.

        rule_params = {
            "ChanId": chan_id,
            "StartTime": start_time,
            "RecordId": record_id,
        }
        response = self._get("Dvr/GetRecordSchedule", params=rule_params)
        recording_rule = response["RecRule"]
        # # If ID is 0, this is a new rule, so we Add. Otherwise Update.
        if recording_rule.get("Id") == 0:
            action = "Add"
        else:
            action = "Update"
        endpoint = f"Dvr/{action}RecordSchedule"

        # update recording rule
        if record_type == "one":
            rec_type = "Record One"
        elif record_type == "all":
            rec_type = "Record All"
        else:
            raise ValueError(f"Unsupported recording type `{record_type}`")

        if recording_rule["Type"] == rec_type:
            print("recording type is already as desired")
            return

        recording_rule["Type"] = rec_type
        # set station from channel call sign
        recording_rule["Station"] = recording_rule["CallSign"]
        # POST the updated recording rule to the add/update api endpoint
        result = self._post(endpoint, data=recording_rule)
        # returns an id for the added recording rule
        return result["uint"]
