# ABOUTME: This file contains a function to calculate factorial of a number
# ABOUTME: Used for demonstration and testing purposes

def factorial(n):
    """
    Calculate the factorial of a non-negative integer.
    
    Args:
        n: A non-negative integer
        
    Returns:
        The factorial of n
        
    Raises:
        ValueError: If n is negative
        TypeError: If n is not an integer
    """
    if not isinstance(n, int):
        raise TypeError("Input must be an integer")
    
    if n < 0:
        raise ValueError("Input must be non-negative")
    
    if n == 0 or n == 1:
        return 1
    
    result = 1
    for i in range(2, n + 1):
        result *= i
    
    return result