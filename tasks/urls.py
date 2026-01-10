
# tasks/urls.py
"""
URL Configuration for Task Manager
"""

from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('task/create/', views.create_task, name='create_task'),
    path('task/<int:task_id>/update/', views.update_task, name='update_task'),
    path('task/<int:task_id>/delete/', views.delete_task, name='delete_task'),
    path('user/create/', views.create_user, name='create_user'),
    path('task/<int:task_id>/edit/', views.edit_task, name='edit_task'),
]