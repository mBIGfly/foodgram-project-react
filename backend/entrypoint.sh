python manage.py collectstatic --noinput
gunicorn foodgram.wsgi:application --bind 0:8000