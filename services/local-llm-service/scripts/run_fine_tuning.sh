#!/bin/bash
# Simple Fine-Tuning Script for Course Creator Platform
# Uses Mistral 7B (no authentication required)

set -e

echo "=================================="
echo "Starting LLM Fine-Tuning"
echo "=================================="
echo ""

# Check if training data exists
if [ ! -f "training_data/quick_training_data.jsonl" ]; then
    echo "❌ Training data not found!"
    echo "Run: python3 scripts/prepare_training_data.py --output-dir ./training_data --quick"
    exit 1
fi

echo "✅ Training data found ($(wc -l < training_data/quick_training_data.jsonl) examples)"
echo ""

# Check GPU
if ! nvidia-smi &> /dev/null; then
    echo "⚠️  Warning: nvidia-smi not found. Training will be slow without GPU."
else
    echo "✅ GPU detected: $(nvidia-smi --query-gpu=name --format=csv,noheader | head -1)"
fi
echo ""

# Start fine-tuning with Mistral (no auth required)
echo "🚀 Starting fine-tuning..."
echo "   Model: mistralai/Mistral-7B-v0.1"
echo "   Config: configs/mistral_training_config.yaml"
echo "   Monitor: tensorboard --logdir logs/mistral-course-creator-quick"
echo ""

python3 scripts/fine_tune_llama3.py --config configs/mistral_training_config.yaml

echo ""
echo "=================================="
echo "✅ Fine-tuning complete!"
echo "=================================="
echo ""
echo "Fine-tuned model saved to: models/mistral-course-creator-quick"
echo ""
echo "Next steps:"
echo "1. Test the model: python3 scripts/test_fine_tuned_model.py"
echo "2. Deploy to Ollama: ./scripts/deploy_to_ollama.sh"
