FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    libcurl4 curl gcc libssl-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py fetchers.py db.py ./

EXPOSE 10000

CMD ["python", "app.py"]
