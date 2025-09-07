# ABOUTME: This file contains a function to check if a string is a palindrome
# ABOUTME: It ignores case and non-alphanumeric characters when checking

def is_palindrome(s):
    """
    Check if a string is a palindrome.
    
    Args:
        s: The string to check
        
    Returns:
        True if the string is a palindrome, False otherwise
    """
    # Remove non-alphanumeric characters and convert to lowercase
    cleaned = ''.join(char.lower() for char in s if char.isalnum())
    
    # Check if the cleaned string equals its reverse
    return cleaned == cleaned[::-1]