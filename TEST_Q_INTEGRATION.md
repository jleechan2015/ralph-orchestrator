Write a Python function that calculates the greatest common divisor (GCD) of two numbers using the Euclidean algorithm. Save it to a file called gcd_calculator.py

## Solution

Created `gcd_calculator.py` with the following implementation:

```python
def gcd(a, b):
    while b:
        a, b = b, a % b
    return a
```

This implements the Euclidean algorithm efficiently using the iterative approach. The algorithm repeatedly replaces the larger number with the remainder of the division until one number becomes zero.

TASK_COMPLETE