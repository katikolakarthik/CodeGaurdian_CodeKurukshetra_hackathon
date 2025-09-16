"""
Sample Python code for testing plagiarism detection.
This is a simple sorting algorithm implementation.
"""

def bubble_sort(arr):
    """Sort an array using bubble sort algorithm."""
    n = len(arr)
    
    # Traverse through all array elements
    for i in range(n):
        # Last i elements are already in place
        for j in range(0, n - i - 1):
            # Swap if the element found is greater than the next element
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    
    return arr

def quick_sort(arr):
    """Sort an array using quick sort algorithm."""
    if len(arr) <= 1:
        return arr
    
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    
    return quick_sort(left) + middle + quick_sort(right)

def binary_search(arr, target):
    """Search for target in sorted array using binary search."""
    left, right = 0, len(arr) - 1
    
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    
    return -1

def fibonacci(n):
    """Calculate nth Fibonacci number."""
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

# Example usage
if __name__ == "__main__":
    numbers = [64, 34, 25, 12, 22, 11, 90]
    print("Original array:", numbers)
    
    sorted_bubble = bubble_sort(numbers.copy())
    print("Bubble sort:", sorted_bubble)
    
    sorted_quick = quick_sort(numbers.copy())
    print("Quick sort:", sorted_quick)
    
    target = 25
    index = binary_search(sorted_quick, target)
    print(f"Binary search for {target}: index {index}")
    
    print(f"Fibonacci(10): {fibonacci(10)}")
