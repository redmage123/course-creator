# HuggingFace Authentication Guide for LLM Fine-Tuning

**Version**: 1.0
**Last Updated**: 2025-10-14
**Status**: Required for LLama 3 Models

---

## Issue: Gated Model Access

The LLama 3 model from Meta is a **gated repository** on HuggingFace, which requires authentication and access approval before you can download and use it.

**Error you'll see**:
```
OSError: You are trying to access a gated repo.
Make sure to have access to it at https://huggingface.co/meta-llama/Meta-Llama-3-8B.
Access to model meta-llama/Meta-Llama-3-8B is restricted.
```

---

## Solution 1: Authenticate with HuggingFace (Recommended for LLama 3)

### Step 1: Create HuggingFace Account
1. Go to https://huggingface.co/join
2. Create a free account
3. Verify your email address

### Step 2: Request Access to LLama 3
1. Visit https://huggingface.co/meta-llama/Meta-Llama-3-8B
2. Click "Request Access" button
3. Fill out the access request form
4. Wait for approval (usually within a few hours to 1 day)

### Step 3: Generate Access Token
1. Go to https://huggingface.co/settings/tokens
2. Click "New token"
3. Name it "course-creator-llm-training"
4. Select scope: **Read** (sufficient for downloading models)
5. Click "Generate token"
6. Copy the token (starts with `hf_...`)

### Step 4: Authenticate on Your System
```bash
# Option A: Using huggingface-cli (recommended)
huggingface-cli login
# Paste your token when prompted

# Option B: Set environment variable
export HUGGING_FACE_HUB_TOKEN="hf_your_token_here"

# Option C: Save token to file
mkdir -p ~/.huggingface
echo "hf_your_token_here" > ~/.huggingface/token
```

### Step 5: Verify Authentication
```bash
python3 -c "from huggingface_hub import whoami; print(whoami())"
# Should display your HuggingFace username and details
```

### Step 6: Resume Training
```bash
cd services/local-llm-service
python3 scripts/fine_tune_llama3.py --config configs/quick_training_config.yaml
```

---

## Solution 2: Use Alternative Models (No Authentication Required)

If you prefer to avoid authentication, here are excellent alternative models:

### Option A: Mistral 7B (Recommended Alternative)
**Advantages**:
- No authentication required
- Excellent performance
- Similar size to LLama 3 8B
- Strong instruction following

**Configuration**:
```yaml
# configs/mistral_training_config.yaml
model_name: "mistralai/Mistral-7B-v0.1"
output_dir: "./models/mistral-course-creator-quick"
training_data: "./training_data/quick_training_data.jsonl"

# Rest of config same as LLama 3
num_train_epochs: 1
per_device_train_batch_size: 2
# ... (same as quick_training_config.yaml)
```

**Usage**:
```bash
python3 scripts/fine_tune_llama3.py --config configs/mistral_training_config.yaml
```

### Option B: Phi-2 (Smaller, Faster)
**Advantages**:
- No authentication required
- Smaller model (2.7B parameters) - faster training
- Lower VRAM requirements (can run on 8GB GPU)
- Good for testing and quick iterations

**Configuration**:
```yaml
# configs/phi2_training_config.yaml
model_name: "microsoft/phi-2"
output_dir: "./models/phi2-course-creator-quick"
training_data: "./training_data/quick_training_data.jsonl"

# Adjusted for smaller model
num_train_epochs: 2
per_device_train_batch_size: 4
gradient_accumulation_steps: 2
learning_rate: 2e-5
max_seq_length: 1024

# LoRA settings (adjusted for smaller model)
use_lora: true
lora_r: 8
lora_alpha: 16
lora_dropout: 0.05
lora_target_modules:
  - "q_proj"
  - "v_proj"
  - "k_proj"
  - "o_proj"

# Quantization
use_4bit: true
bnb_4bit_compute_dtype: "float16"
bnb_4bit_quant_type: "nf4"

# Logging
warmup_steps: 50
logging_steps: 10
save_steps: 200
report_to: "tensorboard"
logging_dir: "./logs/phi2-course-creator-quick"
```

**Usage**:
```bash
python3 scripts/fine_tune_llama3.py --config configs/phi2_training_config.yaml
```

### Option C: Falcon 7B
**Advantages**:
- No authentication required
- Strong open-source model
- Good balance of size and performance

**Configuration**:
```yaml
# configs/falcon_training_config.yaml
model_name: "tiiuae/falcon-7b"
output_dir: "./models/falcon-course-creator-quick"
training_data: "./training_data/quick_training_data.jsonl"

# Same settings as Mistral
num_train_epochs: 1
per_device_train_batch_size: 2
# ... (same as quick_training_config.yaml)
```

---

## Solution 3: Use Pre-Downloaded Models

If you have the LLama 3 model already downloaded locally:

```yaml
# configs/local_model_config.yaml
model_name: "/path/to/local/llama3-8b"  # Point to local directory
output_dir: "./models/llama3-course-creator-quick"
training_data: "./training_data/quick_training_data.jsonl"
# ... rest of config
```

---

## Model Comparison

| Model | Size | Auth Required | VRAM | Training Time* | Quality |
|-------|------|---------------|------|----------------|---------|
| LLama 3 8B | 8B | ✅ Yes | 16GB+ | ~6-8 hours | ⭐⭐⭐⭐⭐ |
| Mistral 7B | 7B | ❌ No | 14GB+ | ~5-7 hours | ⭐⭐⭐⭐⭐ |
| Phi-2 | 2.7B | ❌ No | 8GB+ | ~2-3 hours | ⭐⭐⭐⭐ |
| Falcon 7B | 7B | ❌ No | 14GB+ | ~5-7 hours | ⭐⭐⭐⭐ |

*Training time for quick mode (2500 examples, 1 epoch) on RTX 4090/A100

---

## Recommendation

**For production use**: Use LLama 3 8B (authenticate with HuggingFace) - highest quality results

**For quick testing**: Use Phi-2 (no auth, trains faster) - verify pipeline works

**For no-auth production**: Use Mistral 7B (no auth, excellent quality) - best alternative to LLama 3

---

## Creating Alternative Model Configs

To create a config for any alternative model:

```bash
# Copy the quick config
cp configs/quick_training_config.yaml configs/my_model_config.yaml

# Edit the model_name and output_dir
vim configs/my_model_config.yaml

# Change:
# model_name: "meta-llama/Meta-Llama-3-8B"
# To:
# model_name: "mistralai/Mistral-7B-v0.1"
#
# And:
# output_dir: "./models/llama3-course-creator-quick"
# To:
# output_dir: "./models/mistral-course-creator-quick"
```

---

## Troubleshooting

### Issue: "Token not found" after login
```bash
# Solution: Verify token is saved
cat ~/.huggingface/token

# If empty, login again
huggingface-cli login --token YOUR_TOKEN
```

### Issue: "Access still denied" after approval
```bash
# Solution: Wait a few hours for approval to propagate
# Or try logging out and back in
huggingface-cli logout
huggingface-cli login
```

### Issue: Alternative model not working
```bash
# Solution: Verify model exists on HuggingFace
python3 -c "from transformers import AutoConfig; AutoConfig.from_pretrained('mistralai/Mistral-7B-v0.1')"
```

---

## Next Steps

Once authenticated (or using an alternative model):

1. **Verify authentication** (if using LLama 3)
2. **Run training** with your chosen config
3. **Monitor progress** with TensorBoard
4. **Deploy fine-tuned model** to local-llm-service

See [LLM_FINE_TUNING_GUIDE.md](LLM_FINE_TUNING_GUIDE.md) for detailed training instructions.

---

**Document Version**: 1.0
**Last Updated**: 2025-10-14
**Next Review**: 2025-11-14
