# Data analysis script
import math

# Sample data processing
data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

# Statistical calculations
mean = sum(data) / len(data)
variance = sum((x - mean) ** 2 for x in data) / len(data)
std_dev = math.sqrt(variance)

print(f"Data: {data}")
print(f"Mean: {mean:.2f}")
print(f"Standard Deviation: {std_dev:.2f}")

# Save processed data
with open("analysis_results.txt", "w") as f:
    f.write(f"Statistical Analysis Results\n")
    f.write(f"=========================\n")
    f.write(f"Dataset: {data}\n")
    f.write(f"Mean: {mean:.2f}\n")
    f.write(f"Std Dev: {std_dev:.2f}\n")
