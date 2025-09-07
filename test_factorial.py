# ABOUTME: Test file for factorial function
# ABOUTME: Tests factorial function with inputs 5 and 10

import unittest
from factorial import factorial

class TestFactorial(unittest.TestCase):
    
    def test_factorial_of_5(self):
        """Test factorial of 5"""
        result = factorial(5)
        self.assertEqual(result, 120)
        
    def test_factorial_of_10(self):
        """Test factorial of 10"""
        result = factorial(10)
        self.assertEqual(result, 3628800)

if __name__ == '__main__':
    unittest.main()