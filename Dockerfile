FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04

WORKDIR /app

# Install system dependencies
RUN apt update && apt install -y ffmpeg git python3 python3-pip && apt clean

# Install Python packages
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# App code
COPY . .

CMD ["python3", "run.py"]
