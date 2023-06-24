FROM python:3.11.3-slim-buster

# Select working directory
WORKDIR /code

# Copy requirements.txt to working directory
COPY requirements.txt requirements.txt

# Install dependencies
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy source code to working directory
COPY main.py main.py

# Create data directory
RUN mkdir -p /data/logs

# Run the application
CMD ["python", "main.py"]
