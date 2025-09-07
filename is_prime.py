# ABOUTME: This file contains a function to check if a number is prime
# ABOUTME: A prime number is a natural number greater than 1 with no positive divisors other than 1 and itself

def is_prime(n):
    """
    Check if a number is prime.
    
    Args:
        n: An integer to check for primality
        
    Returns:
        bool: True if n is prime, False otherwise
    """
    if n <= 1:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    
    # Check odd divisors up to the square root of n
    for i in range(3, int(n**0.5) + 1, 2):
        if n % i == 0:
            return False
    
    return True