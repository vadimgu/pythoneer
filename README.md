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
$ pythoneer example.py max
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

## Options

You can provide additional options to Pythoneer by declaring dict literal in the body of a function. Like this

```
def max(a: int, b:int) -> int
    """
    >>> max(5, 6)
    6
    >>> max(6, 5)
    6
    """
    {'max_complexity': 2}
    ...
```

### Using globals

By default Pythoneer will use only variables local to functions.

```python
import math

def factorial_limited(a: int, b:int) -> int
    """
    Return the min(a!, b)
    >>> f(1, 100)
    1
    >>> f(2, 100)
    2
    >>> f(3, 100)
    6
    >>> f(5, 100)
    100
    """
    factorial = math.factorial  # type: Callable[[int], int]
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
