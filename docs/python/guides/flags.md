---
title: Flags
layout: docs
sidenav: side-nav-python.html
type: markdown
---

# Flags

`absl.flags` defines a *distributed* command line system, replacing systems like
`getopt()`, `optparse` and manual argument processing. Rather than an
application having to define all flags in or near `main()`, each Python module
defines flags that are useful to it. When one Python module imports another,
it gains access to the other's flags. (This is implemented by having all modules
share a common, global registry object containing all the flag information.)

It includes the ability to define flag types (`boolean`, `float`, `integer`,
`list`), autogeneration of help (in both human and machine readable format) and
reading arguments from a file. It also includes the ability to automatically
generate man pages from the help flags.

Flags are defined through the use of one of the `DEFINE_xxx` functions. The
specific function used determines how the flag is parsed, checked, and
optionally type-converted, when it's seen on the command line.

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

*   `DEFINE_string`: takes any input, and interprets it as a string.
*   `DEFINE_bool` or `DEFINE_boolean`: typically does not take an argument: say
    `--myflag` to set `FLAGS.myflag` to `True`, or `--nomyflag` to set
    `FLAGS.myflag` to `False`. `--myflag=true` and `--myflag=false` are also
    supported, but not recommended.
*   `DEFINE_float`: takes an input and interprets it as a floating point number.
    Takes optional args lower_bound and upper_bound; if the number specified on
    the command line is out of range, it will raise a `FlagError`.
*   `DEFINE_integer`: takes an input and interprets it as an integer. Takes
    optional args lower_bound and upper_bound as for floats.
*   `DEFINE_enum`: takes a list of strings which represents legal values. If the
    command-line value is not in this list, raise a flag error. Otherwise,
    assign to `FLAGS.flag` as a string.
*   `DEFINE_list`: Takes a comma-separated list of strings on the commandline.
    Stores them in a Python list object.
*   `DEFINE_spaceseplist`: Takes a space-separated list of strings on the
    commandline. Stores them in a Python list object. Example: `--myspacesepflag
    "foo bar baz"`
*   `DEFINE_multi_string`: The same as DEFINE_string, except the flag can be
    specified more than once on the commandline. The result is a Python list
    object (list of strings), even if the flag is only on the command line once.
*   `DEFINE_multi_integer`: The same as DEFINE_integer, except the flag can be
    specified more than once on the commandline. The result is a Python list
    object (list of ints), even if the flag is only on the command line once.
*   `DEFINE_multi_enum`: The same as DEFINE_enum, except the flag can be
    specified more than once on the commandline. The result is a Python list
    object (list of strings), even if the flag is only on the command line once.

## Special Flags

There are a few flags that have special meaning:

*   `--help`: prints a list of all key flags (see below).
*   `--helpshort`: alias for `--help`.
*   `--helpfull`: prints a list of all the flags in a human-readable fashion.
*   `--helpxml`: prints a list of all flags, in XML format. DO NOT parse the
    output of `--helpfull` and `--helpshort`. Instead, parse the output of
    `--helpxml`. For more info, see "OUTPUT FOR --helpxml" below.
*   `--flagfile=foo`: read flags from file foo.
*   `--undefok=f1,f2`: ignore unrecognized option errors for f1,f2. For boolean
    flags, you should use `--undefok=boolflag`, and `--boolflag` and
    `--noboolflag` will be accepted. Do not use `--undefok=noboolflag`.
*   `--`: as in getopt(), terminates flag-processing.

## Implementation

`DEFINE_*` creates a `Flag` object and registers it with a `FlagValues` object
(typically the global FlagValues FLAGS, defined in `__init__.py`). The
`FlagValues` object can scan the command line arguments and pass flag arguments
to the corresponding `Flag` objects for value-checking and type conversion. The
converted flag values are available as attributes of the `FlagValues` object.

Code can access the flag through a `FlagValues` object, for instance
`flags.FLAGS.myflag`. Typically, the `__main__` module passes the command line
arguments to `flags.FLAGS` for parsing.

At bottom, this module calls `getopt()`, so getopt functionality is supported,
including short- and long-style flags, and the use of -- to terminate flags.

Methods defined by the flag module will throw `FlagsError` exceptions. The
exception argument will be a human-readable string.

## Additional features

### Flags Validators

If your program:

*   requires flag X to be specified,
*   needs flag Y to match a regular expression,
*   or requires any more general constraint to be satisfied

then validators are for you!

Each validator represents a constraint over one flag, which is enforced starting
from the initial parsing of the flags and until the program terminates.

Also, lower_bound and upper_bound for numerical flags are enforced using flag
validators.

#### Howto

If you want to enforce a constraint over one flag, use

```python
flags.register_validator(flag_name,
                         checker,
                         message='Flag validation failed',
                         flag_values=FLAGS)
```

After flag values are initially parsed, and after any change to the specified
flag, method checker(flag_value) will be executed. If constraint is not
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

### Note on --flagfile

Flags may be loaded from text files in addition to being specified on the
commandline.

Any flags you don't feel like typing, throw them in a file, one flag per line,
for instance:

    --myflag=myvalue
    --nomyboolean_flag

You then specify your file with the special flag `--flagfile=somefile`. You CAN
recursively nest `flagfile=` tokens OR use multiple files on the command line.
Lines beginning with a single hash '#' or a double slash '//' are comments in
your flagfile.

Any `flagfile=<file>` will be interpreted as having a relative path from the
current working directory rather than from the place the file was included from:
`myPythonScript.py --flagfile=config/somefile.cfg`

If `somefile.cfg` includes further `--flagfile=` directives, these will be
referenced relative to the original CWD, not from the directory the including
flagfile was found in!

The caveat applies to people who are including a series of nested files in a
different dir than they are executing out of. Relative path names are always
from CWD, not from the directory of the parent include flagfile. We do now
support '~' expanded directory names.

Absolute path names ALWAYS work!

## FAQs

### How to fix UnparsedFlagAccessError?

If an `UnparsedFlagAccessError` is raised, you are trying to access one of the
flags before flags library had a chance to parse command-line arguments.
Flags are not parsed at import time; they are parsed manually via
`FLAGS(list_of_args)` or as part of `app.run()`.

Here's a list of common mistakes and suggestions on how to fix them:

### Using flags in Python decorators

Python decorators are run before `app.run()` and thus you can not use flags as
direct arguments for decorators. One solution is to make the decorator support
callables.

#### Using flags for global variables/constants

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

### How to access some C++ flags from Python?

This section is forthcoming!
