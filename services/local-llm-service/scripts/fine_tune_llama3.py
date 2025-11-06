#!/usr/bin/env python3
"""
LLama 3 Fine-Tuning Script for Course Creator Platform

BUSINESS CONTEXT:
Fine-tunes LLama 3 on educational datasets to improve:
- Course content generation
- Student Q&A assistance
- Code lab generation
- Quiz creation
- Concept explanation

TECHNICAL IMPLEMENTATION:
- Uses LoRA (Low-Rank Adaptation) for parameter-efficient fine-tuning
- 4-bit quantization for reduced memory usage
- Supports both single-GPU and multi-GPU training
- Integrated with HuggingFace Transformers and PEFT

USAGE:
    python3 fine_tune_llama3.py --config training_config.yaml
"""

import os
import sys
import yaml
import argparse
import torch
from pathlib import Path
from typing import Dict, Any
from dataclasses import dataclass, field

from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from peft import (
    LoraConfig,
    get_peft_model,
    prepare_model_for_kbit_training,
    TaskType
)
from trl import SFTTrainer


@dataclass
class FineTuningConfig:
    """Configuration for fine-tuning"""
    model_name: str
    output_dir: str
    training_data: str
    num_train_epochs: int = 3
    per_device_train_batch_size: int = 4
    gradient_accumulation_steps: int = 4
    learning_rate: float = 2e-5
    max_seq_length: int = 2048
    warmup_steps: int = 100
    logging_steps: int = 10
    save_steps: int = 500
    use_lora: bool = True
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    lora_target_modules: list = field(default_factory=lambda: ["q_proj", "v_proj"])
    use_4bit: bool = True
    bnb_4bit_compute_dtype: str = "float16"
    bnb_4bit_quant_type: str = "nf4"
    report_to: str = "tensorboard"
    logging_dir: str = "./logs"


class LLama3FineTuner:
    """
    Fine-tunes LLama 3 for educational content generation
    """

    def __init__(self, config: FineTuningConfig):
        self.config = config
        self.model = None
        self.tokenizer = None

    def load_tokenizer(self):
        """Load tokenizer from local cache only (no downloads)"""
        print(f"📥 Loading tokenizer: {self.config.model_name}")
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.config.model_name,
            trust_remote_code=True,
            local_files_only=True  # Use cached files only, no downloads
        )

        # Add pad token if missing
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
            self.tokenizer.pad_token_id = self.tokenizer.eos_token_id

        print("✅ Tokenizer loaded")

    def load_model(self):
        """Load model with optional quantization"""
        print(f"📥 Loading model: {self.config.model_name}")

        # Configure quantization
        if self.config.use_4bit:
            compute_dtype = getattr(torch, self.config.bnb_4bit_compute_dtype)

            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type=self.config.bnb_4bit_quant_type,
                bnb_4bit_compute_dtype=compute_dtype,
                bnb_4bit_use_double_quant=True,
            )

            self.model = AutoModelForCausalLM.from_pretrained(
                self.config.model_name,
                quantization_config=bnb_config,
                device_map="auto",
                trust_remote_code=True,
                local_files_only=True,  # Use cached files only, no downloads
            )
        else:
            self.model = AutoModelForCausalLM.from_pretrained(
                self.config.model_name,
                device_map="auto",
                trust_remote_code=True,
                torch_dtype=torch.float16,
                local_files_only=True,  # Use cached files only, no downloads
            )

        # Prepare model for training
        if self.config.use_4bit:
            self.model = prepare_model_for_kbit_training(self.model)

        self.model.config.use_cache = False
        self.model.config.pretraining_tp = 1

        print("✅ Model loaded")

    def apply_lora(self):
        """Apply LoRA for parameter-efficient fine-tuning"""
        if not self.config.use_lora:
            print("ℹ️  Skipping LoRA (full fine-tuning)")
            return

        print("🔧 Applying LoRA configuration")

        lora_config = LoraConfig(
            r=self.config.lora_r,
            lora_alpha=self.config.lora_alpha,
            target_modules=self.config.lora_target_modules,
            lora_dropout=self.config.lora_dropout,
            bias="none",
            task_type=TaskType.CAUSAL_LM,
        )

        self.model = get_peft_model(self.model, lora_config)
        self.model.print_trainable_parameters()

        print("✅ LoRA applied")

    def load_training_data(self):
        """Load and prepare training data"""
        print(f"📥 Loading training data: {self.config.training_data}")

        dataset = load_dataset('json', data_files=self.config.training_data, split='train')

        print(f"✅ Loaded {len(dataset)} training examples")
        return dataset

    def format_data_for_training(self, dataset):
        """
        Format dataset for SFTTrainer (TRL 0.23.x API)

        Pre-format the dataset by adding a 'text' column.
        This avoids conflicts with completion_only_loss parameter.
        """
        print("🔧 Formatting dataset...")

        def format_example(example):
            """Format example for training (combines prompt + completion)"""
            return {'text': example['prompt'] + example['completion']}

        formatted_dataset = dataset.map(format_example, remove_columns=dataset.column_names)

        print("✅ Dataset formatted")
        return formatted_dataset

    def train(self):
        """Run fine-tuning"""
        print()
        print("=" * 80)
        print("🚀 Starting LLama 3 Fine-Tuning for Course Creator Platform")
        print("=" * 80)
        print()

        # Load components
        self.load_tokenizer()
        self.load_model()
        self.apply_lora()

        # Load and prepare data
        dataset = self.load_training_data()
        formatted_dataset = self.format_data_for_training(dataset)

        # Training arguments
        training_args = TrainingArguments(
            output_dir=self.config.output_dir,
            num_train_epochs=self.config.num_train_epochs,
            per_device_train_batch_size=self.config.per_device_train_batch_size,
            gradient_accumulation_steps=self.config.gradient_accumulation_steps,
            learning_rate=self.config.learning_rate,
            warmup_steps=self.config.warmup_steps,
            logging_steps=self.config.logging_steps,
            save_steps=self.config.save_steps,
            save_total_limit=3,
            report_to=self.config.report_to,
            logging_dir=self.config.logging_dir,
            fp16=True,
            gradient_checkpointing=True,
            optim="paged_adamw_8bit",
            lr_scheduler_type="cosine",
            max_grad_norm=0.3,
            group_by_length=True,
        )

        # Trainer (TRL 0.23.x API)
        # Dataset is pre-formatted with 'text' column
        # No formatting_func needed (avoids completion_only_loss conflict)
        trainer = SFTTrainer(
            model=self.model,
            train_dataset=formatted_dataset,
            args=training_args,
        )

        print()
        print("=" * 80)
        print("🏃 Training started...")
        print("=" * 80)
        print()

        # Train
        trainer.train()

        print()
        print("=" * 80)
        print("✅ Training completed!")
        print("=" * 80)
        print()

        # Save final model
        print(f"💾 Saving fine-tuned model to {self.config.output_dir}")
        trainer.save_model(self.config.output_dir)
        self.tokenizer.save_pretrained(self.config.output_dir)

        print()
        print("✅ Model saved successfully")
        print()
        print("🎉 Fine-tuning complete! Your model is ready to use.")


def load_config(config_path: str) -> FineTuningConfig:
    """Load configuration from YAML file"""
    with open(config_path, 'r') as f:
        config_dict = yaml.safe_load(f)

    return FineTuningConfig(**config_dict)


def main():
    parser = argparse.ArgumentParser(description="Fine-tune LLama 3 for Course Creator")
    parser.add_argument("--config", type=str, required=True,
                       help="Path to training configuration YAML file")
    parser.add_argument("--resume-from-checkpoint", type=str, default=None,
                       help="Path to checkpoint to resume training from")

    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)

    # Create output directory
    os.makedirs(config.output_dir, exist_ok=True)
    os.makedirs(config.logging_dir, exist_ok=True)

    # Run fine-tuning
    fine_tuner = LLama3FineTuner(config)
    fine_tuner.train()


if __name__ == "__main__":
    main()
