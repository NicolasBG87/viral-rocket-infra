FROM python:3.10-slim

WORKDIR /app

# System dependencies
RUN apt update && apt install -y ffmpeg && apt clean

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code
COPY . .

CMD ["python", "run.py"]
