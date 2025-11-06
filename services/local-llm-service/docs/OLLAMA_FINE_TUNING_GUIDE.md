# Ollama Fine-Tuning Guide

## Overview

Ollama models use GGUF format optimized for inference. Fine-tuning requires a different approach than HuggingFace transformers.

## Method 1: Create Custom Modelfile (Recommended for Ollama)

### Step 1: Create a Modelfile with System Prompt

```bash
# Create a Modelfile that layers custom instructions on existing model
FROM mistral:7b-instruct

# System prompt for course creation
SYSTEM """
You are an expert educational AI assistant for the Course Creator Platform.

Your responsibilities:
- Generate engaging course content for technical subjects
- Create practical coding exercises and labs
- Design quizzes with clear explanations
- Provide personalized student assistance
- Explain complex concepts in simple terms

When generating content:
1. Use clear, concise language
2. Include real-world examples
3. Provide step-by-step explanations
4. Adapt to student skill level
5. Encourage hands-on practice
"""

# Temperature for creative content generation
PARAMETER temperature 0.7

# Tokens for longer educational responses
PARAMETER num_predict 2048
```

### Step 2: Build the Custom Model

```bash
ollama create course-creator-assistant -f Modelfile
```

### Step 3: Test the Model

```bash
ollama run course-creator-assistant "Create a Python quiz question about list comprehensions"
```

## Method 2: Fine-tune with Unsloth (LoRA)

For true fine-tuning with custom training data, use Unsloth which supports Ollama export:

### Install Unsloth

```bash
pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"
```

### Fine-tune Script

```python
from unsloth import FastLanguageModel
import torch

# Load model
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = "unsloth/mistral-7b-v0.2-bnb-4bit",
    max_seq_length = 2048,
    dtype = None,
    load_in_4bit = True,
)

# Add LoRA adapters
model = FastLanguageModel.get_peft_model(
    model,
    r = 16,
    target_modules = ["q_proj", "k_proj", "v_proj", "o_proj"],
    lora_alpha = 16,
    lora_dropout = 0,
    bias = "none",
    use_gradient_checkpointing = True,
)

# Train (similar to current setup)
trainer = SFTTrainer(
    model = model,
    train_dataset = dataset,
    # ... training args
)

trainer.train()

# Save for Ollama
model.save_pretrained_gguf("course-creator-mistral", tokenizer)
```

### Import to Ollama

```bash
# Create Modelfile pointing to GGUF
cat > Modelfile <<EOF
FROM ./course-creator-mistral-Q4_K_M.gguf
TEMPLATE """{{ .System }}
{{ .Prompt }}"""
PARAMETER temperature 0.7
EOF

# Import
ollama create course-creator-mistral -f Modelfile
```

## Method 3: Export HuggingFace Fine-tuned Model to Ollama

### Step 1: Convert to GGUF

After fine-tuning with current scripts, convert to GGUF:

```bash
# Install llama.cpp
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
make

# Convert model
python convert.py /path/to/fine-tuned/model --outfile model.gguf --outtype q4_k_m
```

### Step 2: Import to Ollama

```bash
cat > Modelfile <<EOF
FROM ./model.gguf
PARAMETER temperature 0.7
EOF

ollama create my-fine-tuned-model -f Modelfile
```

## Recommended Workflow

**For Quick Setup (Method 1):**
1. Use existing Ollama models
2. Add custom system prompts via Modelfile
3. No training required, instant deployment

**For True Fine-tuning (Method 2 or 3):**
1. Use current HuggingFace scripts
2. Convert to GGUF after training completes
3. Import to Ollama for optimized inference

## Available Ollama Models

You currently have:
- mistral:7b-instruct ✅
- qwen2.5:7b-instruct ✅
- deepseek-coder-v2:latest ✅
- codestral:latest ✅
- phi3:mini ✅

All can be customized with Modelfiles!
