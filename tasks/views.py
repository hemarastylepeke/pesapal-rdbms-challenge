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
        raw_tasks = rdbms.execute("""
            SELECT * FROM tasks
            JOIN users ON tasks.user_id = users.id
        """)
        
        tasks = raw_tasks if raw_tasks else []
        
        # Get all users for the form
        raw_users = rdbms.execute("SELECT * FROM users")
        
        users = raw_users if raw_users else []
        
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


def execute_sql(request):
    """Execute a custom SQL query and return results as JSON."""
    from django.http import JsonResponse
    
    if request.method == 'POST':
        rdbms = TaskDB.get_instance()
        query = request.POST.get('query', '').strip()
        
        if not query:
            return JsonResponse({'error': 'Query cannot be empty'}, status=400)
        
        try:
            result = rdbms.execute(query)
            
            # Check if query modifies data
            query_upper = query.upper().strip()
            if any(query_upper.startswith(cmd) for cmd in ['INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP']):
                TaskDB.save()
                return JsonResponse({
                    'success': True,
                    'message': 'Query executed successfully',
                    'rows_affected': len(result) if isinstance(result, list) else 0
                })
            
            # For SELECT queries, normalize the result format
            if isinstance(result, list) and len(result) > 0:
                # Check if it's a list of tuples (row_id, row_dict) or list of dicts
                if isinstance(result[0], tuple):
                    # Format: [(row_id, {col: val, ...}), ...]
                    normalized_data = [row[1] for row in result]
                elif isinstance(result[0], dict):
                    # Format: [{col: val, ...}, ...] (from JOIN)
                    normalized_data = result
                else:
                    normalized_data = []
                
                return JsonResponse({
                    'success': True,
                    'columns': list(normalized_data[0].keys()) if normalized_data else [],
                    'data': normalized_data
                })
            else:
                # Empty result set
                return JsonResponse({
                    'success': True,
                    'columns': [],
                    'data': []
                })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)


def get_table_schema(request):
    """Get schema information for a specific table."""
    from django.http import JsonResponse
    
    table_name = request.GET.get('table', '')
    
    if not table_name:
        # Return list of all tables
        rdbms = TaskDB.get_instance()
        tables = list(rdbms.db.tables.keys())
        return JsonResponse({'tables': tables})
    
    try:
        rdbms = TaskDB.get_instance()
        
        if table_name not in rdbms.db.tables:
            return JsonResponse({'error': f'Table "{table_name}" not found'}, status=404)
        
        table = rdbms.db.tables[table_name]
        
        # Get column information - columns is a dict, not a list
        columns = []
        for col_name, col in table.columns.items():
            columns.append({
                'name': col.name,
                'type': col.dtype.value,  # Get the string value of the enum
                'primary_key': col.primary_key,
                'unique': col.unique,
                'nullable': not col.not_null
            })
        
        return JsonResponse({
            'table': table_name,
            'columns': columns
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)