# Pythoneer (WORK IN PROGRESS)

Pythoneer is a tool that can write Python functions.

You write a function definition with tests and Pythoneer does the rest for
you. For example

```python
def max(a: int, b:int) -> int
    """
    >>> max(5, 6)
    6
    >>> max(6, 5)
    6
    """
    ...
```

Pythoneer will write code replacing the ellipsis statement (`...`).

## Basic Usage

```bash
$ pythoneer example.py
def max(a: int, b:int) -> int
    """
    >>> max(5, 6)
    6
    >>> max(6, 5)
    6
    """
    return_value = a
    if a < b:
        return_value = b
    return return_value
```

## Installation

Run `pip install` command in you development virtual environment.

```bash
[env]$ pip install pythoneer
```

## Advanced Usage

### Hints

```python
from operator import add

def sum(a: int, b:int) -> int
    """
    >>> sum(0, 0)
    0
    >>> sum(0, 1)
    1
    >>> sum(2, 3)
    5
    """
    add = add  # type: Callable[[int, int], int]
    ...
```

### Search Boundary

...

#### Cyclomatic Complexity

...

#### Nesting Level

...

### Limits

time limit.

## IDE Integration

### VSCode

...
