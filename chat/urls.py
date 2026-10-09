
from django.urls import path
from . import views

urlpatterns = [
    path("chat/", views.chat_view, name="chat"),
    path("history/", views.chat_history_view, name="chat_history"),
    path(
        "edit/<int:message_id>/",
        views.edit_message_view,
        name="edit_message"
    ),
    path(
        "delete/<int:message_id>/",
        views.delete_message_view,
        name="delete_message"
    ),
]