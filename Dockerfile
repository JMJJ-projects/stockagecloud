FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN useradd --create-home appuser && mkdir -p /data/uploads && chown -R appuser /data
USER appuser

ENV DATABASE=/data/database.db \
    UPLOAD_FOLDER=/data/uploads \
    FLASK_ENV=production
VOLUME /data
EXPOSE 8000

# Create the schema on first start, then serve with gunicorn.
CMD ["sh", "-c", "[ -f \"$DATABASE\" ] || flask --app app init-db; exec gunicorn -b 0.0.0.0:8000 -w 2 app:app"]
