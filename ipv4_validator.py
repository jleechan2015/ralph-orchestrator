# ABOUTME: This file contains a function to validate IPv4 addresses
# ABOUTME: It checks if a string represents a valid IPv4 address format

def is_valid_ipv4(address):
    """
    Check if a string is a valid IPv4 address.
    
    Args:
        address (str): The string to check
        
    Returns:
        bool: True if valid IPv4 address, False otherwise
    """
    if not isinstance(address, str):
        return False
    
    parts = address.split('.')
    
    if len(parts) != 4:
        return False
    
    for part in parts:
        if not part:
            return False
        
        if part != '0' and part.startswith('0'):
            return False
        
        try:
            num = int(part)
            if num < 0 or num > 255:
                return False
        except ValueError:
            return False
    
    return True