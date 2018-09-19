---
title: app.py
layout: docs
sidenav: side-nav-python.html
type: markdown
---

# `app.py`

`app.py` is the generic entry point for Abseil Python applications. This is a
key difference from how python applications are typically run, where you
identify a specific file as the entry point, e.g., `$ python my_app.py`. When
you run your application via Bazel, Bazel automatically determines the
entry point by searching for `app.run()` within a build rule's source files.

When the program starts, `app.run()` parses the flags, printing a usage message
and failing if illegal flags or flag values are specified.

For example, if you have a file called `hello.py` that calls `app.run()`:

```python
from absl import app
from absl import flags

FLAGS = flags.FLAGS

flags.DEFINE_string('name', 'Jane Random', 'Your name.')

def main(argv):
  if FLAGS.debug:
    print('non-flag arguments:', argv)
  print('Happy, ', FLAGS.name)


if __name__ == '__main__':
  app.run(main)
```

and you have a bazel build rule such as:

```
py_binary(
  name = "hello",
  deps = [],
  srcs = ["hello.py"],
)
```

You could then run your target as follows:

```sh
$ cd /WORKSPACE_ROOT/
$ bazel run :hello
```

When using `app.py`'s `run()` to start your program, C++ flags will
automatically be available.
