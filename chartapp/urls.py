from os import name
from django.urls import path
from .views import home, get_database_data, update_data_base

app_name = "chart"

urlpatterns = [
    path('', home, name="homepage"),
    path('scrap/', get_database_data, name="getData"),
    path('update/', update_data_base, name="updateDatabase"),
]