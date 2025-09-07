# ABOUTME: This file contains a factorial function implementation
# ABOUTME: It provides both iterative and recursive approaches for calculating factorials

def factorial(n):
    """
    Calculate the factorial of a non-negative integer.
    
    Args:
        n: A non-negative integer
    
    Returns:
        The factorial of n (n!)
    
    Raises:
        ValueError: If n is negative
        TypeError: If n is not an integer
    """
    if not isinstance(n, int):
        raise TypeError("Input must be an integer")
    
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers")
    
    if n == 0 or n == 1:
        return 1
    
    result = 1
    for i in range(2, n + 1):
        result *= i
    
    return result


def factorial_recursive(n):
    """
    Calculate the factorial of a non-negative integer using recursion.
    
    Args:
        n: A non-negative integer
    
    Returns:
        The factorial of n (n!)
    
    Raises:
        ValueError: If n is negative
        TypeError: If n is not an integer
    """
    if not isinstance(n, int):
        raise TypeError("Input must be an integer")
    
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers")
    
    if n == 0 or n == 1:
        return 1
    
    return n * factorial_recursive(n - 1)


if __name__ == "__main__":
    # Test the factorial functions
    test_values = [0, 1, 5, 10]
    
    print("Testing factorial function:")
    for n in test_values:
        print(f"factorial({n}) = {factorial(n)}")
    
    print("\nTesting recursive factorial function:")
    for n in test_values:
        print(f"factorial_recursive({n}) = {factorial_recursive(n)}")