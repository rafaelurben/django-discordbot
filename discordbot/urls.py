from django.urls import path

from . import views

##############

app_name = 'discordbot'
urlpatterns = [
    path('amongus/tracker/post', views.amongus_tracker_post, name="amongus-tracker-post"),
]
