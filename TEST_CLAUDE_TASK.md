Write a Python function that generates the Fibonacci sequence.

The function should:
1. Be named `fibonacci`
2. Take a single integer argument n (number of terms)
3. Return a list of the first n Fibonacci numbers
4. Handle edge cases (n <= 0)

Save the function to a file called `fibonacci_test.py`.

## Solution

The fibonacci function has been implemented in `fibonacci_test.py`. The function:
- Takes an integer `n` as input
- Returns an empty list for n <= 0 (edge case)
- Returns [0] for n = 1
- Returns [0, 1] for n = 2
- For n > 2, generates the sequence iteratively by adding the previous two numbers
- Returns a list containing the first n Fibonacci numbers

The implementation includes test cases that verify:
- Edge cases (n <= 0)
- Base cases (n = 1, 2)
- Normal cases (n = 5, 10)

TASK_COMPLETE