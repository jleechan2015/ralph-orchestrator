Write a simple Python function that calculates the factorial of a number.

The function should:
1. Be named `factorial`
2. Take a single integer argument
3. Return the factorial value
4. Handle edge cases (0 and negative numbers)

Save the function to a file called `factorial_test.py`.

## Solution

Created `factorial_test.py` with the following implementation:

```python
def factorial(n):
    if n < 0:
        raise ValueError("Factorial not defined for negative numbers")
    if n == 0:
        return 1
    result = 1
    for i in range(1, n + 1):
        result *= i
    return result
```

The function handles:
- Negative numbers: Raises ValueError
- Zero: Returns 1 (0! = 1)
- Positive integers: Calculates factorial iteratively

TASK_COMPLETE