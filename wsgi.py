# wsgi.py
from app import app  # importa l'oggetto Flask "app" dal file app.py

# Gunicorn cercherà "app" dentro il modulo "wsgi"
# Comando: gunicorn -b 0.0.0.0:$PORT wsgi:app
