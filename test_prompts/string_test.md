Write a Python function that reverses words in a sentence while keeping the word order intact. For example, "Hello World" becomes "olleH dlroW".

## Solution

```python
def reverse_words(sentence):
    """
    Reverses each word in a sentence while keeping the word order intact.
    
    Args:
        sentence (str): The input sentence
    
    Returns:
        str: The sentence with each word reversed
    
    Examples:
        >>> reverse_words("Hello World")
        'olleH dlroW'
        >>> reverse_words("Python is awesome")
        'nohtyP si emosewa'
    """
    words = sentence.split()
    reversed_words = [word[::-1] for word in words]
    return ' '.join(reversed_words)

# Test the function
if __name__ == "__main__":
    # Test cases
    test_cases = [
        ("Hello World", "olleH dlroW"),
        ("Python is awesome", "nohtyP si emosewa"),
        ("a", "a"),
        ("", ""),
        ("The quick brown fox", "ehT kciuq nworb xof")
    ]
    
    for input_str, expected in test_cases:
        result = reverse_words(input_str)
        print(f"Input: '{input_str}'")
        print(f"Output: '{result}'")
        print(f"Expected: '{expected}'")
        print(f"Pass: {result == expected}\n")
```

TASK_COMPLETE