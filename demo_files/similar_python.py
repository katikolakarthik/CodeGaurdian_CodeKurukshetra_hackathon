"""
Similar Python code for testing plagiarism detection.
This is another sorting algorithm implementation with similar structure.
"""

def bubble_sort_algorithm(data):
    """Sort data using bubble sort method."""
    length = len(data)
    
    # Go through all array elements
    for i in range(length):
        # Last i elements are already sorted
        for j in range(0, length - i - 1):
            # Exchange if current element is larger than next element
            if data[j] > data[j + 1]:
                data[j], data[j + 1] = data[j + 1], data[j]
    
    return data

def quick_sort_algorithm(data):
    """Sort data using quick sort method."""
    if len(data) <= 1:
        return data
    
    pivot = data[len(data) // 2]
    left_part = [x for x in data if x < pivot]
    middle_part = [x for x in data if x == pivot]
    right_part = [x for x in data if x > pivot]
    
    return quick_sort_algorithm(left_part) + middle_part + quick_sort_algorithm(right_part)

def binary_search_algorithm(data, target_value):
    """Search for target_value in sorted data using binary search."""
    left_index, right_index = 0, len(data) - 1
    
    while left_index <= right_index:
        middle_index = (left_index + right_index) // 2
        if data[middle_index] == target_value:
            return middle_index
        elif data[middle_index] < target_value:
            left_index = middle_index + 1
        else:
            right_index = middle_index - 1
    
    return -1

def fibonacci_sequence(n):
    """Calculate nth Fibonacci number."""
    if n <= 1:
        return n
    return fibonacci_sequence(n - 1) + fibonacci_sequence(n - 2)

# Example usage
if __name__ == "__main__":
    test_numbers = [64, 34, 25, 12, 22, 11, 90]
    print("Original array:", test_numbers)
    
    sorted_with_bubble = bubble_sort_algorithm(test_numbers.copy())
    print("Bubble sort result:", sorted_with_bubble)
    
    sorted_with_quick = quick_sort_algorithm(test_numbers.copy())
    print("Quick sort result:", sorted_with_quick)
    
    search_target = 25
    result_index = binary_search_algorithm(sorted_with_quick, search_target)
    print(f"Binary search for {search_target}: found at index {result_index}")
    
    print(f"Fibonacci(10): {fibonacci_sequence(10)}")
