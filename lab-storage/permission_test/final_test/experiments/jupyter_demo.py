# Jupyter-style experiments
# This file demonstrates that subdirectories work properly

def run_experiment(name, iterations=5):
    '''Run a simple experiment'''
    results = []
    for i in range(iterations):
        # Simulate some computation
        result = i ** 2 + 2 * i + 1
        results.append(result)
        print(f"{name} - Iteration {i+1}: {result}")
    
    return results

# Run experiments
print("Running Workspace File Experiments...")
exp1 = run_experiment("Quadratic Function", 5)
exp2 = run_experiment("Linear Growth", 3)

print(f"\nExperiment 1 Results: {exp1}")
print(f"Experiment 2 Results: {exp2}")

# Save experiment log
with open("experiment_log.txt", "w") as f:
    f.write("Experiment Log\n")
    f.write("==============\n")
    f.write(f"Experiment 1: {exp1}\n")
    f.write(f"Experiment 2: {exp2}\n")
