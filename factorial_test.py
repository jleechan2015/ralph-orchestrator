def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

if __name__ == "__main__":
    result = factorial(5)
    print(f"factorial(5) = {result}")
