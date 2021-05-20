---
title: "The Abseil Flags Library"
layout: docs
sidenav: side-nav-cpp.html
type: markdown
---

# The Abseil Flags Library

The Abseil flags library allows programmatic access to flag values passed on the
command-line to binaries. The Abseil Flags library provides the following
features:

* Access to Abseil flags in a thread-safe manner
* Access to flag values that are valid at any point during a program's lifetime
* Prevention of conflicting flag names by ensuring uniqueness within the same
  binary
* Associated help text provided by a number of built-in usage flags
* Has type support for boolean, integral and string types, and is extensible to
  support other Abseil types and custom types
* Default values and programmatic access to flag values for both reading and
  writing
* Allows distributed declaration and definition of flags, though this usage
  has drawbacks and should generally be avoided.

Values for these flags are parsed from the command line by
`absl::ParseCommandLine()`. The resulting value for each flag is stored in a
global variable of an unspecified type `absl::Flag<T>`.

## Introduction

**Command-line flags** are flags that users typically specify on the command
line when they run an executable as runtime parameters. (These flags are often
referred to as *options* in the GNU world, such as within the `getopt()`
command-line argument parser.)

In the command:

```sh
$ fgrep -l -f /var/tmp/foo johannes brahms
```

*   `-l` are `-f` are *command-line flags*.
*   The `-f` flag contains one argument, `/var/tmp/foo` which is its
    *command-line flag argument*.
*   The `johannes` and `brahms` arguments, which are not associated with any
    command-line flag, are *command-line positional arguments*.

NOTE: unlike `getopt()`, the Abseil flags library does not support flags with
both short and long options (e.g. `-v` and `--verbose` as short and long
versions of the same command-line option).

Typically, an application lists what flags the user is allowed to pass in, and
what arguments they take. In this example, `-l` takes no argument, and `-f`
takes a string (in particular, a filename) as an argument. Users use a library
to help parse the command-line and store the flags in some data structure.

## Do I Need Command Line Flags?

In general, don't reach for flags. More often than not, flags are poor choices
for binary configuration. As global variables, it is difficult to avoid
conflicts with other flags, and difficult to deprecate and remove flags once
they are no longer useful. Some flag values end up being wasteful within your
binary: a flag with a single value that never varies is effectively a constant,
but one whose associated code paths can never be optimized, as they are runtime
initialized.

Often, flags interact with other flags to provide configuration to a binary. If
that configuration is reasonably complex, a configuration file is usually a
better option. That said, sometimes flags are appropriate.

A flag is reasonable if you know you will need to change the flag’s value, and
if the associated logic of the flag is self-contained. For example, a flag is
useful for:

* Toggling features: flags such as `--enforce_quota` can be changed
  when quota is causing a problem. When a new feature is being rolled
  out, you may want a simple way to switch it off in an emergency. However, make
  sure to remove these flags once their intended purpose has run its course.
* Platform dependence: specifying values that change in different environments,
  especially for input/output parameters: file paths, URLs, etc.
* Tuning parameters: batch sizes, timeouts, thresholds, etc.
* Debugging: a debugging flag may be desired to log information at runtime
  without changing user-visible behavior. For example, a logging flag may
  collect information if a server appears to be slow to respond.

All that said, many flags are strictly unnecessary. During one of our audits in
2012, we discovered that the majority of our flags never varied in value. Before
you reach for flags, consider whether you really need them, and for how long.

## Flags Best Practices

OK, we've warned you about flag usage. But if we accept that you do need flags
in your binary, what are some best practices around flag usage?

*   Prefer to define flags only in the file containing the binary's `main()`
    function. Although Abseil flags may be defined anywhere in any source file,
    avoid any usage outside of `main()` as it will otherwise be difficult to
    resolve conflicts.
*   Prefer to reference flags only from within the file containing the binary's
    `main()` function, for the same reason.
*   Do not use flags to implement any binary logic.
*   Do not declare any flags that you do not own yourself.
*   Do not access a binary's flags within any tight loops. Flags are expensive
    to read.
*   Prefer using flag types already defined in Abseil rather than implementing
    your own custom flag types.

With these caveats, the rest of this documentation discusses using the Abseil
Flags library API.

## Defining Flags

Use the `ABSL_FLAG(type, name, default, help-text)` macro to define a flag of
the appropriate type:

```cpp
#include "absl/flags/flag.h"
#include "absl/time/time.h"

ABSL_FLAG(bool, big_menu, true,
          "Include 'advanced' options in the menu listing");
ABSL_FLAG(std::string, output_dir, "foo/bar/baz/", "output file dir");
ABSL_FLAG(std::vector<std::string>, languages,
          std::vector<std::string>({"english", "french", "german"}),
          "comma-separated list of languages to offer in the 'lang' menu");
ABSL_FLAG(absl::Duration, timeout, absl::Seconds(30), "Default RPC deadline");
```

Flags defined with `ABSL_FLAG` will create global variables named
<code>FLAGS_<i>name</i></code> of the specified type and default value. Help
text will be displayed using the `--help` usage argument, if invoked. See
[Special Flags](#special_flags) for `--help` documentation.

### Standard Flags

Out of the box, the Abseil flags library supports the following types:

* `bool`
* `int16_t`
* `uint16_t`
* `int32_t`
* `uint32_t`
* `int64_t`
* `uint64_t`
* `float`
* `double`
* `std::string`
* `std::vector<std::string>`
* `absl::LogSeverity` (provided natively for layering reasons)

NOTE: support for integral types is implemented using overloads for
variable-width fundamental types (`short`, `int`, `long`, etc.). However, you
should prefer the fixed-width integral types listed above (`int32_t`,
`uint64_t`, etc.). -->

### Abseil Flags

In addition, several Abseil libraries provide their own custom support for
Abseil flags. Documentation for these formats is provided in the type's
`AbslParseFlag()` definition.

The Abseil [time library][time-library] provides the flag support for
absolute time values:

* `absl::Duration`
* `absl::Time`

The [civil-time library][civiltime-library] additionally provides flag support
for the following civil-time values:

* `absl::CivilSecond`
* `absl::CivilMinute`
* `absl::CivilHour`
* `absl::CivilDay`
* `absl::CivilMonth`
* `absl::CivilYear`

Additional support for Abseil types will be noted here as it is added.

See [Defining Custom Flag Types](#custom) for how to provide support for a new
type.

You can define a flag in any `.cc` file in your executable, but only define a
flag once! All flags should be defined outside any C++ namespace so if multiple
definitions of flags with the same name are linked into a single program the
linker will report an error. If you want to access a flag in more than one
source file, define it in a `.cc` file, and [declare](#declaring_flags) it in
the corresponding header file.

## Accessing Flags

A flag defined via `ABSL_FLAG` is available as a variable of an unspecified
type and named using the name passed to `ABSL_FLAG`. `absl::GetFlag()` and
`absl::SetFlag()` can be used to access such flags. E.g., for flags of type
`absl::Duration`:

```cpp
// Creates variable "absl::Flag<absl::Duration> FLAGS_timeout;"
// Example command line usage: --timeout=1m30s
ABSL_FLAG(absl::Duration, timeout, absl::Seconds(30), "Default RPC timeout");

// Read the flag
absl::Duration d = absl::GetFlag(FLAGS_timeout);

// Modify the flag
absl::SetFlag(&FLAGS_timeout, d + absl::Seconds(10));
```

Accesses to `ABSL_FLAG` flags are thread-safe.

## Using a Flag in a Different File {#declaring_flags}

Accessing a flag in the manner of the previous section only works if the flag
was defined earlier in the same `.cc` file. If it wasn't, you'll get an
'unknown variable' error.

If you need to allow other modules to access the flag, you must export it in
some header file that is included by those modules. For an `ABSL_FLAG` flag
named `FLAGS_name` of type `T`, use the `ABSL_DECLARE_FLAG(T, name);` macro to
do so:

```cpp
ABSL_DECLARE_FLAG(absl::Duration, timeout);
```

The declaration should always be placed in the header file associated with the
`.cc` file that defines and owns the flag, as with any other exported entities.
If you need to do this for testing only, you can place it with an
`// Exposed for testing only` comment.

Warning: The necessity to access flags from different files, especially in
libraries, is generally a sign of a bad design. Given the "global variable"
nature of flags they should be avoided in libraries and be injected instead
(e.g. in constructors). (see
[abseil.io/tips/45](https://abseil.io/tips/45))

## Validating Flag Values

Some flag values may be invalid. E.g., the underlying type may have a larger
range than desired for the flag.

For `ABSL_FLAG` flags, extra checks on a flag value can be done by providing a
custom type and adding appropriate validation to the corresponding
`AbslParseFlag()` function, which defines how a particular flag should be
parsed.

Example:

```c++
#include <string>

#include "absl/flags/flag.h"
#include "absl/flags/marshalling.h"
#include "absl/strings/string_view.h"

struct PortNumber {
  explicit PortNumber(int p = 0) : port(p) {}

  int port;  // Valid range is [0..32767]
};

// Returns a textual flag value corresponding to the PortNumber `p`.
std::string AbslUnparseFlag(PortNumber p) {
  // Delegate to the usual unparsing for int.
  return absl::UnparseFlag(p.port);
}

// Parses a PortNumber from the command line flag value `text`.
// Returns true and sets `*p` on success; returns false and sets `*error`
// on failure.
bool AbslParseFlag(absl::string_view text, PortNumber* p, std::string* error) {
  // Convert from text to int using the int-flag parser.
  if (!absl::ParseFlag(text, &p->port, error)) {
    return false;
  }
  if (p->port < 0 || p->port > 32767) {
    *error = "not in range [0,32767]";
    return false;
  }
  return true;
}

ABSL_FLAG(PortNumber, port, PortNumber(0), "What port to listen on");
```

If `AbslParseFlag()` returns false for a value specified on the command-line,
the process will exit with an error message. Note that `AbslParseFlag()` does
not initiate any parsing itself, but simply defines the parsing behavior.

## Parsing Flags During Startup

Command-line flags should be parsed at startup, preferably before any other
business logic associated with your binary. To do so:

```cpp
absl::ParseCommandLine(argc, argv);
```

`absl::ParseCommandLine()` parses the set of command-line arguments passed in
the `argc` (argument count) and `argv[]` (argument vector) parameters from
`main()`, assigning values to any defined Abseil flags. (Any arguments passed
after the flag-terminating delimiter (`--`) are treated as positional arguments
and ignored.)

Any command-line flags (and arguments to those flags) are parsed into Abseil
Flag values, if those flags are defined. Any undefined flags will either
return an error, or be ignored if that flag is designated using `--undefok` to
indicate "undefined is OK."

Any command-line positional arguments not part of any command-line flag (or
arguments to a flag) are returned in a vector, with the program invocation
name at position 0 of that vector. (Note that this includes positional
arguments after the flag-terminating delimiter `--`.)

After all flags and flag arguments are parsed, this function looks for any
built-in usage flags (e.g. `--help`), and if any were specified, it reports
help messages and then exits the program. If command-line flags fail to pass
parsing and validation, the process will be terminated.

## Setting Flags on the Command Line

The reason you make something a flag instead of a compile-time constant, is to
allow users to specify a non-default value on the command-line. Here's how they
might do it for an application that links in `foo.cc`:

```sh
app_containing_foo --nobig_menu --languages="chinese,japanese,korean" ...
```

This sets `FLAGS_big_menu = false;` and `FLAGS_languages =
"chinese,japanese,korean"`, when `ParseCommandLine()` is run.

Note the atypical syntax for setting a boolean flag to false: putting "no" in
front of its name. There's a fair bit of flexibility to how flags may be
specified. Here's an example of all the ways to specify the "languages" flag:

-   `app_containing_foo --languages="chinese,japanese,korean"`
-   `app_containing_foo -languages="chinese,japanese,korean"`
-   `app_containing_foo --languages "chinese,japanese,korean"`
-   `app_containing_foo -languages "chinese,japanese,korean"`

For boolean flags, the possibilities are slightly different:

-   `app_containing_foo --big_menu`
-   `app_containing_foo --nobig_menu`
-   `app_containing_foo --big_menu=true`
-   `app_containing_foo --big_menu=false`

(as well as the single-dash variant on all of these).

Despite this flexibility, we recommend using only a single form:
`--variable=value` for non-boolean flags, and `--variable/--novariable` for
boolean flags. This consistency will make your code more readable.

It is a fatal error to specify a flag on the command-line that has not been
defined somewhere in the executable. If you need that functionality for some
reason -- say you want to use the same set of flags for several executables, but
not all of them define every flag in your list -- you can specify
[--undefok](#special_flags) to suppress the error.

If a flag is specified more than once, only the last specification is used; the
others are ignored.

Note that Abseil flags do not have single-letter synonyms, like they do in the
`getopt()` library, nor do we allow "combining" flags behind a single dash, as
in `ls -laf`.

## Changing the Default Flag Value

Sometimes a flag is defined in a library, and you want to change its default
value in one application but not others. To do so, you can use `absl::SetFlag()`
to override this default value before calling `ParseCommandLine()`; if the
user does not pass a value on the command line, this new default will be used:

```cpp
int main(int argc, char** argv) {
  // Overrides the default for FLAGS_logtostderr
  absl::SetFlag(&FLAGS_logtostderr, true);
  // If the command-line contains a value for logtostderr, use that. Otherwise,
  // use the default (as set above).
  absl::ParseCommandLine(argc, argv);
}
```

Note that setting the flag *after* parsing the command-line is neither generally
useful nor recommended, as it will ignore the user's intentions with a
command-line flag and essentially set the flag as a constant value.

## Removing / Retiring Flags

When a flag is no longer useful (and no longer referenced in code), in some
cases it may be possible to simply remove the definition. However, if the flag
is referenced in configuration files, job launching scripts, and the like,
simply removing the definition will cause problems for deployment. For flags
referenced in complex deployments where a single configuration may be used with
multiple builds, it can be impossible to satisfy all constraints. To handle
these cases where timing and coordination are difficult, you can denote some
flags as "retired" flags via `ABSL_RETIRED_FLAG()`.

```cpp
ABSL_RETIRED_FLAG(bool, old_bool_flag, true, "old description");
```

Retired flags have a number of important behaviors. Specifically, they:

-   do not define a C++ `FLAGS_` variable.
-   have a type and a value, but that value is intentionally inaccessible.
-   do not appear in `--help` messages.
-   are fully supported by _all_ flag parsing routines.
-   consume args normally, and complain about type mismatches in those
    arguments.
-   emit a complaint but do not die if they are accessed by name through the
    flags API for parsing or otherwise.

In this way, you can safely remove flags that are used in (multiple) complex
deployments: retire the flag, wait for releases of affected binaries, then
remove reference to the flag from configuration files and startup scripts. Once
all jobs are starting up without logging warnings about reference to the retired
flag, the retired flag can be removed completely.

For more details, see the [Tip of the Week on retired flags][retired-flags].

## Special Usage Flags {#special_flags}

There are a few flags defined by the Abseil flags library itself. These usage
flags are reserved words and should not be declared by anyone other than the
Abseil team, just like any other flags which you don't own. Usage flags, if
invoked, cause the application to print some information about itself and exit.

```text
--help            show help on important flags for this binary
--helpfull        shows all flags from all files, sorted by file and then
                  by name; shows the flagname, its default value, and its
                  help string
--helpshort       shows only flags for the file with the same name as the
                  executable (usually the one containing main())
--helpon=FILE     shows only flags defined in FILE.*
--helpmatch=S     shows only flags defined in *S*.*
--helppackage     shows flags defined in files in same directory as main()
--version         prints version info for the executable
```
NOTE: The help message for a flag will include its default value, so in most cases there is no need to mention the default value in the definition of a flag's `help-text`.

Additionally, some built-in flags have additional behavioral effects. These are
noted below.

### `--undefok`

The Abseil flags library also supports an `undefok` flag:

`--undefok=flagname,flagname,...`

For any listed `flagname`, this instructs the Abseil flags library to suppress
normal error signaling that occurs when `--flagname` is seen on the command-line
(or `--noflagname` since a listed flag might have been an old boolean flag), but
no flag with name `flagname` has been defined.

## Defining Custom Flag Types {#custom}

For a type `T` to be used as an Abseil flag type, it must support conversion to
and from strings supplied on the command-line. Custom types may have a unique
format for this command-line string, and hence may require custom support for
Abseil flags.

To add support for your user-defined type, add overloads of `AbslParseFlag()`
and `AbslUnparseFlag()` as free (non-member) functions to your type. If `T`
is a class type, these functions can be friend function definitions. These
overloads must be added to the same namespace where the type is defined, so
that they can be discovered by Argument-Dependent Lookup (ADL).

Example:

```cpp
namespace foo {
enum class OutputMode { kPlainText, kHtml };

// AbslParseFlag converts from a string to OutputMode.
// Must be in same namespace as OutputMode.

// Parses an OutputMode from the command line flag value `text`. Returns
// `true` and sets `*mode` on success; returns `false` and sets `*error`
// on failure.
bool AbslParseFlag(absl::string_view text,
                   OutputMode* mode,
                   std::string* error) {
  if (text == "plaintext") {
    *mode = OutputMode::kPlainText;
    return true;
  }
  if (text == "html") {
    *mode = OutputMode::kHtml;
    return true;
  }
  *error = "unknown value for enumeration";
  return false;
}

// AbslUnparseFlag converts from an OutputMode to a string.
// Must be in same namespace as OutputMode.

// Returns a textual flag value corresponding to the OutputMode `mode`.
std::string AbslUnparseFlag(OutputMode mode) {
  switch (mode) {
    case OutputMode::kPlainText: return "plaintext";
    case OutputMode::kHtml: return "html";
    default: return absl::StrCat(mode);
  }
}
}  // namespace foo
```

Notice that neither `AbslParseFlag()` nor `AbslUnparseFlag()` are class
members, but free functions. `AbslParseFlag/AbslUnparseFlag()` overloads
for a type should only be declared in the same file and namespace as said
type. The proper `AbslParseFlag/AbslUnparseFlag()` implementations for a
given type will be discovered via Argument-Dependent Lookup (ADL).

`AbslParseFlag()` may need, in turn, to parse simpler constituent types
using `absl::ParseFlag()`. For example, a custom struct `MyFlagType`
consisting of a `std::pair<int, std::string>` would add an `AbslParseFlag()`
overload for its `MyFlagType` like so:

Example:

```cpp
namespace my_flag_namespace {

struct MyFlagType {
  std::pair<int, std::string> my_flag_data;
};

bool AbslParseFlag(absl::string_view text, MyFlagType* flag,
                   std::string* err);

std::string AbslUnparseFlag(const MyFlagType&);

// Within the implementation, `AbslParseFlag()` will, in turn invoke
// `absl::ParseFlag()` on its constituent `int` and `std::string` types
// (which have built-in Abseil flag support.

bool AbslParseFlag(absl::string_view text, MyFlagType* flag,
                   std::string* err) {
  std::pair<absl::string_view, absl::string_view> tokens =
      absl::StrSplit(text, ',');
  if (!absl::ParseFlag(tokens.first, &flag->my_flag_data.first, err))
    return false;
  if (!absl::ParseFlag(tokens.second, &flag->my_flag_data.second, err))
    return false;
  return true;
}

// Similarly, for unparsing, we can simply invoke `absl::UnparseFlag()` on
// the constituent types.
std::string AbslUnparseFlag(const MyFlagType& flag) {
  return absl::StrCat(absl::UnparseFlag(flag.my_flag_data.first),
                      ",",
                      absl::UnparseFlag(flag.my_flag_data.second));
}
}  // my_flag_namespace
```

### Best Practices for Defining Custom Flag Types

*   Declare `AbslParseFlag()` and `AbslUnparseFlag()` in exactly one place for
    `T`, generally in the same file that declares `T`. If `T` is a class type,
    they can be defined with [friend _function-definitions_][friend-functions].
*   If you must declare `AbslParseFlag()` and `AbslUnparseFlag()` away from
    `T`'s declaration, you must still be the owner of `T` and must guarantee
    that the functions are defined exactly once in the codebase.
*   Document the format string of the flag where you declare `AbslParseFlag()`
    and `AbslUnparseFlag()`. As the owner of `T`, you are responsible for
    documenting this format.
*   `absl::StrSplit("")` returns `{""}` (a list with one element), so watch out
    for that if you are defining a compound flag type. Flags defined with
    `ABSL_FLAG(std::vector<std::string>, ...)` treat an empty string as an empty
    container.
*   Escape separators if they can occur in values for compound flag types.
*   Invoke `absl::ParseFlag()` and `absl::UnparseFlag()` within your free
    function overloads to get the string conversion behavior implemented for
    constituent built-in types.
*   Only boolean flags are allowed to not pass a value: e.g. `--enable_foo` or
    `--noenable_foo`. As a result, all custom flag types require an explicit
    value to be passed to `AbslParseFlag()` and `AbslUnparseFlag()`, even if
    that value is the empty string (e.g. `--my_custom_flag=""`).

[retired-flags]: https://abseil.io/tips/90
[friend-functions]: http://en.cppreference.com/w/cpp/language/friend
[time-library]: time.md#time-durations
[civiltime-library]: time.md#civil-times
