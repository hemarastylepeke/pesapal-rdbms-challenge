"""
Task Manager Models
Demonstrates CRUD operations with our custom SimpleRDBMS
"""

from django.db import models


class Task(models.Model):
    """
    Simple task model with basic fields
    """
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    completed = models.BooleanField(default=False)
    priority = models.IntegerField(default=1)  # 1=Low, 2=Medium, 3=High
    
    class Meta:
        db_table = 'tasks'
    
    def __str__(self):
        return self.title
    
    def get_priority_display(self):
        priorities = {1: 'Low', 2: 'Medium', 3: 'High'}
        return priorities.get(self.priority, 'Unknown')


class Category(models.Model):
    """
    Category model to demonstrate relationships
    Note: Our SimpleRDBMS doesn't enforce foreign keys,
    but we can still store the relationship
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    class Meta:
        db_table = 'categories'
        verbose_name_plural = 'Categories'
    
    def __str__(self):
        return self.name


class TaskCategory(models.Model):
    """
    Many-to-many relationship table
    Manually created since our RDBMS doesn't auto-create these
    """
    task_id = models.IntegerField()
    category_id = models.IntegerField()
    
    class Meta:
        db_table = 'task_categories'
        unique_together = [['task_id', 'category_id']]
    
    def __str__(self):
        return f"Task {self.task_id} - Category {self.category_id}"