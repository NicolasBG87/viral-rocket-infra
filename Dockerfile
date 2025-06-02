FROM nvidia/cuda:12.3.2-cudnn9-runtime-ubuntu22.04

WORKDIR /app

# Switch to a reliable mirror & ensure all apt components are enabled
RUN sed -i 's|http://archive.ubuntu.com|http://mirror.kakao.com|g' /etc/apt/sources.list && \
    apt update && \
    apt install -y software-properties-common && \
    add-apt-repository universe && \
    add-apt-repository multiverse && \
    apt update && \
    apt install -y python3 python3-pip git ffmpeg && \
    apt clean && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python3", "run.py"]