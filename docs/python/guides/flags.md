---
title: Flags
layout: docs
sidenav: side-nav-python.html
type: markdown
---

# Flags

`absl.flags` defines a *distributed* command line system, replacing systems like
`getopt()`, `optparse`, and manual argument processing. Rather than an
application having to define all flags in or near `main()`, each Python module
defines flags that are useful to it. When one Python module imports another,
it gains access to the other's flags. (This behavior is implemented by having
all modules share a common, global registry object containing all the flag
information.)

The Abseil flags library includes the ability to define flag types (`boolean`,
`float`, `integer`, `list`), autogeneration of help (in both human and machine
readable format) and reading arguments from a file. It also includes the ability
to automatically generate manual pages from the help flags.

Flags are defined through the use of `DEFINE_*` functions (where the flag's type
is used to define the value).

## Example Usage

```python
from absl import app
from absl import flags

FLAGS = flags.FLAGS

# Flag names are globally defined!  So in general, we need to be
# careful to pick names that are unlikely to be used by other libraries.
# If there is a conflict, we'll get an error at import time.
flags.DEFINE_string('name', 'Jane Random', 'Your name.')
flags.DEFINE_integer('age', None, 'Your age in years.', lower_bound=0)
flags.DEFINE_boolean('debug', False, 'Produces debugging output.')
flags.DEFINE_enum('job', 'running', ['running', 'stopped'], 'Job status.')


def main(argv):
  if FLAGS.debug:
    print('non-flag arguments:', argv)
  print('Happy Birthday', FLAGS.name)
  if FLAGS.age is not None:
    print('You are %d years old, and your job is %s' % (FLAGS.age, FLAGS.job))


if __name__ == '__main__':
  app.run(main)
```

## Flag Types

This is a list of the `DEFINE_*`'s that you can do. All flags take a name,
default value, help-string, and optional 'short' name (one-letter name). Some
flags have other arguments, which are described with the flag.

*   `DEFINE_string`: takes any input and interprets it as a string.
*   `DEFINE_bool` or `DEFINE_boolean`: typically does not take an argument: pass
    `--myflag` to set `FLAGS.myflag` to `True`, or `--nomyflag` to set
    `FLAGS.myflag` to `False`. `--myflag=true` and `--myflag=false` are also
    supported, but not recommended.
*   `DEFINE_float`: takes an input and interprets it as a floating point number.
    This also takes optional arguments `lower_bound` and `upper_bound`; if the
    number  specified on the command line is out of range, it raises a
    `FlagError`.
*   `DEFINE_integer`: takes an input and interprets it as an integer. This also
    takes optional arguments `lower_bound` and `upper_bound` as for floats.
*   `DEFINE_enum`: takes a list of strings that represents legal values. If the
    command-line value is not in this list, it raises a flag error; otherwise,
    it assigns to `FLAGS.flag` as a string.
*   `DEFINE_list`: Takes a comma-separated list of strings on the command line
    and stores them in a Python list object.
*   `DEFINE_spaceseplist`: Takes a space-separated list of strings on the
    commandline and stores them in a Python list object. For example:
    `--myspacesepflag "foo bar baz"`
*   `DEFINE_multi_string`: The same as `DEFINE_string`, except the flag can be
    specified more than once on the command line. The result is a Python list
    object (list of strings), even if the flag is only on the command line once.
*   `DEFINE_multi_integer`: The same as `DEFINE_integer`, except the flag can be
    specified more than once on the command line. The result is a Python list
    object (list of ints), even if the flag is only on the command line once.
*   `DEFINE_multi_enum`: The same as `DEFINE_enum`, except the flag can be
    specified more than once on the command line. The result is a Python list
    object (list of strings), even if the flag is only on the command line once.

## Special Flags

Some flags have special meanings:

*   `--help`: prints a list of all key flags (see below).
*   `--helpshort`: alias for `--help`.
*   `--helpfull`: prints a list of all the flags in a human-readable fashion.
*   `--helpxml`: prints a list of all flags, in XML format. *Do not* parse the
    output of `--helpfull` and `--helpshort`. Instead, parse the output of
    `--helpxml`.
*   `--flagfile=filename`: read flags from file *filename*.
*   `--undefok=f1,f2`: ignore unrecognized option errors for *f1*,*f2*. For
    boolean flags, you should use `--undefok=boolflag`, and `--boolflag` and
    `--noboolflag` will be accepted. Do not use `--undefok=noboolflag`.
*   `--`: as in getopt(). This terminates flag-processing.

## Implementation

`DEFINE_*` creates a `Flag` object and registers it with a `FlagValues` object
(typically the global FlagValues `FLAGS`, defined in `__init__.py`). The
`FlagValues` object can scan the command line arguments and pass flag arguments
to the corresponding `Flag` objects for value-checking and type conversion. The
converted flag values are available as attributes of the `FlagValues` object.

Code can access a flag through a `FlagValues` object, for instance
`flags.FLAGS.myflag`. Typically, the `__main__` module passes the command line
arguments to `flags.FLAGS` for parsing.  For example:

```python
FLAGS = flags.FLAGS

flags.DEFINE_string('myflag', 'Some default string', 'The value of myflag.')

def main(argv):
  if FLAGS.debug:
    print('non-flag arguments:', argv)
  print('The value of myflag is %s' % FLAGS.myflag)


if __name__ == '__main__':
  app.run(main)
```

At bottom, this module calls `getopt()`, so getopt functionality is supported,
including short- and long-style flags, and the use of `--` to terminate flags.

Methods defined by the flag module will throw `FlagsError` exceptions. The
exception argument will be a human-readable string.

## Additional Features

### Flags Validators

Validators are for you if your program:

*   requires flag X to be specified,
*   needs flag Y to match a regular expression, or
*   requires any more general constraint to be satisfied

Each validator represents a constraint over one flag, which is enforced starting
from the initial parsing of the flags and until the program terminates.

Also, `lower_bound` and `upper_bound` for numerical flags are enforced using
flag validators.

#### Registering Validators

If you want to enforce a constraint over one flag, use

```python
flags.register_validator(flag_name,
                         checker,
                         message='Flag validation failed',
                         flag_values=FLAGS)
```

After flag values are initially parsed, and after any change to the specified
flag, method checker(`flag_value`) will be executed. If constraint is not
satisfied, an `IllegalFlagValueError` exception will be raised. See
[`register_validator`'s
docstring](https://github.com/abseil/abseil-py/blob/master/absl/flags/_validators.py)
for a detailed explanation on how to construct your own checker.

#### Example Usage

```python
from absl import flags

FLAGS = flags.FLAGS

flags.DEFINE_integer('my_version', 0, 'Version number.')
flags.DEFINE_string('filename', None, 'Input file name.', short_name='f')

flags.register_validator('my_version',
                         lambda value: value % 2 == 0,
                         message='--my_version must be divisible by 2')
flags.mark_flag_as_required('filename')
```

### A Note About `--flagfile`

Flags may be loaded from text files in addition to being specified on the
commandline.

This means that you can throw any flags you don't feel like typing into a file,
listing one flag per line. For example:

```
--myflag=myvalue
--nomyboolean_flag
```

You then specify your file with the special flag `--flagfile=somefile`. You can
recursively nest `flagfile=` tokens or use multiple files on the command line.
Lines beginning with a single hash '#' or a double slash '//' are comments in
your flagfile.

Any `flagfile=<filename>` will be interpreted as having a relative path from the
current working directory rather than from the place the file was included from:
`myPythonScript.py --flagfile=config/somefile.cfg`

If `somefile.cfg` includes further `--flagfile=` directives, these will be
referenced relative to the original CWD, not from the directory the including
flagfile was found in!

The caveat applies to people who are including a series of nested files in a
different directory than that from which they execute. Relative path names are
always from `CWD` (current working directory), not from the directory of the
parent include flagfile.

Absolute path names ALWAYS work!

## FAQs

### How Do I fix UnparsedFlagAccessError?

If an `UnparsedFlagAccessError` is raised, you are trying to access one of the
flags before Abseil flags library has a chance to parse command line arguments.
Flags are not parsed at import time; they are parsed manually via
`FLAGS(list_of_arguments)` or as part of `app.run()`.

Here's a list of common mistakes and suggestions on how to fix them:

### Using Flags in Python Decorators

Python decorators are run before `app.run()` and thus you cannot use flags as
direct arguments for decorators. One solution is to make the decorator support
callable objects.

#### Using Flags for Global Variables/Constants

Assignment operations for module-level variables and constants are executed
during module import, before `app.run()`. It is recommended to wrap those
assignments in functions. For example:

```python
# Broken:
_OUTPUT_DIR = os.path.join(FLAGS.my_dir, 'my_subdir')
```

```python
# Proposed fix:
def _get_output_dir():
  return os.path.join(FLAGS.my_dir, 'my_subdir')
```

### How do I Access C++ flags from Python?

This section is forthcoming!
