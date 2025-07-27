# Python script demonstrating student workspace
import json
import math

def calculate_fibonacci(n):
    '''Calculate Fibonacci sequence up to n terms'''
    sequence = []
    a, b = 0, 1
    for _ in range(n):
        sequence.append(a)
        a, b = b, a + b
    return sequence

def save_results(data, filename):
    '''Save results to JSON file'''
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Results saved to {filename}")

if __name__ == "__main__":
    fib = calculate_fibonacci(10)
    print("Fibonacci sequence:", fib)
    save_results({"fibonacci": fib}, "results.json")
