FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Flask es WSGI, no ASGI: se sirve con gunicorn (no con uvicorn).
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "run:app"]
