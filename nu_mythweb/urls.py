"""
URL configuration for nu_mythweb project.
"""

# from django.contrib import admin
from django.urls import path

from nu_mythweb.recordings.views import dashboard, guide_search, upcoming_list

urlpatterns = [
    path("", dashboard, name="home"),
    path("upcoming/", upcoming_list, name="upcoming"),
    path("guide/", guide_search, name="guide-search"),
]
