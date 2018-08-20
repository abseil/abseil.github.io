---
title: Python Abseil Quickstart
layout: docs
sidenav: side-nav-python.html
type: markdown
---

# Abseil Quickstart (Python)

This quick tutorial will get you up and running with Python Abseil. Python
Abseil works with Python 2 and 3. Please see the
[Programming Guides](/docs/python/guides) for details about specific modules.

## Installation

To install the package, simply run:

```sh
pip install absl-py
```

Or you can install from source via the instructions on
[github](https://github.com/abseil/abseil-py).

## Creating and Running a Script

Here's an example `hello.py` script that takes a user name and optionally the
number of times to print it as input, then prints the greeting(s).

```python
from absl import app
from absl import flags

FLAGS = flags.FLAGS
flags.DEFINE_string("name", None, "Your name.")
flags.DEFINE_integer("num_times", 1,
                     "Number of times to print greeting.")

# Required flag.
flags.mark_flag_as_required("name")

def main(argv):
  del argv  # Unused.
  for i in range(0, FLAGS.num_times):
    print('Hello, %s!' % FLAGS.name)


if __name__ == '__main__':
  app.run(main)
```

You can then run your script with the command:

```
python hello.py --name=YOURNAME
```

### Running with Bazel

Alternatively, you can use Bazel to build and run your script. You will need a
`WORKSPACE` file and a `BUILD` file with a rule such as:

```
py_binary(
  name = "hello",
  deps = [],
  srcs = ["hello.py"],
)
```

You can then build and run your target:

```sh
$ cd /WORKSPACE_ROOT/
$ bazel build :hello
Starting local Bazel server and connecting to it...
INFO: Analysed target //:hello (13 packages loaded).
INFO: Found 1 target...
Target //:hello up-to-date:
  bazel-bin/hello
INFO: Elapsed time: 1.931s, Critical Path: 0.01s
INFO: 0 processes.
INFO: Build completed successfully, 4 total action

$ bazel-bin/hello --name=Daenerys
Hello, Daenerys!
```

Or alternatively run via a single command:

```
$ bazel run :hello --name=Daenerys
```

Please see the [C++ Quickstart Guide](/docs/cpp/quickstart.html) for more
details about using Bazel for building and running your code. For more
information about Bazel Python Build Rules, consult the
[Bazel Documentation](https://docs.bazel.build/versions/master/be/python.html)

## What's Next

* See the [Programming Guides](/docs/python/guides) for details about specific
modules.
