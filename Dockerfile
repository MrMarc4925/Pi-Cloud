FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

RUN pip install flask flask-limiter psutil

COPY . .

EXPOSE 8080

CMD ["python3", "app.py"]
