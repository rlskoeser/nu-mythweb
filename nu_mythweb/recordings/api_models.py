import datetime
import re
from dataclasses import dataclass, fields


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


@dataclass
class MythProgram:
    # field names match the lowercase version of the MythTV JSON API response keys
    title: str = ""
    subtitle: str = ""
    description: str = ""
    start_time: datetime = None
    end_time: datetime = None
    status_display: str = ""
    status_code_class: str = ""
    category_code: str = ""
    season: int = None
    episode: int = None
    channel: dict = None
    recording: dict = None

    @classmethod
    def from_json(cls, data):
        """Factory method to initialize from MythTV API response."""
        class_fields = {f.name for f in fields(cls)}

        # Build a kwargs dict of data for the class
        # get recording status
        recording_data = data.get("Recording", {})
        init_kwargs = {
            "status_display": split_camel_case(
                recording_data.get("StatusName", "Unknown")
            ),
            "status_code_class": get_status_class(
                int(recording_data.get("Status", 99))
            ),
            "category_code": category_slug(data["Category"]),
        }
        for key, val in data.items():
            key = key.lower()
            if key in class_fields:
                init_kwargs[key] = val
            elif key in ["starttime", "endtime"] and val:
                key = key.replace("time", "_time")  # add _ between start/end and time
                init_kwargs[key] = datetime.datetime.fromisoformat(val)

        return cls(**init_kwargs)

    @property
    def duration(self) -> datetime.timedelta:
        return self.end_time - self.start_time
