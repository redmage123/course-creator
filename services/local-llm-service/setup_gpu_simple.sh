#!/bin/bash
#
# Local LLM Service - Simplified GPU Setup Script
#
# This script sets up GPU acceleration for Ollama WITHOUT installing CUDA toolkit
# (Ollama includes its own CUDA runtime libraries)
#

set -e

echo "=========================================="
echo "Local LLM Service - GPU Setup (Simplified)"
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
    if nvidia-smi &> /dev/null; then
        echo -e "${GREEN}✓ NVIDIA drivers are working${NC}"
        nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
        echo ""
    else
        echo -e "${RED}✗ NVIDIA drivers installed but not working${NC}"
        echo "This usually means kernel modules are not loaded"
        echo "Please reboot and try again"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠ NVIDIA drivers not found${NC}"
    echo "Checking for NVIDIA GPU hardware..."

    if lspci | grep -i nvidia > /dev/null; then
        echo -e "${GREEN}✓ NVIDIA GPU detected${NC}"
        lspci | grep -i nvidia
        echo ""

        echo "Installing NVIDIA drivers (570)..."
        apt-get update
        apt-get install -y nvidia-driver-570-server

        echo ""
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

# Step 2: Verify GPU is accessible
echo "=========================================="
echo "Step 2: Verifying GPU Access"
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

# Step 3: Check Ollama installation
echo "=========================================="
echo "Step 3: Checking Ollama Installation"
echo "=========================================="
echo ""

if command -v ollama &> /dev/null; then
    echo -e "${GREEN}✓ Ollama is already installed${NC}"
    ollama --version
    echo ""
else
    echo -e "${YELLOW}⚠ Ollama not found${NC}"
    echo "Please run the install_ollama_and_models.sh script first"
    exit 1
fi

# Step 4: Start Ollama service
echo "=========================================="
echo "Step 4: Starting Ollama Service"
echo "=========================================="
echo ""

echo "Starting Ollama service..."
systemctl enable ollama 2>/dev/null || true
systemctl restart ollama 2>/dev/null || (killall ollama 2>/dev/null; ollama serve > /tmp/ollama.log 2>&1 &)
sleep 5

# Verify Ollama is running
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Ollama is running${NC}"
    echo ""
else
    echo -e "${RED}✗ Ollama failed to start${NC}"
    echo "Check logs: tail -f /tmp/ollama.log"
    exit 1
fi

# Step 5: Verify model is downloaded
echo "=========================================="
echo "Step 5: Checking Llama 3.1 8B Model"
echo "=========================================="
echo ""

MODEL_NAME="llama3.1:8b-instruct-q4_K_M"

if ollama list | grep -q "llama3.1" || ollama list | grep -q "llama3"; then
    echo -e "${GREEN}✓ Llama model is downloaded${NC}"
    ollama list
    echo ""
else
    echo -e "${YELLOW}⚠ Model not found, downloading...${NC}"
    ollama pull $MODEL_NAME
    echo -e "${GREEN}✓ Model downloaded${NC}"
    echo ""
fi

# Step 6: Test GPU acceleration
echo "=========================================="
echo "Step 6: Testing GPU Acceleration"
echo "=========================================="
echo ""

echo "Running test query to verify GPU is being used..."
echo ""

# Run a simple test and check for GPU usage
TEST_OUTPUT=$(ollama run $MODEL_NAME "Say 'GPU test successful'" 2>&1)
echo "$TEST_OUTPUT"
echo ""

# Monitor GPU usage during inference
echo "Checking GPU memory usage (should show model loaded)..."
nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader
echo ""

# Step 7: Run performance benchmark
echo "=========================================="
echo "Step 7: Running Performance Benchmark"
echo "=========================================="
echo ""

ACTUAL_USER="${SUDO_USER:-$USER}"
REPO_ROOT="/home/$ACTUAL_USER/course-creator"

cat > /tmp/benchmark_gpu.py << 'EOFPY'
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
        print("  Note: First run may be slower, try running benchmark again")


if __name__ == "__main__":
    asyncio.run(benchmark())
EOFPY

echo "Checking Python dependencies..."
cd "$REPO_ROOT/services/local-llm-service"

# Check if dependencies are already installed
if python3 -c "import ollama" 2>/dev/null; then
    echo -e "${GREEN}✓ Python dependencies already installed${NC}"
else
    echo "Installing Python dependencies in user space..."
    su - $ACTUAL_USER -c "cd $REPO_ROOT/services/local-llm-service && pip install --user -q -r requirements.txt"
fi

echo "Running benchmark..."
echo ""
su - $ACTUAL_USER -c "python3 /tmp/benchmark_gpu.py"

# Step 8: Setup complete
echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""

echo -e "${GREEN}✓ NVIDIA GPU configured${NC}"
echo -e "${GREEN}✓ Ollama with GPU support running${NC}"
echo -e "${GREEN}✓ Llama 3.1 8B model ready${NC}"
echo -e "${GREEN}✓ Performance benchmark completed${NC}"
echo ""

echo "GPU Information:"
nvidia-smi --query-gpu=name,driver_version,memory.total,memory.used --format=csv,noheader
echo ""

echo "To start the Local LLM Service:"
echo "  cd $REPO_ROOT/services/local-llm-service"
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
echo "Note: Ollama includes its own CUDA runtime libraries,"
echo "      so no separate CUDA toolkit installation is needed."
echo ""
