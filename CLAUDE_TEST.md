Create a Python file called prime_checker.py that checks if a number is prime. Include a function is_prime(n) that returns True if n is prime, False otherwise.

## Solution

Created `prime_checker.py` with the following implementation:

```python
def is_prime(n):
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    
    return True
```

This function efficiently checks if a number is prime by:
- Handling edge cases (n <= 1 returns False)
- Checking small primes (2 and 3)
- Eliminating even numbers and multiples of 3
- Using the 6k±1 optimization to check only potential prime candidates

TASK_COMPLETE