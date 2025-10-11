#!/bin/bash
#
# Install Ollama and Download Llama 3.1 8B Model
# This script must be run with sudo privileges
#

set -e

echo "=========================================="
echo "Ollama Installation & Model Download"
echo "=========================================="
echo ""

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}✗ This script must be run with sudo${NC}"
    echo "Please run: sudo $0"
    exit 1
fi

# Get the actual user (not root)
ACTUAL_USER="${SUDO_USER:-$USER}"
REPO_ROOT="/home/$ACTUAL_USER/course-creator"
MODELS_DIR="$REPO_ROOT/models"

echo "User: $ACTUAL_USER"
echo "Repo root: $REPO_ROOT"
echo "Models directory: $MODELS_DIR"
echo ""

# Step 1: Install Ollama
echo "=========================================="
echo "Step 1: Installing Ollama"
echo "=========================================="
echo ""

if command -v ollama &> /dev/null; then
    echo -e "${GREEN}✓ Ollama is already installed${NC}"
    ollama --version
else
    echo "Installing Ollama..."
    curl -fsSL https://ollama.ai/install.sh | sh

    if command -v ollama &> /dev/null; then
        echo -e "${GREEN}✓ Ollama installed successfully${NC}"
        ollama --version
    else
        echo -e "${RED}✗ Ollama installation failed${NC}"
        exit 1
    fi
fi

echo ""

# Step 2: Configure Ollama to use custom models directory
echo "=========================================="
echo "Step 2: Configuring Ollama Models Directory"
echo "=========================================="
echo ""

# Create models directory if it doesn't exist
if [ ! -d "$MODELS_DIR" ]; then
    mkdir -p "$MODELS_DIR"
    chown -R $ACTUAL_USER:$ACTUAL_USER "$MODELS_DIR"
    echo -e "${GREEN}✓ Created models directory: $MODELS_DIR${NC}"
fi

# Configure Ollama environment
echo "Setting OLLAMA_MODELS environment variable..."

# Create or update environment file
ENV_FILE="/etc/environment"
if grep -q "OLLAMA_MODELS" "$ENV_FILE"; then
    sed -i "s|OLLAMA_MODELS=.*|OLLAMA_MODELS=\"$MODELS_DIR\"|" "$ENV_FILE"
    echo -e "${GREEN}✓ Updated OLLAMA_MODELS in $ENV_FILE${NC}"
else
    echo "OLLAMA_MODELS=\"$MODELS_DIR\"" >> "$ENV_FILE"
    echo -e "${GREEN}✓ Added OLLAMA_MODELS to $ENV_FILE${NC}"
fi

# Also set for systemd service
SYSTEMD_DIR="/etc/systemd/system/ollama.service.d"
if [ ! -d "$SYSTEMD_DIR" ]; then
    mkdir -p "$SYSTEMD_DIR"
fi

cat > "$SYSTEMD_DIR/environment.conf" << EOF
[Service]
Environment="OLLAMA_MODELS=$MODELS_DIR"
EOF

echo -e "${GREEN}✓ Configured Ollama systemd service${NC}"

# Set for current session
export OLLAMA_MODELS="$MODELS_DIR"

echo ""

# Step 3: Start Ollama service
echo "=========================================="
echo "Step 3: Starting Ollama Service"
echo "=========================================="
echo ""

# Check if systemd service exists
if systemctl list-unit-files | grep -q ollama.service; then
    systemctl daemon-reload
    systemctl enable ollama
    systemctl restart ollama

    sleep 3

    if systemctl is-active --quiet ollama; then
        echo -e "${GREEN}✓ Ollama service is running${NC}"
    else
        echo -e "${YELLOW}⚠ Ollama service not active, starting manually...${NC}"
        # Start Ollama manually in background
        su - $ACTUAL_USER -c "OLLAMA_MODELS=$MODELS_DIR ollama serve > /tmp/ollama.log 2>&1 &"
        sleep 5
    fi
else
    echo -e "${YELLOW}⚠ Ollama systemd service not found, starting manually...${NC}"
    # Start Ollama manually in background
    su - $ACTUAL_USER -c "OLLAMA_MODELS=$MODELS_DIR ollama serve > /tmp/ollama.log 2>&1 &"
    sleep 5
fi

# Verify Ollama is running
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Ollama API is responding${NC}"
else
    echo -e "${RED}✗ Ollama API is not responding${NC}"
    echo "Check logs: tail -f /tmp/ollama.log"
    exit 1
fi

echo ""

# Step 4: Download Llama 3.1 8B model
echo "=========================================="
echo "Step 4: Downloading Llama 3.1 8B Model"
echo "=========================================="
echo ""

MODEL_NAME="llama3.1:8b-instruct-q4_K_M"

echo "Downloading $MODEL_NAME (~5GB)..."
echo "This will take several minutes depending on your internet speed..."
echo ""

# Check if model already exists
if su - $ACTUAL_USER -c "OLLAMA_MODELS=$MODELS_DIR ollama list" | grep -q "$MODEL_NAME"; then
    echo -e "${GREEN}✓ Model $MODEL_NAME already downloaded${NC}"
else
    # Download model as the actual user
    su - $ACTUAL_USER -c "OLLAMA_MODELS=$MODELS_DIR ollama pull $MODEL_NAME"

    if su - $ACTUAL_USER -c "OLLAMA_MODELS=$MODELS_DIR ollama list" | grep -q "$MODEL_NAME"; then
        echo -e "${GREEN}✓ Model downloaded successfully${NC}"
    else
        echo -e "${RED}✗ Model download failed${NC}"
        exit 1
    fi
fi

echo ""

# Step 5: Verify installation
echo "=========================================="
echo "Step 5: Verifying Installation"
echo "=========================================="
echo ""

echo "Models directory contents:"
ls -lh "$MODELS_DIR"

echo ""
echo "Downloaded models:"
su - $ACTUAL_USER -c "OLLAMA_MODELS=$MODELS_DIR ollama list"

echo ""
echo "Testing model with a simple query..."
RESPONSE=$(su - $ACTUAL_USER -c "OLLAMA_MODELS=$MODELS_DIR ollama run $MODEL_NAME 'What is 2+2? Answer in one word.' --verbose 2>&1 | head -20")
echo "$RESPONSE"

echo ""

# Step 6: Summary
echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""

echo -e "${GREEN}✓ Ollama installed${NC}"
echo -e "${GREEN}✓ Models directory configured: $MODELS_DIR${NC}"
echo -e "${GREEN}✓ Llama 3.1 8B model downloaded (~5GB)${NC}"
echo -e "${GREEN}✓ Ollama service running${NC}"

echo ""
echo "Model location:"
MODEL_PATH=$(find "$MODELS_DIR" -name "*.bin" -o -name "*.gguf" 2>/dev/null | head -1)
if [ -n "$MODEL_PATH" ]; then
    MODEL_SIZE=$(du -sh "$MODEL_PATH" | cut -f1)
    echo "  $MODEL_PATH ($MODEL_SIZE)"
else
    echo "  $MODELS_DIR (model blobs stored here)"
fi

echo ""
echo "To use Ollama with custom models directory:"
echo "  export OLLAMA_MODELS=$MODELS_DIR"
echo "  ollama list"
echo "  ollama run $MODEL_NAME"

echo ""
echo "To start Local LLM Service:"
echo "  cd $REPO_ROOT/services/local-llm-service"
echo "  export OLLAMA_MODELS=$MODELS_DIR"
echo "  python3 main.py"

echo ""
echo -e "${GREEN}Setup complete!${NC}"
echo ""
