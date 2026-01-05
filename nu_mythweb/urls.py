"""
URL configuration for nu_mythweb project.
"""

# from django.contrib import admin
from django.urls import path

from nu_mythweb.recordings.views import upcoming_list

urlpatterns = [
    path("", upcoming_list, name="upcoming"),
]
