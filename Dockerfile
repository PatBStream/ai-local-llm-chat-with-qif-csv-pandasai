# chat-qif-csv-agent/Dockerfile
FROM python:3.11-slim

# 1️⃣ Install system build tools & math libraries
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    libssl-dev \
    pkg-config \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 2️⃣ Set workdir & copy your pinned dependencies
WORKDIR /app
COPY app/requirements.txt .

# 3️⃣ Upgrade packaging tools, then install everything
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --only-binary=numpy "numpy>=1.24.0,<2.0.0" && \
    pip install --no-cache-dir --only-binary=pandas "pandas>=2.1.0" && \
    pip install --no-cache-dir --prefer-binary -r requirements.txt

# 4️⃣ Copy your app code
COPY app/ .

# 5️⃣ Expose port & launch Uvicorn
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
