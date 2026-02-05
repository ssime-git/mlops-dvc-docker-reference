FROM python:3.11-slim

# Install git for commit tracking
RUN apt-get update && \
    apt-get install -y git && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY train.py .
COPY dvc_lineage.py .

CMD ["python", "train.py"]
