---
title: "Python List Comprehension"
domain: "programming"
subdomain: "python"
source: "Python Official Documentation"
source_license: "PSF"
source_id: "python-docs-3.12"
source_path: "tutorial/datastructures.html"
retrieved_at: "2026-02-26"
verified: "2026-02-26"
importance: 0.8
tags: ["python", "lists", "comprehension", "syntax"]
version: "1.0.0"
content_hash: "sha256:placeholder"
---

# Python List Comprehension

List comprehensions provide a concise way to create lists in Python. They consist of brackets containing an expression followed by a for clause, then zero or more for or if clauses.

## Basic Syntax

```python
new_list = [expression for item in iterable if condition]
```

## Examples

Simple list comprehension:
```python
squares = [x**2 for x in range(10)]
# Result: [0, 1, 4, 9, 16, 25, 36, 49, 64, 81]
```

With condition:
```python
even_squares = [x**2 for x in range(10) if x % 2 == 0]
# Result: [0, 4, 16, 36, 64]
```

## Nested List Comprehensions

List comprehensions can contain complex expressions and nested comprehensions:

```python
matrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
flattened = [num for row in matrix for num in row]
# Result: [1, 2, 3, 4, 5, 6, 7, 8, 9]
```

## When to Use

List comprehensions are more concise and often faster than equivalent for loops. However, they should be used when the logic is simple and readable. Complex comprehensions should be replaced with regular for loops for clarity.
