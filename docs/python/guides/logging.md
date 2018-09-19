---
title: Logging
layout: docs
sidenav: side-nav-python.html
type: markdown
---

# Logging

Abseil has its own library for logging in Python. It is implemented on top of
the standard logging module in Python (described in
[PEP282](http://legacy.python.org/dev/peps/pep-0282/)), which is good if you're
already familiar with that library. This section mentions the basics of Abseil's
logging library. See the [source](https://github.com/abseil/abseil-py/blob/master/absl/logging/__init__.py)
for more details.

**Dependencies:**

```python
from absl import logging
```

**Example code:**

```python
logging.info('Interesting Stuff')
logging.info('Interesting Stuff with Arguments: %d', 42)

logging.set_verbosity(logging.INFO)
logging.log(logging.DEBUG, 'This will *not* be printed')
logging.set_verbosity(logging.DEBUG)
logging.log(logging.DEBUG, 'This will be printed')

logging.warning('Worrying Stuff')
logging.error('Alarming Stuff')
logging.fatal('AAAAHHHHH!!!!')  # Process exits
```

**Log levels:**

*   `logging.FATAL`
*   `logging.ERROR`
*   `logging.WARNING`
*   `logging.INFO`
*   `logging.DEBUG`

**Functions:**

*   `fatal(msg, *args)`
*   `error(msg, *args)`
*   `warning(msg, *args)`
*   `info(msg, *args)`
*   `debug(msg, *args)`
*   `vlog(level, msg, *args)`
*   `exception(msg, *args)`
