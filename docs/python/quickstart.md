---
title: Python Abseil Quickstart
layout: docs
sidenav: side-nav-python.html
type: markdown
---

# Abseil Quickstart (Python)

This quick tutorial will get you up and running with Python Abseil. Please see
the [Programming Guides](/docs/python/guides) for details about specific modules.

## Prerequisites

Running the Abseil code within this tutorial requires the following:

* A compatible platform (e.g. Windows, Mac OS X, Linux, etc.). Most platforms
  are fully supported. Consult the
  [Platforms Guide](platforms/platforms) for more information.
* Python 2 or 3.
* [`pip`](https://pypi.org/project/pip/)
* [Git](https://git-scm.com/) for interacting with the Abseil source code
  repository, which is contained on [GitHub](http://github.com). To install Git,
  consult the [Set Up Git](https://help.github.com/articles/set-up-git/) guide
  on GitHub.

<p class="note">
Note: this Quickstart uses Bazel as the official build system for Abseil,
which is supported on most major platforms (Linux, Windows, MacOS, for example)
and compilers. The Abseil source code assumes you are using Bazel and contains
`BUILD.bazel` files for that purpose.
</p>

To install the Abseil Python package, simply run:

```sh
pip install absl-py
```

Or you can install from source via the instructions on
[github](https://github.com/abseil/abseil-py).

## Creating and Running a Script

Here's an example `hello.py` script that takes a user name and an optional
integer specifying the number of times to print the greeting.

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

### Running with Bazel

Now you can build and run your script using Bazel. To do this, you will need a
`WORKSPACE` file (simply adding an empty file named `WORKSPACE` in your Bazel
base directory is fine for this exercise) and a `BUILD` file with this build
rule:

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
..................

$ bazel-bin/hello --name=Daenerys
Hello, Daenerys!
```

Or alternatively you can run your application via a single `run` command:

```
$ bazel run :hello --name=Daenerys
```

For more information about Bazel Python Build Rules, consult the
[Bazel Documentation for Python](https://docs.bazel.build/versions/master/be/python.html)

## What's Next

* See the [Programming Guides](/docs/python/guides) for details about specific
modules.
