def fibonacci():
    a, b = 0, 1
    result = [a, b]
    for _ in range(8):
        a, b = b, a + b
        result.append(b)
    return result

# Test the function
numbers = fibonacci()
print(numbers)
