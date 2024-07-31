FROM python:slim

WORKDIR /app
COPY requirements.lock ./
RUN PYTHONDONTWRITEBYTECODE=1 pip install --no-cache-dir -r requirements.lock

COPY server .
CMD ["fastapi", "run", "app.py", "--port", "80"]