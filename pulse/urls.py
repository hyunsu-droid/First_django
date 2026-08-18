from django.urls import path

from . import views

app_name = "pulse"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("api/market/", views.market_api, name="market_api"),
]
