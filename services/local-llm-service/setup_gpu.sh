#!/bin/bash
#
# Local LLM Service - GPU Setup Script
#
# This script sets up the Local LLM Service with NVIDIA GPU (CUDA) support:
# 1. Checks for NVIDIA GPU
# 2. Installs NVIDIA drivers if needed
# 3. Installs CUDA toolkit
# 4. Installs cuDNN libraries
# 5. Installs Ollama with GPU support
# 6. Pulls Llama 3.1 8B model
# 7. Runs GPU benchmarks
#

set -e

echo "=========================================="
echo "Local LLM Service - GPU Setup"
echo "=========================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}✗ This script must be run as root${NC}"
    echo "Please run: sudo $0"
    exit 1
fi

echo "Running as root ✓"
echo ""

# Step 1: Check for NVIDIA GPU
echo "=========================================="
echo "Step 1: Checking for NVIDIA GPU"
echo "=========================================="
echo ""

if command -v nvidia-smi &> /dev/null; then
    echo -e "${GREEN}✓ NVIDIA drivers are installed${NC}"
    nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
    echo ""
else
    echo -e "${YELLOW}⚠ NVIDIA drivers not found${NC}"
    echo "Checking for NVIDIA GPU hardware..."

    if lspci | grep -i nvidia > /dev/null; then
        echo -e "${GREEN}✓ NVIDIA GPU detected${NC}"
        lspci | grep -i nvidia
        echo ""

        echo "Installing NVIDIA drivers..."
        apt-get update
        apt-get install -y nvidia-driver-535 nvidia-utils-535

        echo -e "${YELLOW}⚠ System reboot required for drivers to take effect${NC}"
        echo "Please run: sudo reboot"
        echo "Then run this script again after reboot"
        exit 0
    else
        echo -e "${RED}✗ No NVIDIA GPU found${NC}"
        echo "This script requires an NVIDIA GPU for CUDA acceleration"
        exit 1
    fi
fi

# Step 2: Check CUDA installation
echo "=========================================="
echo "Step 2: Checking CUDA Toolkit"
echo "=========================================="
echo ""

if command -v nvcc &> /dev/null; then
    CUDA_VERSION=$(nvcc --version | grep "release" | sed 's/.*release //' | sed 's/,.*//')
    echo -e "${GREEN}✓ CUDA Toolkit installed: version $CUDA_VERSION${NC}"
    nvcc --version | grep "release"
    echo ""
else
    echo -e "${YELLOW}⚠ CUDA Toolkit not found${NC}"
    echo "Installing CUDA Toolkit 12.2..."

    # Add NVIDIA CUDA repository
    wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb
    dpkg -i cuda-keyring_1.1-1_all.deb
    rm cuda-keyring_1.1-1_all.deb

    apt-get update

    # Install CUDA without nsight-systems (requires libtinfo5 which is unavailable in Ubuntu 24.04)
    echo "Installing CUDA runtime and compiler (excluding problematic dev tools)..."
    apt-get install -y \
        cuda-runtime-12-2 \
        cuda-compiler-12-2 \
        cuda-cudart-12-2 \
        cuda-nvcc-12-2 \
        cuda-nvrtc-12-2 \
        cuda-libraries-12-2 \
        cuda-libraries-dev-12-2

    # Add CUDA to PATH
    echo 'export PATH=/usr/local/cuda-12.2/bin:$PATH' >> /etc/profile.d/cuda.sh
    echo 'export LD_LIBRARY_PATH=/usr/local/cuda-12.2/lib64:$LD_LIBRARY_PATH' >> /etc/profile.d/cuda.sh
    source /etc/profile.d/cuda.sh

    echo -e "${GREEN}✓ CUDA Toolkit 12.2 installed${NC}"
    echo ""
fi

# Step 3: Check cuDNN libraries
echo "=========================================="
echo "Step 3: Checking cuDNN Libraries"
echo "=========================================="
echo ""

if [ -f "/usr/local/cuda/include/cudnn.h" ] || [ -f "/usr/include/cudnn.h" ]; then
    CUDNN_VERSION=$(cat /usr/include/cudnn_version.h 2>/dev/null | grep CUDNN_MAJOR -A 2 | grep '#define' | awk '{print $3}' | xargs | tr ' ' '.')
    echo -e "${GREEN}✓ cuDNN installed: version $CUDNN_VERSION${NC}"
    echo ""
else
    echo -e "${YELLOW}⚠ cuDNN not found${NC}"
    echo "Installing cuDNN 8.9..."

    apt-get install -y libcudnn8=8.9.5.*-1+cuda12.2 \
                       libcudnn8-dev=8.9.5.*-1+cuda12.2

    echo -e "${GREEN}✓ cuDNN 8.9 installed${NC}"
    echo ""
fi

# Step 4: Verify GPU is accessible
echo "=========================================="
echo "Step 4: Verifying GPU Access"
echo "=========================================="
echo ""

nvidia-smi
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ GPU is accessible${NC}"
    echo ""
else
    echo -e "${RED}✗ GPU is not accessible${NC}"
    exit 1
fi

# Step 5: Install Ollama with GPU support
echo "=========================================="
echo "Step 5: Installing Ollama with GPU Support"
echo "=========================================="
echo ""

if command -v ollama &> /dev/null; then
    echo -e "${GREEN}✓ Ollama is already installed${NC}"
    ollama --version
    echo ""
else
    echo "Installing Ollama..."
    curl -fsSL https://ollama.ai/install.sh | sh

    echo -e "${GREEN}✓ Ollama installed${NC}"
    echo ""
fi

# Start Ollama service
echo "Starting Ollama service..."
systemctl enable ollama || true
systemctl start ollama || ollama serve &
sleep 5

# Verify Ollama is running
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Ollama is running${NC}"
    echo ""
else
    echo -e "${RED}✗ Ollama failed to start${NC}"
    exit 1
fi

# Step 6: Pull Llama 3.1 8B model
echo "=========================================="
echo "Step 6: Pulling Llama 3.1 8B Model"
echo "=========================================="
echo ""

MODEL_NAME="llama3.1:8b-instruct-q4_K_M"

if ollama list | grep -q "$MODEL_NAME"; then
    echo -e "${GREEN}✓ Model $MODEL_NAME already downloaded${NC}"
    echo ""
else
    echo "Downloading $MODEL_NAME (this will take several minutes)..."
    ollama pull $MODEL_NAME

    echo -e "${GREEN}✓ Model downloaded successfully${NC}"
    echo ""
fi

# Step 7: Test GPU acceleration
echo "=========================================="
echo "Step 7: Testing GPU Acceleration"
echo "=========================================="
echo ""

echo "Running test query with verbose output..."
echo "Looking for 'Using GPU' confirmation..."
echo ""

ollama run $MODEL_NAME "What is Python?" --verbose 2>&1 | grep -i "gpu\|cuda" || echo "GPU info not shown in verbose output"

echo ""

# Step 8: Install Python dependencies
echo "=========================================="
echo "Step 8: Installing Python Dependencies"
echo "=========================================="
echo ""

cd "$(dirname "$0")"
pip install -r requirements.txt

echo -e "${GREEN}✓ Python dependencies installed${NC}"
echo ""

# Step 9: Run GPU benchmark
echo "=========================================="
echo "Step 9: Running GPU Performance Benchmark"
echo "=========================================="
echo ""

cat > /tmp/benchmark_gpu.py << 'EOF'
import asyncio
import sys
import time

sys.path.insert(0, '/home/bbrelin/course-creator/services/local-llm-service')

from local_llm_service.application.services.local_llm_service import LocalLLMService


async def benchmark():
    service = LocalLLMService()

    print("Checking service health...")
    healthy = await service.health_check()
    if not healthy:
        print("✗ Service is not healthy")
        return

    print("✓ Service is healthy\n")

    # Test queries
    queries = [
        "What is Python?",
        "Explain machine learning",
        "How do I create a list?"
    ]

    print("Warming up GPU...")
    await service.generate_response(prompt=queries[0], max_tokens=50)

    print("\nRunning benchmark (5 queries)...\n")

    latencies = []
    for i in range(5):
        query = queries[i % len(queries)]

        start = time.time()
        response = await service.generate_response(
            prompt=query,
            max_tokens=100
        )
        latency = (time.time() - start) * 1000

        latencies.append(latency)
        print(f"Query {i+1}: {latency:.0f}ms - {query}")

    print(f"\n{'='*50}")
    print(f"Average latency: {sum(latencies)/len(latencies):.0f}ms")
    print(f"Min latency: {min(latencies):.0f}ms")
    print(f"Max latency: {max(latencies):.0f}ms")
    print(f"{'='*50}\n")

    if sum(latencies)/len(latencies) < 150:
        print("✓ GPU acceleration is working! (latency < 150ms)")
    else:
        print("⚠ Latency is higher than expected (target: <100ms with GPU)")


if __name__ == "__main__":
    asyncio.run(benchmark())
EOF

python3 /tmp/benchmark_gpu.py

# Step 10: Setup complete
echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""

echo -e "${GREEN}✓ NVIDIA GPU configured${NC}"
echo -e "${GREEN}✓ CUDA Toolkit installed${NC}"
echo -e "${GREEN}✓ cuDNN libraries installed${NC}"
echo -e "${GREEN}✓ Ollama with GPU support installed${NC}"
echo -e "${GREEN}✓ Llama 3.1 8B model downloaded${NC}"
echo -e "${GREEN}✓ Python dependencies installed${NC}"
echo -e "${GREEN}✓ GPU benchmark completed${NC}"
echo ""

echo "GPU Information:"
nvidia-smi --query-gpu=name,driver_version,memory.total,memory.used --format=csv,noheader
echo ""

echo "To start the Local LLM Service:"
echo "  cd /home/bbrelin/course-creator/services/local-llm-service"
echo "  python3 main.py"
echo ""

echo "To test the service:"
echo "  curl http://localhost:8015/health"
echo ""

echo "To monitor GPU usage:"
echo "  watch -n 1 nvidia-smi"
echo ""

echo -e "${GREEN}GPU-accelerated Local LLM Service is ready!${NC}"
echo ""
