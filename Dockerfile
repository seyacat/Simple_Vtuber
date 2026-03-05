# TensorFlow GPU Dockerfile for fast training
FROM tensorflow/tensorflow:latest-gpu

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-dev \
    wget \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install Python dependencies
RUN pip3 install --upgrade pip
COPY requirements.txt .
RUN pip3 install -r requirements.txt

# Copy application files
COPY . .

# Create directory for TensorBoard logs
RUN mkdir -p /app/logs/tensorboard

# Set environment variables for optimal performance
ENV TF_FORCE_GPU_ALLOW_GROWTH=true
ENV TF_CPP_MIN_LOG_LEVEL=3
ENV CUDA_VISIBLE_DEVICES=0

# Default command (can be overridden)
CMD ["python3", "train_tensorflow_gpu.py"]