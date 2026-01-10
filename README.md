# Task Manager with Custom RDBMS

A fully functional task management web application built with Django and powered by a custom-built Relational Database Management System (RDBMS) written from scratch in Python.

## 🚀 Live Demo

**[View Live Project](https://your-project-url.com)**

## 📋 Overview

This project demonstrates the implementation of a complete RDBMS from the ground up, featuring:

- **Custom Database Engine** - Built entirely in Python without any external database dependencies
- **SQL Parser** - Parses and executes SQL commands (CREATE, INSERT, SELECT, UPDATE, DELETE)
- **JOIN Operations** - Supports INNER JOINs for relational queries
- **Indexing** - Automatic indexing on primary keys and unique columns for optimized lookups
- **Data Persistence** - Database state is serialized and saved to disk using Python's pickle
- **Django Integration** - Seamlessly integrated with Django's web framework

## ✨ Features

### Database Features
- **Full CRUD Operations** - Create, Read, Update, Delete records
- **SQL Query Support** - Standard SQL syntax for database operations
- **Data Types** - INTEGER, TEXT, and REAL data types
- **Constraints** - PRIMARY KEY, UNIQUE, NOT NULL constraints
- **Indexing** - Automatic index creation and maintenance
- **JOIN Support** - Multi-table queries with INNER JOIN
- **Transaction Safety** - Data validation and type checking

### Application Features
- **Task Management** - Create, edit, update, and delete tasks
- **User Assignment** - Assign tasks to different users
- **Status Tracking** - Track task status (Pending, In Progress, Completed)
- **Priority Levels** - Set task priorities (Low, Medium, High)
- **Modal Editing** - Edit tasks without leaving the main page
- **Real-time Updates** - Instant feedback with Django messages
- **Responsive Design** - Modern UI built with Tailwind CSS

## 🛠️ Technology Stack

- **Backend**: Python 3.12.10, Django
- **Frontend**: HTML5, Tailwind CSS, JavaScript
- **Database**: Custom RDBMS (Python)
- **Styling**: Barlow Font, Custom CSS

## 📁 Project Structure

```
project/
├── simple_rdbms.py          # Custom RDBMS implementation
├── tasks/
│   ├── views.py             # Django view functions
│   ├── urls.py              # URL routing
│   ├── db_wrapper.py        # Database wrapper and initialization
│   ├── templatetags/
│   │   └── task_filters.py  # Custom template filters
│   └── templates/
│       └── tasks/
│           └── index.html   # Main application page
├── custom_rdbms.db          # Persisted database file
└── README.md
........
```

## 🚦 Getting Started

### Prerequisites

- Python 3.8 or higher
- Django 4.0 or higher
- django-tailwind (optional, for Tailwind CSS)

### Installation

1. **Clone the repository**
   ```bash
   git https://github.com/hemarastylepeke/pesapal-rdbms-challenge.git
   cd pesapal-rdbms-challenge
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations** (if any Django migrations exist)
   ```bash
   python manage.py migrate
   ```

5. **Start the development server**
   ```bash
   python manage.py runserver localhost:8000
   ```

6. **Open your browser**
   Navigate to `http://localhost:8000`

### First Time Setup

On first run, the application will automatically:
- Create the custom database file (`custom_rdbms.db`)
- Initialize the schema (users and tasks tables)
- Create sample users (Alice Smith and Bob Jones)

## 📖 How It Works

### Custom RDBMS Architecture

The custom RDBMS (`simple_rdbms.py`) implements:

1. **Data Structures**
   - `Database`: Container for multiple tables
   - `Table`: Stores rows and manages indexes
   - `Column`: Defines column properties and constraints
   - `Index`: Hash-based index for fast lookups

2. **SQL Parser**
   - Regex-based parsing of SQL commands
   - Supports CREATE TABLE, INSERT, SELECT, UPDATE, DELETE
   - WHERE clause evaluation
   - JOIN operation parsing

3. **Storage Engine**
   - In-memory row storage using dictionaries
   - Automatic ID generation for primary keys
   - Pickle-based serialization for persistence

### Database Schema

**Users Table**
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE
)
```

**Tasks Table**
```sql
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL,
    priority INTEGER
)
```

### Example Queries

```sql
-- Create a new task
INSERT INTO tasks (user_id, title, description, status, priority)
VALUES (1, 'Complete project', 'Finish the RDBMS implementation', 'in-progress', 2)

-- Get all tasks with user information
SELECT * FROM tasks
JOIN users ON tasks.user_id = users.id

-- Update task status
UPDATE tasks SET status = 'completed'
WHERE id = 1

-- Delete a task
DELETE FROM tasks WHERE id = 1
```

## 🔧 Customization

### Adding New Fields

1. Update the schema in `db_wrapper.py`:
   ```python
   rdbms.execute("""
       CREATE TABLE tasks (
           id INTEGER PRIMARY KEY,
           user_id INTEGER NOT NULL,
           title TEXT NOT NULL,
           description TEXT,
           status TEXT NOT NULL,
           priority INTEGER,
           due_date TEXT  -- New field
       )
   """)
   ```

2. Update the form in `index.html`
3. Update the view logic in `views.py`

### Extending SQL Support

The SQL parser can be extended in `simple_rdbms.py`:
- Add new data types
- Implement ORDER BY, GROUP BY
- Add aggregate functions (COUNT, SUM, AVG)
- Support for multiple JOIN types

## ⚠️ Limitations

This is RDBMS simple application has some limitations:

- **Performance**: Not optimized for large datasets (1000+ rows)
- **Concurrency**: No support for concurrent writes
- **Transactions**: No ACID transaction support
- **Advanced SQL**: Limited SQL feature set
- **Security**: SQL injection vulnerable (used parameter escaping)
- **Scalability**: Single-file storage, not suitable for production

## 🤝 Contributing

Contributions are welcome! Feel free to:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 👨‍💻 Author

**Your Name**
- GitHub: [@hemarastylepeke](https://github.com/hemarastylepeke)
- Email: omollohemstone@gmail.com

## 🙏 Acknowledgments

- Inspired by SQLite's architecture
- Special thanks to the Django and Python communities
- Appreciation to Claude (Anthropic AI) team. Claude Sonnet model was used for debugging and generation of some sections of the code as well as this README.md

## 📚 Resources

- [Database Internals Book](https://www.databass.dev/)
- [SQLite Documentation](https://www.sqlite.org/docs.html)
- [Django Documentation](https://docs.djangoproject.com/)

---

**Note**: This project is just a simple demonstration of how RDBMS actually works behind the scenes. For production applications, use established database systems like PostgreSQL, MySQL, or SQLite in production.