"""
Task Manager Views
Demonstrates all CRUD operations with SimpleRDBMS
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Task, Category, TaskCategory
from django.db import connection


class TaskListView(View):
    """
    READ: List all tasks
    """
    def get(self, request):
        # Direct SQL query to our RDBMS
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM tasks")
        
        tasks = []
        for row in cursor.fetchall():
            # row format: (row_id, title, description, completed, priority)
            if len(row) >= 5:
                tasks.append({
                    'id': row[0],
                    'title': row[1],
                    'description': row[2],
                    'completed': row[3],
                    'priority': row[4],
                })
        
        # Get priority filter
        priority_filter = request.GET.get('priority')
        if priority_filter:
            tasks = [t for t in tasks if str(t['priority']) == priority_filter]
        
        # Get completion filter
        completed_filter = request.GET.get('completed')
        if completed_filter is not None:
            is_completed = completed_filter.lower() == 'true'
            tasks = [t for t in tasks if t['completed'] == is_completed]
        
        context = {
            'tasks': tasks,
            'priority_filter': priority_filter,
            'completed_filter': completed_filter,
        }
        return render(request, 'tasks/task_list.html', context)


class TaskCreateView(View):
    """
    CREATE: Add a new task
    """
    def get(self, request):
        return render(request, 'tasks/task_form.html', {'edit': False})
    
    def post(self, request):
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        priority = int(request.POST.get('priority', 1))
        
        # Direct INSERT using our RDBMS
        cursor = connection.cursor()
        sql = f"INSERT INTO tasks (title, description, completed, priority) VALUES ('{title}', '{description}', False, {priority})"
        cursor.execute(sql)
        
        return redirect('task_list')


class TaskDetailView(View):
    """
    READ: View a single task
    """
    def get(self, request, pk):
        cursor = connection.cursor()
        cursor.execute(f"SELECT * FROM tasks WHERE id = {pk}")
        
        row = cursor.fetchone()
        if not row or len(row) < 5:
            return redirect('task_list')
        
        task = {
            'id': row[0],
            'title': row[1],
            'description': row[2],
            'completed': row[3],
            'priority': row[4],
        }
        
        priorities = {1: 'Low', 2: 'Medium', 3: 'High'}
        task['priority_display'] = priorities.get(task['priority'], 'Unknown')
        
        return render(request, 'tasks/task_detail.html', {'task': task})


class TaskUpdateView(View):
    """
    UPDATE: Edit an existing task
    """
    def get(self, request, pk):
        cursor = connection.cursor()
        cursor.execute(f"SELECT * FROM tasks WHERE id = {pk}")
        
        row = cursor.fetchone()
        if not row or len(row) < 5:
            return redirect('task_list')
        
        task = {
            'id': row[0],
            'title': row[1],
            'description': row[2],
            'completed': row[3],
            'priority': row[4],
        }
        
        return render(request, 'tasks/task_form.html', {'task': task, 'edit': True})
    
    def post(self, request, pk):
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        completed = request.POST.get('completed') == 'on'
        priority = int(request.POST.get('priority', 1))
        
        # Direct UPDATE using our RDBMS
        cursor = connection.cursor()
        sql = f"UPDATE tasks SET title = '{title}', description = '{description}', completed = {completed}, priority = {priority} WHERE id = {pk}"
        cursor.execute(sql)
        
        return redirect('task_detail', pk=pk)


class TaskDeleteView(View):
    """
    DELETE: Remove a task
    """
    def post(self, request, pk):
        # Direct DELETE using our RDBMS
        cursor = connection.cursor()
        cursor.execute(f"DELETE FROM tasks WHERE id = {pk}")
        
        return redirect('task_list')


class TaskToggleView(View):
    """
    UPDATE: Toggle task completion status
    """
    def post(self, request, pk):
        cursor = connection.cursor()
        cursor.execute(f"SELECT * FROM tasks WHERE id = {pk}")
        
        row = cursor.fetchone()
        if row and len(row) >= 4:
            current_status = row[3]
            new_status = not current_status
            
            cursor.execute(f"UPDATE tasks SET completed = {new_status} WHERE id = {pk}")
        
        return redirect('task_list')


class CategoryListView(View):
    """
    READ: List all categories
    """
    def get(self, request):
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM categories")
        
        categories = []
        for row in cursor.fetchall():
            if len(row) >= 3:
                categories.append({
                    'id': row[0],
                    'name': row[1],
                    'description': row[2],
                })
        
        return render(request, 'tasks/category_list.html', {'categories': categories})


class CategoryCreateView(View):
    """
    CREATE: Add a new category
    """
    def get(self, request):
        return render(request, 'tasks/category_form.html')
    
    def post(self, request):
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        
        cursor = connection.cursor()
        sql = f"INSERT INTO categories (name, description) VALUES ('{name}', '{description}')"
        try:
            cursor.execute(sql)
            return redirect('category_list')
        except Exception as e:
            return render(request, 'tasks/category_form.html', {
                'error': 'Category name must be unique',
                'name': name,
                'description': description,
            })


def index(request):
    """
    Home page with dashboard
    """
    cursor = connection.cursor()
    
    # Get task counts
    cursor.execute("SELECT * FROM tasks")
    all_tasks = cursor.fetchall()
    
    total_tasks = len(all_tasks)
    completed_tasks = len([t for t in all_tasks if len(t) >= 4 and t[3]])
    pending_tasks = total_tasks - completed_tasks
    
    context = {
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'pending_tasks': pending_tasks,
    }
    
    return render(request, 'tasks/index.html', context)