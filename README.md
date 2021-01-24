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

TODO: Package
TODO: Upload to Pypi

For now, clone and run `setup.py`

```
$ git clone https://github.com/vadimgu/pythoneer.git
$ cd pythoneer
$ python setup.py install
```

## Configdict

You can provide additional options to Pythoneer by declaring configdict. A
configdict is a first dict literal following the "doctstring". For example:

```python
def max(a: int, b:int) -> int
    """ Return the largest value."""
    {
        "compare_operators": ['<=',],
    }
    ...
```

TODO: List all options.

### Using globals

By default Pythoneer will use only variables local to functions. To make it
use a global function, assign it to a local variable and add a type
annotation.

```python
import math

def factorial_limited(n: int, upper_limit: int) -> int:
    """
    Return the minimum between the factorial of `n` and `upper_limit`.

    >>> factorial_limited(3, 100), factorial_limited(4, 100), factorial_limited(5, 100)
    (6, 24, 100)
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
