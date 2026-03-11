"""
URL configuration for nu_mythweb project.
"""

# from django.contrib import admin
from django.conf import settings
from django.urls import path
from django.views.generic.base import RedirectView

from nu_mythweb.recordings.views import (
    dashboard,
    guide_search,
    manage_recording,
    recordings_list,
    schedule_recording,
    upcoming_list,
)

urlpatterns = [
    path("", dashboard, name="home"),
    path("upcoming/", upcoming_list, name="upcoming"),
    path("guide/", guide_search, name="guide-search"),
    path("recording/schedule/", schedule_recording, name="schedule-recording"),
    path(
        "recording/manage/<int:recorded_id>/", manage_recording, name="manage-recording"
    ),
    path("recordings/", recordings_list, name="list-recordings"),
    path(
        "favicon.ico", RedirectView.as_view(url=settings.STATIC_URL + "img/favicon.ico")
    ),
]
