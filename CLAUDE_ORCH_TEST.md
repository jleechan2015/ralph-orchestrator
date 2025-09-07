Create a Python function that returns the first n prime numbers.

```python
def first_n_primes(n):
    primes = []
    num = 2
    while len(primes) < n:
        if all(num % p != 0 for p in primes):
            primes.append(num)
        num += 1
    return primes
```

TASK_COMPLETE