#!/bin/bash
# Setup script for Docker TensorFlow training

echo "========================================="
echo "Docker TensorFlow Training Setup"
echo "========================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed"
    echo "Please install Docker from: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Warning: docker-compose not found, trying docker compose..."
    if ! docker compose version &> /dev/null; then
        echo "Error: Docker Compose is not installed"
        echo "Please install Docker Compose from: https://docs.docker.com/compose/install/"
        exit 1
    fi
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

echo "✓ Docker and Docker Compose are installed"

# Check for NVIDIA GPU if using GPU version
if [[ "$1" == "--gpu" ]]; then
    echo "Checking for NVIDIA GPU..."
    if ! command -v nvidia-smi &> /dev/null; then
        echo "Warning: nvidia-smi not found. GPU acceleration may not be available."
        echo "Continuing with CPU-only setup..."
        GPU_AVAILABLE=false
    else
        echo "✓ NVIDIA GPU detected"
        GPU_AVAILABLE=true
        
        # Check NVIDIA Container Toolkit
        if ! docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi &> /dev/null; then
            echo "Warning: NVIDIA Container Toolkit may not be properly installed"
            echo "GPU acceleration in Docker may not work"
            echo "Install from: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html"
        else
            echo "✓ NVIDIA Container Toolkit is working"
        fi
    fi
fi

# Build Docker image
echo ""
echo "Building Docker image..."
$DOCKER_COMPOSE build

if [ $? -eq 0 ]; then
    echo "✓ Docker image built successfully"
else
    echo "✗ Docker build failed"
    exit 1
fi

# Convert features to numpy format for faster loading
echo ""
echo "Converting features to optimized format..."
python3 convert_to_numpy.py

if [ $? -eq 0 ]; then
    echo "✓ Features converted successfully"
else
    echo "Warning: Feature conversion failed, but continuing..."
fi

# Create necessary directories
echo ""
echo "Creating directories..."
mkdir -p logs/tensorboard/fast_gpu
mkdir -p trained_python_fast
mkdir -p trained_experiments

echo "✓ Directories created"

# Test Docker setup
echo ""
echo "Testing Docker setup..."
if [[ "$GPU_AVAILABLE" == "true" && "$1" == "--gpu" ]]; then
    echo "Testing GPU acceleration..."
    docker run --rm --gpus all tensorflow/tensorflow:latest-gpu python3 -c "import tensorflow as tf; print('TensorFlow version:', tf.__version__); print('GPU available:', tf.config.list_physical_devices('GPU'))"
else
    echo "Testing CPU setup..."
    docker run --rm tensorflow/tensorflow:latest python3 -c "import tensorflow as tf; print('TensorFlow version:', tf.__version__)"
fi

echo ""
echo "========================================="
echo "SETUP COMPLETE"
echo "========================================="
echo ""
echo "Available commands:"
echo ""
echo "1. Fast GPU training (recommended):"
echo "   $DOCKER_COMPOSE up tensorflow-gpu"
echo ""
echo "2. Fast CPU training:"
echo "   $DOCKER_COMPOSE up tensorflow-cpu"
echo ""
echo "3. Run batch experiments:"
echo "   python3 batch_train.py --parallel 2"
echo ""
echo "4. Start TensorBoard:"
echo "   $DOCKER_COMPOSE up tensorboard"
echo "   Then open: http://localhost:6006"
echo ""
echo "5. Quick test training:"
echo "   docker run --gpus all -v \$(pwd):/app simple-vtuber-tensorflow-gpu python3 train_tensorflow_gpu.py --fast"
echo ""
echo "For maximum speed, use GPU training with:"
echo "  $DOCKER_COMPOSE up tensorflow-gpu"
echo ""
echo "Check logs in: logs/tensorboard/fast_gpu"
echo "Models saved in: trained_python_fast/"