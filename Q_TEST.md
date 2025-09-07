Create a Python file called fibonacci.py that calculates the first 10 Fibonacci numbers and prints them.

## Solution

Created fibonacci.py with the following code:

```python
a, b = 0, 1
for _ in range(10):
    print(a)
    a, b = b, a + b
```

This uses tuple unpacking to efficiently calculate the Fibonacci sequence without needing a separate function or list storage.

TASK_COMPLETE