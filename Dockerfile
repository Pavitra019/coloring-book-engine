1. Use a lightweight base Python image
FROM python:3.11-slim

2. Install system dependencies needed for Pillow and fonts.
The '&& ' allows the command to span multiple lines cleanly.
RUN apt-get update && 

apt-get install -y libjpeg-dev zlib1g-dev gcc build-essential fontconfig fonts-dejavu-core && 

rm -rf /var/lib/apt/lists/*

3. Set the working directory inside the container
WORKDIR /app

4. Copy the requirements file and install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

5. Copy the rest of the application files
COPY . .

6. Run the application using the Procfile command
CMD ["/usr/local/bin/gunicorn"]