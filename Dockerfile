FROM python:3.11-slim
RUN apt-get update && 

apt-get install -y libjpeg-dev zlib1g-dev gcc build-essential fontconfig fonts-dejavu-core && 

rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["/usr/local/bin/gunicorn"]