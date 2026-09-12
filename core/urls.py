from django.contrib import admin
from django.urls import path
from .views import Route
urlpatterns = [
    path('route/',Route.as_view())
]
