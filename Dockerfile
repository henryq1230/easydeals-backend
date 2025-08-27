# Usar Python 3.11 como base
FROM python:3.11-slim

# Variables de entorno para optimizar Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Crear directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements.txt e instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el código de la aplicación
COPY . .

# Recopilar archivos estáticos de Django
RUN python manage.py collectstatic --noinput --clear

# Exponer puerto 8080 (que usa Cloud Run)
EXPOSE $PORT

# Comando para ejecutar la aplicación
CMD "exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 easydeals_backend.wsgi:application"