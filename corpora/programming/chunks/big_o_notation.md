---
title: "Big O Notation"
domain: "programming"
subdomain: "algorithms"
source: "Introduction to Algorithms"
source_license: "Educational Fair Use"
source_id: "clrs-4th-edition"
source_path: "chapter3/asymptotic-notation"
retrieved_at: "2026-02-26"
verified: "2026-02-26"
importance: 0.95
tags: ["algorithms", "complexity", "big-o", "time-complexity"]
version: "1.0.0"
content_hash: "sha256:placeholder"
---

# Big O Notation

Big O notation is a mathematical notation that describes the limiting behavior of a function when the argument tends towards a particular value or infinity. In computer science, Big O notation is used to classify algorithms according to how their run time or space requirements grow as the input size grows.

## Definition

For a given function g(n), we denote by O(g(n)) the set of functions:

O(g(n)) = {f(n) : there exist positive constants c and n₀ such that 0 ≤ f(n) ≤ c·g(n) for all n ≥ n₀}

## Common Time Complexities

From fastest to slowest:

- **O(1)** - Constant time: The algorithm always takes the same amount of time, regardless of input size.
  Example: Accessing an array element by index.

- **O(log n)** - Logarithmic time: The algorithm's running time grows logarithmically with input size.
  Example: Binary search in a sorted array.

- **O(n)** - Linear time: Running time grows linearly with input size.
  Example: Finding the maximum element in an unsorted array.

- **O(n log n)** - Linearithmic time: Efficient sorting algorithms.
  Example: Merge sort, heap sort, quicksort (average case).

- **O(n²)** - Quadratic time: Running time grows quadratically.
  Example: Bubble sort, insertion sort, selection sort.

- **O(2ⁿ)** - Exponential time: Running time doubles with each addition to input.
  Example: Recursive calculation of Fibonacci numbers (naive approach).

- **O(n!)** - Factorial time: Extremely slow growth.
  Example: Generating all permutations of n items.

## Practical Implications

Understanding Big O notation helps developers:
- Choose appropriate algorithms for different problem sizes
- Predict how algorithms will scale
- Identify performance bottlenecks
- Compare algorithm efficiency independent of hardware
