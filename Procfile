release: python manage.py makemigrations && python manage.py migrate
web: gunicorn simple_rdbms_project.wsgi --log-file -