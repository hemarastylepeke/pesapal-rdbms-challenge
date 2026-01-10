# ===== tasks/apps.py =====
"""
Django app configuration for tasks.
"""
from django.apps import AppConfig


class TasksConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tasks'
