#!/usr/bin/env python3
"""
Training Data Preparation for LLama 3 Fine-tuning

BUSINESS CONTEXT:
Prepares and combines multiple datasets for fine-tuning the local LLM
to better serve the Course Creator platform's educational needs.

TECHNICAL IMPLEMENTATION:
- Downloads datasets from HuggingFace
- Formats data for LLama 3 training
- Combines datasets with appropriate weighting
- Outputs training-ready JSONL files

USAGE:
    python3 prepare_training_data.py --output-dir ./training_data
"""

import os
import json
import argparse
from datasets import load_dataset, concatenate_datasets
from typing import List, Dict, Any
from tqdm import tqdm


class TrainingDataPreparer:
    """
    Prepares training data for LLama 3 fine-tuning
    """

    def __init__(self, output_dir: str = "./training_data"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def format_for_llama3(self, example: Dict[str, Any], dataset_type: str) -> Dict[str, str]:
        """
        Format examples for LLama 3 chat template

        Args:
            example: Raw dataset example
            dataset_type: Type of dataset (oasst, alpaca, code, etc.)

        Returns:
            Formatted example with 'prompt' and 'completion' keys
        """
        if dataset_type == "oasst":
            # OpenAssistant format
            return {
                "prompt": f"<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\n{example['text']}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n",
                "completion": f"{example['text']}<|eot_id|>"
            }

        elif dataset_type == "alpaca":
            # Alpaca format
            instruction = example.get('instruction', '')
            input_text = example.get('input', '')
            output = example.get('output', '')

            if input_text:
                prompt_text = f"{instruction}\n\nInput: {input_text}"
            else:
                prompt_text = instruction

            return {
                "prompt": f"<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\n{prompt_text}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n",
                "completion": f"{output}<|eot_id|>"
            }

        elif dataset_type == "code":
            # Code generation format
            instruction = example.get('instruction', '')
            output = example.get('output', '')

            return {
                "prompt": f"<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\n{instruction}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n",
                "completion": f"```python\n{output}\n```<|eot_id|>"
            }

        elif dataset_type == "qa":
            # Q&A format (MMLU, SciQ, etc.)
            question = example.get('question', '')
            answer = example.get('answer', '')

            return {
                "prompt": f"<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\n{question}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n",
                "completion": f"{answer}<|eot_id|>"
            }

        elif dataset_type == "eli5":
            # ELI5 format
            title = example.get('title', '')
            selftext = example.get('selftext', '')
            answers = example.get('answers', {})

            question = f"{title}\n{selftext}" if selftext else title
            answer = answers.get('text', [''])[0] if answers else ''

            return {
                "prompt": f"<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\nExplain this concept clearly: {question}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n",
                "completion": f"{answer}<|eot_id|>"
            }

        else:
            raise ValueError(f"Unknown dataset type: {dataset_type}")

    def download_and_prepare_oasst(self, num_samples: int = 40000) -> List[Dict]:
        """
        Download and prepare OpenAssistant dataset

        Args:
            num_samples: Number of samples to use

        Returns:
            List of formatted examples
        """
        print("📥 Downloading OpenAssistant dataset...")
        dataset = load_dataset("OpenAssistant/oasst1", split="train")

        # Filter for high-quality conversations (rank 0 = best)
        filtered = dataset.filter(lambda x: x.get('rank') == 0)

        formatted = []
        for i, example in enumerate(tqdm(filtered, desc="Formatting OASST")):
            if i >= num_samples:
                break
            try:
                formatted_example = self.format_for_llama3(example, "oasst")
                formatted.append(formatted_example)
            except Exception as e:
                print(f"Warning: Failed to format example {i}: {e}")
                continue

        print(f"✅ Prepared {len(formatted)} OASST examples")
        return formatted

    def download_and_prepare_alpaca(self, num_samples: int = 32000) -> List[Dict]:
        """
        Download and prepare Alpaca dataset

        Args:
            num_samples: Number of samples to use

        Returns:
            List of formatted examples
        """
        print("📥 Downloading Alpaca dataset...")
        dataset = load_dataset("tatsu-lab/alpaca", split="train")

        formatted = []
        for i, example in enumerate(tqdm(dataset, desc="Formatting Alpaca")):
            if i >= num_samples:
                break
            try:
                formatted_example = self.format_for_llama3(example, "alpaca")
                formatted.append(formatted_example)
            except Exception as e:
                print(f"Warning: Failed to format example {i}: {e}")
                continue

        print(f"✅ Prepared {len(formatted)} Alpaca examples")
        return formatted

    def download_and_prepare_code_alpaca(self, num_samples: int = 20000) -> List[Dict]:
        """
        Download and prepare CodeAlpaca dataset

        Args:
            num_samples: Number of samples to use

        Returns:
            List of formatted examples
        """
        print("📥 Downloading CodeAlpaca dataset...")
        dataset = load_dataset("sahil2801/CodeAlpaca-20k", split="train")

        formatted = []
        for i, example in enumerate(tqdm(dataset, desc="Formatting CodeAlpaca")):
            if i >= num_samples:
                break
            try:
                formatted_example = self.format_for_llama3(example, "code")
                formatted.append(formatted_example)
            except Exception as e:
                print(f"Warning: Failed to format example {i}: {e}")
                continue

        print(f"✅ Prepared {len(formatted)} CodeAlpaca examples")
        return formatted

    def download_and_prepare_mmlu(self, num_samples: int = 15000) -> List[Dict]:
        """
        Download and prepare MMLU dataset

        Args:
            num_samples: Number of samples to use

        Returns:
            List of formatted examples
        """
        print("📥 Downloading MMLU dataset...")

        # Load multiple MMLU subsets for diverse coverage
        subsets = ["abstract_algebra", "anatomy", "astronomy", "business_ethics",
                   "clinical_knowledge", "college_biology", "college_chemistry",
                   "college_computer_science", "college_mathematics", "college_physics",
                   "computer_security", "conceptual_physics", "econometrics"]

        all_examples = []
        samples_per_subset = num_samples // len(subsets)

        for subset in tqdm(subsets, desc="Loading MMLU subsets"):
            try:
                dataset = load_dataset("cais/mmlu", subset, split="test")

                for i, example in enumerate(dataset):
                    if i >= samples_per_subset:
                        break

                    # Format MMLU example
                    question = example.get('question', '')
                    choices = example.get('choices', [])
                    answer = example.get('answer', 0)

                    # Build question with choices
                    formatted_question = f"{question}\n\n"
                    for idx, choice in enumerate(choices):
                        formatted_question += f"{chr(65+idx)}. {choice}\n"

                    formatted_answer = f"The correct answer is {chr(65+answer)}. {choices[answer]}"

                    formatted_example = {
                        "prompt": f"<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\n{formatted_question}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n",
                        "completion": f"{formatted_answer}<|eot_id|>"
                    }
                    all_examples.append(formatted_example)
            except Exception as e:
                print(f"Warning: Failed to load subset {subset}: {e}")
                continue

        print(f"✅ Prepared {len(all_examples)} MMLU examples")
        return all_examples

    def download_and_prepare_eli5(self, num_samples: int = 25000) -> List[Dict]:
        """
        Download and prepare ELI5 dataset

        Args:
            num_samples: Number of samples to use

        Returns:
            List of formatted examples
        """
        print("📥 Downloading ELI5 dataset...")
        dataset = load_dataset("eli5_category", split="train")

        # Filter for examples with good answers
        filtered = dataset.filter(
            lambda x: x.get('answers') and
                      len(x['answers'].get('text', [])) > 0 and
                      len(x['answers']['text'][0]) > 100  # Ensure substantial answers
        )

        formatted = []
        for i, example in enumerate(tqdm(filtered, desc="Formatting ELI5")):
            if i >= num_samples:
                break
            try:
                formatted_example = self.format_for_llama3(example, "eli5")
                formatted.append(formatted_example)
            except Exception as e:
                print(f"Warning: Failed to format example {i}: {e}")
                continue

        print(f"✅ Prepared {len(formatted)} ELI5 examples")
        return formatted

    def combine_and_save(self, datasets: Dict[str, List[Dict]], output_file: str = "combined_training_data.jsonl"):
        """
        Combine datasets and save to JSONL file

        Args:
            datasets: Dictionary of dataset_name -> examples
            output_file: Output filename
        """
        output_path = os.path.join(self.output_dir, output_file)

        print(f"\n📊 Combining datasets...")
        all_examples = []
        for name, examples in datasets.items():
            print(f"  - {name}: {len(examples)} examples")
            all_examples.extend(examples)

        print(f"\n💾 Saving {len(all_examples)} examples to {output_path}")
        with open(output_path, 'w', encoding='utf-8') as f:
            for example in tqdm(all_examples, desc="Writing to file"):
                f.write(json.dumps(example, ensure_ascii=False) + '\n')

        print(f"✅ Training data saved to {output_path}")
        print(f"📈 Total examples: {len(all_examples)}")

        # Save dataset statistics
        stats = {
            "total_examples": len(all_examples),
            "datasets": {name: len(examples) for name, examples in datasets.items()},
            "output_file": output_path
        }

        stats_path = os.path.join(self.output_dir, "dataset_stats.json")
        with open(stats_path, 'w') as f:
            json.dump(stats, f, indent=2)

        print(f"📊 Statistics saved to {stats_path}")

    def prepare_all(self):
        """
        Prepare all recommended datasets for Course Creator platform
        """
        print("=" * 80)
        print("🚀 Preparing Training Data for LLama 3 Fine-tuning")
        print("=" * 80)
        print()

        datasets = {}

        # Priority 1: Core datasets
        datasets["oasst"] = self.download_and_prepare_oasst(num_samples=40000)
        datasets["alpaca"] = self.download_and_prepare_alpaca(num_samples=32000)
        datasets["code_alpaca"] = self.download_and_prepare_code_alpaca(num_samples=20000)
        datasets["mmlu"] = self.download_and_prepare_mmlu(num_samples=15000)
        datasets["eli5"] = self.download_and_prepare_eli5(num_samples=25000)

        # Combine and save
        self.combine_and_save(datasets)

        print()
        print("=" * 80)
        print("✅ Training data preparation complete!")
        print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description="Prepare training data for LLama 3 fine-tuning")
    parser.add_argument("--output-dir", type=str, default="./training_data",
                       help="Output directory for training data")
    parser.add_argument("--quick", action="store_true",
                       help="Quick mode: Use fewer samples for testing")

    args = parser.parse_args()

    preparer = TrainingDataPreparer(output_dir=args.output_dir)

    if args.quick:
        print("🏃 Quick mode: Using reduced sample sizes")
        # Use smaller samples for quick testing
        datasets = {
            "oasst": preparer.download_and_prepare_oasst(num_samples=1000),
            "alpaca": preparer.download_and_prepare_alpaca(num_samples=1000),
            "code_alpaca": preparer.download_and_prepare_code_alpaca(num_samples=500),
        }
        preparer.combine_and_save(datasets, output_file="quick_training_data.jsonl")
    else:
        preparer.prepare_all()


if __name__ == "__main__":
    main()
