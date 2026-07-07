import datetime
import re
from dataclasses import dataclass, fields
from typing import Optional


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
    # -3: Recorded (?)
    elif code == -3:
        return "status-recorded"
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
    start_time: Optional[datetime.datetime] = None
    end_time: Optional[datetime.datetime] = None
    air_date: Optional[datetime.datetime] = None
    raw_start_time: str = ""
    raw_end_time: str = ""
    status_display: str = ""
    status_code_class: str = ""
    category_code: str = ""
    category: str = ""
    category_type: str = ""
    season: int = None
    episode: int = None
    channel: dict = None
    recording: dict = None
    cast: dict = None
    filesize: int = None

    @classmethod
    def from_json(cls, data):
        """Factory method to initialize from MythTV API response."""

        # Build a kwargs dict of data for the class
        init_kwargs = {
            "category_code": category_slug(data["Category"]),
        }
        init_kwargs.update(cls.clean_values(data))
        # get recording status - for programs in guide, is None
        recording_data = data.get("Recording")
        if recording_data:
            init_kwargs.update(
                {
                    "status_display": split_camel_case(
                        recording_data.get("StatusName", "Unknown")
                    ),
                    "status_code_class": get_status_class(
                        int(recording_data.get("Status", 99))
                    ),
                }
            )
            init_kwargs["recording"] = cls.clean_values(recording_data, all=True)
        else:
            init_kwargs.update(
                {
                    "status_display": "Not Recording",
                    "status_code_class": "not-recording",
                }
            )

        return cls(**init_kwargs)

    @classmethod
    def clean_values(cls, data: dict, all: bool = False) -> dict:
        # clean up data values for conversion to myth program object
        # by default, only includes class fields; use all=true for all
        class_fields = {f.name for f in fields(cls)}
        cleaned_data = {}
        for key, val in data.items():
            key = key.lower()
            if key in class_fields:
                cleaned_data[key] = val
            elif key in ["starttime", "endtime", "startts", "endts"] and val:
                key = key.replace("time", "_time")  # add _ between start/end and time
                key = key.replace("ts", "_time")  # same for recording timestamp
                cleaned_data[key] = datetime.datetime.fromisoformat(val)
                # store raw value for use in forms
                cleaned_data[f"raw_{key}"] = val
            elif key == "airdate" and val:
                cleaned_data["air_date"] = datetime.date.fromisoformat(val)
            elif key == "cattype" and val:
                cleaned_data["category_type"] = val
            else:
                if all:  #  include all values when requested
                    cleaned_data[key] = val

        return cleaned_data

    @property
    def duration(self) -> datetime.timedelta | None:
        if self.end_time and self.start_time:
            return self.end_time - self.start_time
