# ===== tasks/views.py =====
"""
Django views for the task manager application.
"""
from django.shortcuts import render, redirect
from django.contrib import messages
from .db_wrapper import TaskDB


def index(request):
    """Main page showing all tasks."""
    rdbms = TaskDB.get_instance()
    
    try:
        # Get all tasks with user information via JOIN
        tasks = rdbms.execute("""
            SELECT * FROM tasks
            JOIN users ON tasks.user_id = users.id
        """)
        
        # Get all users for the form
        users = rdbms.execute("SELECT * FROM users")
    except Exception as e:
        messages.error(request, f"Database error: {e}")
        tasks = []
        users = []
    
    context = {
        'tasks': tasks,
        'users': users
    }
    
    return render(request, 'tasks/index.html', context)


def create_task(request):
    """Create a new task."""
    if request.method == 'POST':
        rdbms = TaskDB.get_instance()
        
        user_id = request.POST.get('user_id')
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        status = request.POST.get('status', 'pending')
        priority = request.POST.get('priority', '1')
        
        try:
            # Escape single quotes in strings
            title = title.replace("'", "''")
            description = description.replace("'", "''")
            
            result = rdbms.execute(f"""
                INSERT INTO tasks (user_id, title, description, status, priority)
                VALUES ({user_id}, '{title}', '{description}', '{status}', {priority})
            """)
            
            # Save to disk after modification
            TaskDB.save()
            
            messages.success(request, 'Task created successfully!')
            
        except Exception as e:
            messages.error(request, f"Error creating task: {e}")
    
    return redirect('index')


def update_task(request, task_id):
    """Update a task's status."""
    if request.method == 'POST':
        rdbms = TaskDB.get_instance()
        
        status = request.POST.get('status')
        
        try:
            # Update the status
            result = rdbms.execute(f"""
                UPDATE tasks SET status = '{status}'
                WHERE id = {task_id}
            """)
            
            # Save to disk after modification
            TaskDB.save()
            
            messages.success(request, 'Task updated successfully!')
            
        except Exception as e:
            messages.error(request, f"Error updating task: {e}")
    
    return redirect('index')


def delete_task(request, task_id):
    """Delete a task."""
    if request.method == 'POST':
        rdbms = TaskDB.get_instance()
        
        try:
            result = rdbms.execute(f"""
                DELETE FROM tasks WHERE id = {task_id}
            """)
            
            # Save to disk after modification
            TaskDB.save()
            
            messages.success(request, 'Task deleted successfully!')
            
        except Exception as e:
            messages.error(request, f"Error deleting task: {e}")
    
    return redirect('index')

def edit_task(request, task_id):
    """Handle task updates via modal form."""
    if request.method == 'POST':
        rdbms = TaskDB.get_instance()
        
        user_id = request.POST.get('user_id')
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        status = request.POST.get('status', 'pending')
        priority = request.POST.get('priority', '1')
        
        try:
            # Escape single quotes in strings
            title = title.replace("'", "''")
            description = description.replace("'", "''")
            
            result = rdbms.execute(f"""
                UPDATE tasks 
                SET user_id = {user_id}, 
                    title = '{title}', 
                    description = '{description}', 
                    status = '{status}', 
                    priority = {priority}
                WHERE id = {task_id}
            """)
            
            # Save to disk after modification
            TaskDB.save()
            
            messages.success(request, 'Task updated successfully!')
            
        except Exception as e:
            messages.error(request, f"Error updating task: {e}")
    
    return redirect('index')

def create_user(request):
    """Create a new user."""
    if request.method == 'POST':
        rdbms = TaskDB.get_instance()
        
        name = request.POST.get('name')
        email = request.POST.get('email')
        
        try:
            # Escape single quotes in strings
            name = name.replace("'", "''")
            email = email.replace("'", "''")
            
            result = rdbms.execute(f"""
                INSERT INTO users (name, email)
                VALUES ('{name}', '{email}')
            """)
            
            # Save to disk after modification
            TaskDB.save()
            
            messages.success(request, 'User created successfully!')
            
        except Exception as e:
            messages.error(request, f"Error creating user: {e}")
    
    return redirect('index')