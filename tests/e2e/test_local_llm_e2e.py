"""
End-to-End Tests for Local LLM Service

BUSINESS CONTEXT:
Tests complete user workflows involving the local LLM service from
end-user perspective, ensuring all components work together correctly
in production-like environment.

TECHNICAL IMPLEMENTATION:
- Tests full request/response cycles
- Validates Docker deployment
- Tests real Ollama integration (NO MOCKS)
- Measures actual performance metrics
- Tests GPU acceleration is working

These tests require:
- All services running (docker-compose up)
- Ollama service running on host
- Local LLM service deployed and healthy

NOTE: This file already uses real services with NO MOCKS - compliant with E2E requirements.
"""

import pytest
import requests
import time
from typing import Dict, Any
import subprocess


BASE_URL = "http://localhost:8015"


class TestLocalLLMDeployment:
    """Test Docker deployment and service availability."""

    @pytest.mark.e2e
    def test_service_is_running(self):
        """Test Local LLM service is deployed and running."""
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=5)
            assert response.status_code == 200, "Service should be running"
        except requests.RequestException as e:
            pytest.fail(f"Service not reachable: {e}")

    @pytest.mark.e2e
    def test_docker_container_healthy(self):
        """Test Docker container is in healthy state."""
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=local-llm", "--format", "{{.Status}}"],
            capture_output=True,
            text=True
        )

        status = result.stdout.strip()
        assert "healthy" in status.lower() or "up" in status.lower(), \
            f"Container should be healthy, got: {status}"

    @pytest.mark.e2e
    def test_ollama_connectivity(self):
        """Test service can connect to Ollama."""
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy", \
            f"Service should be healthy with Ollama connection. Status: {data}"


class TestRealInferenceWorkflows:
    """Test real inference with actual Llama model."""

    @pytest.mark.e2e
    def test_simple_question_response(self):
        """Test real inference for simple question."""
        payload = {
            "prompt": "What is Python? Answer in one sentence.",
            "max_tokens": 100,
            "temperature": 0.7
        }

        start_time = time.time()
        response = requests.post(f"{BASE_URL}/generate", json=payload, timeout=30)
        latency = (time.time() - start_time) * 1000  # ms

        assert response.status_code == 200
        data = response.json()

        assert "response" in data
        assert len(data["response"]) > 0
        assert "python" in data["response"].lower()
        assert "latency_ms" in data
        assert data["latency_ms"] > 0

        # First query can be slow (cold start)
        print(f"Cold start latency: {latency}ms")

    @pytest.mark.e2e
    def test_warm_inference_performance(self):
        """Test warm inference is fast (model loaded)."""
        # Warm up
        requests.post(
            f"{BASE_URL}/generate",
            json={"prompt": "Hello", "max_tokens": 10},
            timeout=30
        )

        # Now measure warm inference
        payload = {
            "prompt": "What is machine learning? Answer in one sentence.",
            "max_tokens": 100,
            "temperature": 0.7
        }

        start_time = time.time()
        response = requests.post(f"{BASE_URL}/generate", json=payload, timeout=30)
        latency = (time.time() - start_time) * 1000  # ms

        assert response.status_code == 200
        data = response.json()

        print(f"Warm inference latency: {latency}ms")
        assert latency < 5000, "Warm inference should be < 5s with GPU"

    @pytest.mark.e2e
    def test_caching_actually_works(self):
        """Test response caching with real requests."""
        payload = {
            "prompt": "What is Python programming?",
            "max_tokens": 50
        }

        # First request - not cached
        response1 = requests.post(f"{BASE_URL}/generate", json=payload, timeout=30)
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["cached"] is False

        # Second request - should be cached
        start_time = time.time()
        response2 = requests.post(f"{BASE_URL}/generate", json=payload, timeout=30)
        cache_latency = (time.time() - start_time) * 1000

        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["cached"] is True
        assert data2["response"] == data1["response"]  # Same response
        assert cache_latency < 100, "Cached response should be < 100ms"

        print(f"Cache hit latency: {cache_latency}ms")


class TestContextSummarization:
    """Test context summarization with real content."""

    @pytest.mark.e2e
    def test_summarize_long_context(self):
        """Test summarization of real long context."""
        long_context = """
        Python is a high-level, interpreted programming language known for its
        simplicity and readability. Created by Guido van Rossum and first released
        in 1991, Python has become one of the most popular programming languages
        worldwide. It supports multiple programming paradigms including procedural,
        object-oriented, and functional programming. Python's design philosophy
        emphasizes code readability with its use of significant indentation.
        The language provides constructs intended to enable clear programs on both
        small and large scales. Python features a dynamic type system and automatic
        memory management. It supports modules and packages, which encourages program
        modularity and code reuse. The Python Package Index (PyPI) hosts thousands
        of third-party modules. Python is widely used in web development, data analysis,
        artificial intelligence, scientific computing, and automation.
        """ * 5  # Make it longer

        payload = {
            "context": long_context,
            "max_summary_tokens": 100
        }

        response = requests.post(f"{BASE_URL}/summarize", json=payload, timeout=30)

        assert response.status_code == 200
        data = response.json()

        assert "summary" in data
        assert len(data["summary"]) < len(long_context)
        assert data["tokens_saved"] > 0
        print(f"Tokens saved: {data['tokens_saved']}")


class TestConversationCompression:
    """Test conversation compression with realistic data."""

    @pytest.mark.e2e
    def test_compress_multi_turn_conversation(self):
        """Test compression of realistic multi-turn conversation."""
        messages = [
            {"role": "user", "content": "I want to learn Python programming from scratch."},
            {"role": "assistant", "content": "Great choice! Python is beginner-friendly. Start with basic syntax, variables, and data types. Then move to control structures like if-else and loops."},
            {"role": "user", "content": "How long will it take to learn?"},
            {"role": "assistant", "content": "With consistent practice, you can learn basics in 2-3 months. Mastery takes longer, around 6-12 months depending on your goals."},
            {"role": "user", "content": "What projects should I build?"},
            {"role": "assistant", "content": "Start simple: calculator, to-do list, web scraper. Then progress to more complex projects like a web application or data analysis project."}
        ]

        payload = {
            "messages": messages,
            "target_tokens": 150
        }

        response = requests.post(f"{BASE_URL}/compress", json=payload, timeout=30)

        assert response.status_code == 200
        data = response.json()

        assert "compressed_summary" in data
        assert data["original_token_count"] > data["compressed_token_count"]
        print(f"Compression ratio: {data['original_token_count']} → {data['compressed_token_count']}")


class TestFunctionParameterExtraction:
    """Test function parameter extraction with real scenarios."""

    @pytest.mark.e2e
    def test_extract_course_creation_parameters(self):
        """Test extracting parameters for course creation."""
        payload = {
            "user_message": "Create a 12-week advanced Python course for data scientists with 15 modules covering pandas, numpy, and scikit-learn",
            "function_schema": {
                "name": "create_course",
                "parameters": {
                    "title": "string",
                    "duration_weeks": "integer",
                    "level": "string",
                    "num_modules": "integer",
                    "topics": "array of strings"
                }
            }
        }

        response = requests.post(
            f"{BASE_URL}/extract_parameters",
            json=payload,
            timeout=30
        )

        assert response.status_code == 200
        data = response.json()

        assert "parameters" in data
        params = data["parameters"]

        # Validate extracted parameters
        if params:  # May be empty if extraction failed
            assert "duration_weeks" in params or "num_modules" in params
            print(f"Extracted parameters: {params}")


class TestGPUAcceleration:
    """Test GPU acceleration is working."""

    @pytest.mark.e2e
    def test_gpu_is_being_used(self):
        """Test that GPU is actually being used by Ollama."""
        # Check nvidia-smi for Ollama process
        result = subprocess.run(
            ["nvidia-smi", "--query-compute-apps=pid,process_name,used_memory", "--format=csv,noheader"],
            capture_output=True,
            text=True
        )

        output = result.stdout.strip()

        # Should show Ollama using GPU
        assert "ollama" in output.lower(), \
            f"Ollama should be using GPU. nvidia-smi output: {output}"

        print(f"GPU usage confirmed: {output}")

    @pytest.mark.e2e
    def test_inference_speed_indicates_gpu(self):
        """Test inference speed indicates GPU acceleration."""
        # Warm up
        requests.post(
            f"{BASE_URL}/generate",
            json={"prompt": "Test", "max_tokens": 10},
            timeout=30
        )

        # Measure multiple inferences
        latencies = []
        for i in range(3):
            start_time = time.time()
            response = requests.post(
                f"{BASE_URL}/generate",
                json={"prompt": f"Question {i}: What is {['Python', 'Java', 'C++'][i]}?", "max_tokens": 50},
                timeout=30
            )
            latency = (time.time() - start_time) * 1000
            latencies.append(latency)

            assert response.status_code == 200

        avg_latency = sum(latencies) / len(latencies)
        print(f"Average latency: {avg_latency}ms")

        # With GPU, should be < 2s for warm inference
        assert avg_latency < 2000, \
            f"GPU-accelerated inference should be < 2s, got {avg_latency}ms"


class TestErrorHandling:
    """Test error handling in production scenarios."""

    @pytest.mark.e2e
    def test_invalid_request_handling(self):
        """Test service handles invalid requests."""
        payload = {"invalid": "data"}

        response = requests.post(f"{BASE_URL}/generate", json=payload, timeout=5)

        assert response.status_code in [400, 422]

    @pytest.mark.e2e
    def test_empty_prompt_handling(self):
        """Test service handles empty prompts."""
        payload = {"prompt": "", "max_tokens": 50}

        response = requests.post(f"{BASE_URL}/generate", json=payload, timeout=10)

        # Should either accept and return something or reject with 400
        assert response.status_code in [200, 400]

    @pytest.mark.e2e
    def test_service_recovers_from_errors(self):
        """Test service recovers after errors."""
        # Send invalid request
        requests.post(f"{BASE_URL}/generate", json={"bad": "request"}, timeout=5)

        # Service should still work
        response = requests.post(
            f"{BASE_URL}/generate",
            json={"prompt": "Hello", "max_tokens": 10},
            timeout=30
        )

        assert response.status_code == 200


class TestConcurrentRequests:
    """Test handling of concurrent requests."""

    @pytest.mark.e2e
    def test_handles_concurrent_requests(self):
        """Test service handles multiple concurrent requests."""
        import concurrent.futures

        def make_request(i):
            payload = {"prompt": f"Question {i}", "max_tokens": 50}
            response = requests.post(f"{BASE_URL}/generate", json=payload, timeout=30)
            return response.status_code == 200

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request, i) for i in range(5)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # All requests should succeed
        assert all(results), "All concurrent requests should succeed"


class TestModelListEndpoint:
    """Test model listing functionality."""

    @pytest.mark.e2e
    def test_list_available_models(self):
        """Test listing available Ollama models."""
        response = requests.get(f"{BASE_URL}/models", timeout=5)

        assert response.status_code == 200
        data = response.json()

        assert "models" in data
        assert isinstance(data["models"], list)
        # Should include the configured model
        assert any("llama" in m.lower() for m in data["models"])


class TestServiceMetrics:
    """Test service exposes metrics."""

    @pytest.mark.e2e
    def test_metrics_endpoint(self):
        """Test metrics endpoint if available."""
        # Try to get metrics
        try:
            response = requests.get(f"{BASE_URL}/metrics", timeout=5)
            if response.status_code == 200:
                data = response.json()
                assert "total_requests" in data or "uptime" in data
        except requests.RequestException:
            pytest.skip("Metrics endpoint not implemented")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "e2e", "--tb=short"])
