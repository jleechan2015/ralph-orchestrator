# ABOUTME: This file contains the fibonacci function that generates the Fibonacci sequence
# ABOUTME: The function takes an integer n and returns the first n Fibonacci numbers

def fibonacci(n):
    """
    Generate the first n numbers in the Fibonacci sequence.
    
    Args:
        n: Number of Fibonacci numbers to generate
        
    Returns:
        List of the first n Fibonacci numbers
    """
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    elif n == 2:
        return [0, 1]
    
    fib_sequence = [0, 1]
    for i in range(2, n):
        next_fib = fib_sequence[i-1] + fib_sequence[i-2]
        fib_sequence.append(next_fib)
    
    return fib_sequence


if __name__ == "__main__":
    # Test the function with various inputs
    test_cases = [
        (0, []),
        (-5, []),
        (1, [0]),
        (2, [0, 1]),
        (5, [0, 1, 1, 2, 3]),
        (10, [0, 1, 1, 2, 3, 5, 8, 13, 21, 34])
    ]
    
    for n, expected in test_cases:
        result = fibonacci(n)
        assert result == expected, f"Failed for n={n}: expected {expected}, got {result}"
        print(f"fibonacci({n}) = {result} ✓")
    
    print("\nAll tests passed!")