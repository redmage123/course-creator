# LLama 3 Fine-Tuning Guide for Course Creator Platform

**Version**: 1.0
**Last Updated**: 2025-10-14
**Status**: Production Ready

---

## Overview

This guide provides comprehensive instructions for fine-tuning LLama 3 to enhance your Course Creator platform's local LLM capabilities. The fine-tuned model will excel at:

- 🎓 **Course Content Generation** - Creating engaging educational materials
- 💬 **Student Q&A** - Answering student questions accurately
- 💻 **Code Lab Generation** - Generating programming exercises
- 📝 **Quiz Creation** - Creating assessments and test questions
- 🧠 **Concept Explanation** - Breaking down complex topics clearly

---

## Quick Start

```bash
# 1. Prepare training data (~30 minutes)
cd services/local-llm-service
python3 scripts/prepare_training_data.py --output-dir ./training_data

# 2. Configure training (edit config file)
cp configs/training_config.example.yaml configs/my_training.yaml
vim configs/my_training.yaml

# 3. Run fine-tuning (~6-12 hours on single GPU)
python3 scripts/fine_tune_llama3.py --config configs/my_training.yaml

# 4. Deploy fine-tuned model
./scripts/deploy_fine_tuned_model.sh ./models/llama3-course-creator-v1
```

---

## Prerequisites

### Hardware Requirements

**Minimum** (4-bit quantized LoRA):
- GPU: NVIDIA GPU with 16GB+ VRAM (RTX 4090, A100, etc.)
- RAM: 32GB system RAM
- Storage: 100GB free space
- Time: ~12 hours for full training

**Recommended** (faster training):
- GPU: NVIDIA A100 (40GB+) or H100
- RAM: 64GB+ system RAM
- Storage: 250GB+ NVMe SSD
- Time: ~6 hours for full training

### Software Requirements

```bash
# Python 3.10+
python3 --version

# CUDA 11.8+ or 12.1+
nvcc --version

# Install dependencies
pip install -r requirements-training.txt
```

**Key dependencies**:
- `transformers>=4.35.0`
- `datasets>=2.14.0`
- `peft>=0.6.0`
- `bitsandbytes>=0.41.0`
- `accelerate>=0.24.0`
- `trl>=0.7.4`
- `scipy`
- `tensorboard`

---

## Training Data Preparation

### Step 1: Download and Format Datasets

Our preparation script handles everything automatically:

```bash
python3 scripts/prepare_training_data.py --output-dir ./training_data
```

This downloads and formats:
- **OpenAssistant** (40k samples) - Conversational AI
- **Alpaca** (32k samples) - Instruction following
- **CodeAlpaca** (20k samples) - Code generation
- **MMLU** (15k samples) - Multi-domain knowledge
- **ELI5** (25k samples) - Concept explanation

**Total**: ~132k training examples
**Output**: `training_data/combined_training_data.jsonl`

### Step 2: Quick Test (Optional)

For testing the pipeline quickly:

```bash
python3 scripts/prepare_training_data.py --output-dir ./training_data --quick
```

This creates a smaller dataset (~2.5k examples) for rapid testing.

### Step 3: Verify Data

```bash
# Check dataset statistics
cat training_data/dataset_stats.json

# Sample first few lines
head -n 3 training_data/combined_training_data.jsonl | jq .
```

---

## Training Configuration

### Create Config File

```bash
cp configs/training_config.example.yaml configs/course_creator_v1.yaml
```

### Example Configuration

```yaml
# Model Configuration
model_name: "meta-llama/Meta-Llama-3-8B"
output_dir: "./models/llama3-course-creator-v1"
training_data: "./training_data/combined_training_data.jsonl"

# Training Hyperparameters
num_train_epochs: 3
per_device_train_batch_size: 4
gradient_accumulation_steps: 4  # Effective batch size = 4 * 4 = 16
learning_rate: 2e-5
max_seq_length: 2048

# LoRA Configuration (Parameter-Efficient Fine-Tuning)
use_lora: true
lora_r: 16              # Rank - higher = more capacity, slower
lora_alpha: 32          # Scaling factor
lora_dropout: 0.05
lora_target_modules:
  - "q_proj"
  - "v_proj"
  - "k_proj"
  - "o_proj"
  - "gate_proj"
  - "up_proj"
  - "down_proj"

# Quantization (Memory Efficiency)
use_4bit: true
bnb_4bit_compute_dtype: "float16"
bnb_4bit_quant_type: "nf4"

# Logging and Checkpointing
warmup_steps: 100
logging_steps: 10
save_steps: 500
report_to: "tensorboard"
logging_dir: "./logs/llama3-course-creator-v1"
```

### Configuration Options Explained

**Training Hyperparameters**:
- `num_train_epochs`: 3 epochs is standard (1 epoch = full pass through data)
- `learning_rate`: 2e-5 is good for LoRA; 1e-5 for full fine-tuning
- `gradient_accumulation_steps`: Increase if GPU memory is limited
- `max_seq_length`: 2048 balances context and memory usage

**LoRA Settings**:
- `lora_r`: Rank 16-32 is typical; higher = more capacity
- `lora_alpha`: Usually 2x the rank
- `target_modules`: Which layers to fine-tune (more = better, slower)

**Memory Optimization**:
- `use_4bit`: Enables 4-bit quantization (saves ~75% VRAM)
- `use_lora`: Reduces trainable parameters by ~99%
- Together: Can train on consumer GPUs (16-24GB VRAM)

---

## Running Fine-Tuning

### Start Training

```bash
# Activate environment
source .venv/bin/activate

# Run training
python3 scripts/fine_tune_llama3.py --config configs/course_creator_v1.yaml
```

### Monitor Progress

**TensorBoard** (recommended):
```bash
# In separate terminal
tensorboard --logdir ./logs/llama3-course-creator-v1
# Open browser to http://localhost:6006
```

**Console Output**:
```
🚀 Starting LLama 3 Fine-Tuning for Course Creator Platform
================================================================================

📥 Loading tokenizer: meta-llama/Meta-Llama-3-8B
✅ Tokenizer loaded

📥 Loading model: meta-llama/Meta-Llama-3-8B
✅ Model loaded

🔧 Applying LoRA configuration
trainable params: 20,971,520 || all params: 8,030,261,248 || trainable%: 0.2611
✅ LoRA applied

📥 Loading training data: ./training_data/combined_training_data.jsonl
✅ Loaded 132,000 training examples

================================================================================
🏃 Training started...
================================================================================

[Epoch 1/3]  [  100/24750]  loss: 1.234  lr: 1.8e-05  ETA: 6h 23m
[Epoch 1/3]  [  200/24750]  loss: 1.156  lr: 1.9e-05  ETA: 6h 21m
...
```

### Resume from Checkpoint

If training is interrupted:

```bash
python3 scripts/fine_tune_llama3.py \
  --config configs/course_creator_v1.yaml \
  --resume-from-checkpoint ./models/llama3-course-creator-v1/checkpoint-1000
```

---

## Training Time Estimates

| GPU Model | VRAM | Batch Size | Time (3 epochs) | Cost* |
|-----------|------|------------|-----------------|-------|
| RTX 4090 | 24GB | 4 | ~12 hours | $0 (local) |
| A100 (40GB) | 40GB | 8 | ~6 hours | ~$18 (cloud) |
| A100 (80GB) | 80GB | 16 | ~3 hours | ~$18 (cloud) |
| H100 | 80GB | 16 | ~1.5 hours | ~$25 (cloud) |

*Cloud costs based on AWS/GCP hourly rates

---

## Evaluating the Fine-Tuned Model

### Quick Test

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

# Load base model
base_model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Meta-Llama-3-8B",
    device_map="auto"
)

# Load LoRA adapter
model = PeftModel.from_pretrained(
    base_model,
    "./models/llama3-course-creator-v1"
)

# Load tokenizer
tokenizer = AutoTokenizer.from_pretrained("meta-llama/Meta-Llama-3-8B")

# Test prompt
prompt = """<|begin_of_text|><|start_header_id|>user<|end_header_id|>

Explain what a binary search tree is to a beginner programmer.<|eot_id|><|start_header_id|>assistant<|end_header_id|>

"""

inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
outputs = model.generate(**inputs, max_new_tokens=256)
print(tokenizer.decode(outputs[0]))
```

### Benchmark Against Original

```bash
# Run evaluation suite
python3 scripts/evaluate_model.py \
  --base-model meta-llama/Meta-Llama-3-8B \
  --fine-tuned-model ./models/llama3-course-creator-v1 \
  --test-set ./test_data/educational_qa.jsonl
```

---

## Deploying the Fine-Tuned Model

### Option 1: Replace Local LLM Service Model

```bash
# Stop service
docker-compose stop local-llm-service

# Update model path in docker-compose.yml
vim docker-compose.yml

# Change:
# MODEL_PATH: "/models/llama3-8b"
# To:
# MODEL_PATH: "/models/llama3-course-creator-v1"

# Restart service
docker-compose up -d local-llm-service
```

### Option 2: Deploy to HuggingFace Hub

```bash
# Login to HuggingFace
huggingface-cli login

# Push model
python3 scripts/push_to_hub.py \
  --model-path ./models/llama3-course-creator-v1 \
  --repo-name your-org/llama3-course-creator-v1 \
  --private
```

### Option 3: Merge LoRA and Export

```bash
# Merge LoRA weights into base model
python3 scripts/merge_lora.py \
  --base-model meta-llama/Meta-Llama-3-8B \
  --lora-path ./models/llama3-course-creator-v1 \
  --output-path ./models/llama3-course-creator-v1-merged

# This creates a standalone model (larger, but faster inference)
```

---

## Troubleshooting

### Out of Memory (OOM) Errors

**Problem**: `CUDA out of memory` error during training

**Solutions**:
1. Reduce `per_device_train_batch_size` (try 2 or 1)
2. Increase `gradient_accumulation_steps` (to maintain effective batch size)
3. Reduce `max_seq_length` (try 1024 or 512)
4. Enable gradient checkpointing (already enabled in config)
5. Use smaller LoRA rank (try `lora_r: 8`)

### Slow Training

**Problem**: Training is taking too long

**Solutions**:
1. Reduce dataset size (sample fewer examples)
2. Reduce `num_train_epochs` (try 2 or 1)
3. Use larger `per_device_train_batch_size` if memory allows
4. Use FP16 or BF16 instead of FP32 (already enabled)
5. Use cloud GPU (A100/H100)

### Loss Not Decreasing

**Problem**: Training loss stuck or increasing

**Solutions**:
1. Check learning rate (try 1e-5 or 5e-6)
2. Verify data formatting is correct
3. Increase `warmup_steps` (try 500)
4. Check for data quality issues
5. Try different `lora_alpha` values

### Model Outputs Gibberish

**Problem**: Fine-tuned model produces nonsense

**Solutions**:
1. Check if training completed successfully
2. Verify LoRA adapter loaded correctly
3. Ensure chat template matches training format
4. Try lower learning rate and retrain
5. Check for data contamination

---

## Best Practices

### Data Quality
✅ **Do**:
- Use high-quality, diverse datasets
- Filter out low-quality examples
- Balance dataset proportions
- Remove duplicates

❌ **Don't**:
- Include noisy or incorrect data
- Over-represent one domain
- Use outdated information
- Skip data validation

### Training Process
✅ **Do**:
- Start with smaller test run
- Monitor loss curves
- Save checkpoints frequently
- Evaluate at multiple checkpoints
- Document your config

❌ **Don't**:
- Train without validation
- Use same data for train and eval
- Ignore loss curves
- Skip hyperparameter tuning
- Forget to version models

### Deployment
✅ **Do**:
- Test thoroughly before production
- Version your models
- Keep base model for comparison
- Monitor performance in production
- Gather user feedback

❌ **Don't**:
- Deploy without testing
- Overwrite previous versions
- Skip A/B testing
- Ignore production metrics
- Stop monitoring after deployment

---

## Advanced Topics

### Multi-GPU Training

```yaml
# In training_config.yaml, add:
distributed:
  enabled: true
  world_size: 4  # Number of GPUs

# Run with:
torchrun --nproc_per_node=4 scripts/fine_tune_llama3.py --config configs/course_creator_v1.yaml
```

### Custom Dataset Integration

```python
# Add your own dataset to prepare_training_data.py
def download_and_prepare_custom(self, num_samples: int = 10000):
    dataset = load_dataset("your-org/your-dataset", split="train")

    formatted = []
    for example in dataset:
        formatted_example = {
            "prompt": f"<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\n{example['input']}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n",
            "completion": f"{example['output']}<|eot_id|>"
        }
        formatted.append(formatted_example)

    return formatted
```

### Quantization After Training

```bash
# Convert to GGUF format for llama.cpp
python3 scripts/convert_to_gguf.py \
  --model-path ./models/llama3-course-creator-v1-merged \
  --output-path ./models/llama3-course-creator-v1.gguf \
  --quantization Q4_K_M
```

---

## FAQ

**Q: How much does fine-tuning cost?**
A: Local GPU (RTX 4090): Free. Cloud (A100): ~$18-25 for full training.

**Q: Can I use a smaller model?**
A: Yes! LLama 3.1-8B Instruct works great and trains faster.

**Q: How often should I retrain?**
A: Every 3-6 months as new educational content is added.

**Q: Can I fine-tune on my own course data?**
A: Absolutely! Add your course content to the training data.

**Q: Will this work with other models?**
A: Yes, with minor modifications to the chat template.

---

## Support

**Issues**: [GitHub Issues](https://github.com/your-org/course-creator/issues)
**Discussions**: [GitHub Discussions](https://github.com/your-org/course-creator/discussions)
**Email**: support@course-creator.com

---

**Document Version**: 1.0
**Last Updated**: 2025-10-14
**Next Review**: 2025-11-14
