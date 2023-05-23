---
title: "The Abseil Logging Library"
layout: docs
sidenav: side-nav-cpp.html
type: markdown
---

# The Abseil Logging Library

The Abseil Logging library provides facilities for writing short text messages
about the status of a program to `stderr`, disk files, or other sinks (via an
extension API).

## API Overview {#API}

The `LOG()` and `CHECK()` macro families are the core of the API. Each forms the
beginning of a statement that additional data may optionally be streamed into
just like `std::cout`.

All data streamed into a single macro will be concatenated and written to the
logfiles as a single message with a [prefix](#prefix) formed from metadata
(time, file/line, etc.). In particular, and unlike `std::cout`, the library
supplies a newline at the end of each message, so you shouldn't generally end
logging statements with `\n` or `std::endl`. Any newlines that *are* streamed in
will show up in the logfiles.

For more detailed information, see the header files.

### `LOG()` Macro {#LOG}

`LOG()` takes a severity level as an argument, which defines the granularity and
type of logging information to log. The four basic severity levels are `INFO`,
`WARNING`, `ERROR`, and `FATAL`. `FATAL` is not named idly; it causes the
logging library to terminate the process after recording the streamed message.
See below for more about [severity levels](#severity), including best practices
for picking one.

```c++
LOG(INFO) << "Hello world!";
```

This will produce a message in the logs like:

```
I0926 09:00:00.000000   12345 foo.cc:10] Hello world!
```

The format of the metadata is documented [below](#prefix).

### `CHECK()` Macro {#CHECK}

`CHECK()` is an assertion. Its severity is always `FATAL`, so its only argument
is a condition that *should* be true. If it isn't, `CHECK()` writes to the log
and terminates the process. It's active in **all build modes** (unlike the C
`assert()` macro) and logs failures to the application logs in the same way as
`LOG()` but with additional information about what failed and where.

Like `FATAL`, a `CHECK()` assertion should be used sparingly (especially in
server code) and only in cases where it is preferable to actually terminate the
process rather than attempt recovery: e.g. no recovery is possible, or memory
corruption could damage user data. Note that you should also be aware of where
your code may be running; a `CHECK()` in a commandline utility or batch
processing job needs less caution than a `CHECK()` in a user-facing service. If
you are unsure where your code will run (if you are writing a utility library,
for example), be conservative and assume it will be used in production-facing
services and should avoid `CHECK()` where possible.

```c++
CHECK(!filenames_sorted.empty()) << "no files matched";
ProcessFile(filenames_sorted.front());
```

This will produce a message in the logs like:

```
F0926 09:00:01.000000   12345 foo.cc:100] Check failed: !filenames_sorted.empty() no files matched
E0926 09:00:01.150000   12345 process_state.cc:1133] *** SIGABRT received by PID 12345 (TID 12345) on cpu 0 from PID 12345; stack trace: ***
E0926 09:00:01.250000   12345 process_state.cc:1136] PC: @     0xdeadbeef  (unknown)  raise
    @     0xdeadbeef       1920  FailureSignalHandler()
    @     0xdeadc0w5    2377680  (unknown)
(more stack frames follow)
```

Note that this log entry uses the prefix `F` for a severity level of `FATAL`.
The text of the condition itself is logged before the streamed operands.
Additionally, a stack trace is logged at severity `ERROR` (on lines prefixed
with `E`) after the `FATAL` message but before the process terminates.

Special two-argument forms spelled `CHECK_EQ()`, `CHECK_GT()`, `CHECK_STREQ()`
(for `char*` strings), etc. can be used to make assertions about comparisons
between streamable, comparable types. In addition to the text of the arguments,
these forms log the actual values of the arguments.

```c++
int x = 3, y = 5;
CHECK_EQ(2 * x, y) << "oops!";
```

This will produce a message in the logs like:

```
F0926 09:00:02.000000   12345 foo.cc:20] Check failed: 2 * x == y (6 vs. 5) oops!
```

### Alternate Macro Names for Interoperability

Abseil provides alternative macro names prefixed with `ABSL_` (e.g. `ABSL_LOG`)
for the benefit of projects that need them.  These macros are provided in
separate `absl_log.h` and `absl_check.h` header files.  Both names are identical
and are equally supported.

We expect most libraries to avoid logging in headers, and most projects to use
only one logging framework.  In these cases, the shorter names tend to be more
convenient and readable, which is especially valuable for macros used as heavily
as these tend to be.

### Severity Levels {#severity}

The `absl::LogSeverity` type represents severity levels. `LOG()`'s parameter is
actually not of this type, or of *any* type. Some [macro tricks](#hygiene) are
used to make `LOG(ERROR)` work without using a macro or global symbol named
`ERROR`. This is necessary because `ERROR` is defined by some popular
third-party packages (e.g. Microsoft Windows) and cannot be redefined.

There are four proper severity levels:

*   `INFO` corresponds to `absl::LogSeverity::kInfo`. It describes *expected*
    events that are important for understanding the state *of the program* but
    which are not indicative of a problem. Libraries, especially low-level
    common libraries, should use this level sparingly lest they spam the logs of
    every program that uses them.<br />
*   `WARNING` corresponds to `absl::LogSeverity::kWarning`. It describes
    unexpected events which *may* indicate a problem.
*   `ERROR` corresponds to `absl::LogSeverity::kError`. It describes unexpected
    problematic events that the program is able to recover from. `ERROR`
    messages should be actionable, meaning that they should describe actual
    problems with the software or its configuration (and not e.g. with user
    input) and the combination of the message, the file name and line number,
    and surrounding messages should be sufficient to at least understand the
    event being reported.<br />
*   `FATAL` corresponds to `absl::LogSeverity::kFatal` and is the implicit
    severity level for `CHECK` failures. It describes unrecoverable problems.
    Logging at this level terminates the process. The `FATAL` logging level
    should be used sparingly and carefully in services, especially user-facing
    services, and in library code that may be included in such services. Each
    fatal log is a potential outage if a significant fraction of the serving
    jobs hit it at once.<br />
    Fatal logging is more often appropriate for developer tools, some batch
    jobs, and failures at job startup. That said, process termination and
    outages are always preferable to undefined behavior (which could include
    user data corruption and/or a security or privacy incident), so `FATAL` is
    sometimes appropriate even in server and library code as a last resort in
    response to unexpected behavior that cannot be handled any other way.

There is also one pseudo-level:

*   `QFATAL` ("quiet fatal") does not have a corresponding `absl::LogSeverity`
    value. It behaves like `FATAL` except that no stack trace is logged and
    `atexit()` handlers are not run. It is usually the best choice for errors
    occurring at startup (e.g. flag validation) where the control flow is
    uninteresting and unnecessary to diagnosis.

If you want to specify a severity level using a C++ expression, e.g. so that the
level used varies at runtime, you can do that too:

```c++
LOG(LEVEL(MoonPhase() == kFullMoon ? absl::LogSeverity::kFatal
                                     : absl::LogSeverity::kError))
      << "Spooky error!";
```

### Other Macro Variants {#macros}

The logging API contains a number of additional macros for special cases.

*   `QCHECK()` works like `CHECK()` but with the same variations as `QFATAL` vs.
    `FATAL`: it does not log a stack trace or run `atexit()` handlers on
    failure.

    ```c++
    int main (int argc, char**argv) {
      absl::ParseCommandLine(argc, argv);
      QCHECK(!absl::GetFlag(FLAGS_path).empty()) << "--path is required";
      ...
    ```

*   `PLOG()` and `PCHECK()` automatically append a string describing `errno` to
    the logged message. They are useful with system library calls that set
    `errno` on failure to indicate the nature of the failure. Their names are
    intended to be consistent with the `perror` library function.

    ```c++
    const int fd = open(path.c_str(), O_RDONLY);
    PCHECK(fd != -1) << "Failed to open " << path;

    const ssize_t bytes_read = read(fd, buf, sizeof(buf));
    PCHECK(bytes_read != -1) << "Failed to read from " << path;

    const int close_ret = close(fd);
    if (close_ret == -1) PLOG(WARNING) << "Failed to close " << path;
    ```

*   `DLOG()` ("debug log") and `DCHECK()` disappear from the binary completely
    in optimized builds. Note that `DLOG(FATAL)` and `DCHECK()` have very
    different semantics from `LOG(DFATAL)`.<br />
    Debug logging is helpful for information that's useful when debugging tests
    but expensive to collect (e.g. acquiring a contended lock) in production:

    ```c++
    DLOG(INFO) << server.State();
    ```

    Be careful with `DCHECK()`; if it's worth checking in tests it's probably
    worth checking in production too:

    ```c++
    DCHECK(ptr != nullptr);
    ptr->Method();
    ```

    `DCHECK` can sometimes be useful for checking invariants in very hot
    codepaths, where checks in tests must be assumed to validate behavior in
    production.<br />
    Just like `assert()`, be sure not to rely on evaluation of side-effects
    inside `DCHECK` and `DLOG` statements:

    ```c++ {.bad}
    DCHECK(server.Start());
    // In an optimized build, no attempt will have been made to start the
    // server!
    ```

*   `LOG_IF()` adds a condition parameter and is equivalent to an `if`
    statement. As with `if` and the ternary operator, the condition will be
    contextually converted to `bool`. `PLOG_IF()` and `DLOG_IF()` variants also
    exist.

    ```c++
    LOG_IF(INFO, absl::GetFlag(FLAGS_dry_run))
        << "--dry_run set; no changes will be made";
    ```

*   `LOG_EVERY_N()`, `LOG_FIRST_N()`, `LOG_EVERY_N_SEC()`, and
    `LOG_EVERY_POW_2()` add more complicated conditions that can't be easily
    replicated with a simple `if` statement. Each of these maintains a
    per-statement state object in static storage that's used to determine
    whether it's time to log again. They are thread-safe.<br />
    The token `COUNTER` may be streamed into these; it will be replaced by a
    monotonically increasing count of the number of times execution has passed
    through this statement, including both the times when logging happened and
    the times when it did not. Macro variants with an added condition (e.g.
    `LOG_IF_EVERY_N()`) also exist, as do many combinations with `VLOG()`,
    `PLOG()`, and `DLOG()`.

    ```c++
    LOG_EVERY_N(WARNING, 1000) << "Got a packet with a bad CRC (" << COUNTER
                               << " total)";
    ```

### Mutator Methods {#mutators}

The `LOG()` and `CHECK()` macros support some chainable methods that alter their
behavior.

*   `.AtLocation(absl::string_view file, int line)`<br />
    Overrides the location inferred from the callsite. The string pointed to by
    `file` must be valid until the end of the statement.
*   `.NoPrefix()`<br />
    Omits the [prefix](#prefix) from this line. The prefix includes metadata
    about the logged data such as source code location and timestamp.
*   `.WithTimestamp(absl::Time timestamp)`<br />
    Uses the specified timestamp instead of one collected at the time of
    execution.
*   `.WithThreadID(absl::LogEntry::tid_t tid)`<br />
    Uses the specified thread ID instead of one collected at the time of
    execution.
*   `.WithMetadataFrom(const absl::LogEntry &entry)`<br />
    Copies all metadata (but no data) from the specified `absl::LogEntry`.<br />
    This can be used to change the severity of a message, but it has some
    limitations:
    *   `ABSL_MIN_LOG_LEVEL` is evaluated against the severity passed into `LOG`
        (or the implicit `FATAL` level of `CHECK`).
    *   `LOG(FATAL)` and `CHECK` terminate the process unconditionally, even if
        the severity is changed later.
*   `.WithPerror()`<br />
    Appends to the logged message a colon, a space, a textual description of the
    current value of `errno` (as by `strerror(3)`), and the numerical value of
    `errno`. The result is comparable to `PLOG()` and `PCHECK()`.
*   `.ToSinkAlso(absl::LogSink* sink)`<br />
    Sends this message to `*sink` in addition to whatever other sinks it would
    otherwise have been sent to. `sink` must not be null.
*   `.ToSinkOnly(absl::LogSink* sink)`<br />
    Sends this message to `*sink` and no others. `sink` must not be null.

## Logged Message Output {#output}

### Log Line Format {#prefix}

Each message is logged with metadata of the following form:

```
I0926 09:00:00.000000   12345 foo.cc:10] Hello world!
```

The prefix starts with an `I`, representing the `INFO` severity level, combined
with a date, `0926`. The time follows, with microseconds, in the machine's local
timezone. `12345` is a thread ID number. `foo.cc:10` is the source code
location where the `LOG()` statement appears, and the bracket and space are a
fixed delimiter before the message itself.

The prefix can be suppressed globally with the `--nolog_prefix` flag or for a
single message the `.NoPrefix()` [mutator method](#mutators).

### `absl::LogSink` {#LogSink}

`absl::LogSink` is an extension point for processing logged messages, such as by
writing them to a disk file.  A single message can be directed to it with the
`.ToSinkOnly()` or `.ToSinkAlso()` [mutator methods](#mutators), or a sink can
be registered to observe all logged messages (except those logged with
`.ToSinkOnly()`) with `absl::AddLogSink()` and unregistered with
`absl::RemoveLogSink`.  For example:

```c++
class LinePrinterLogSink : public absl::LogSink {
 public:
  LinePrinterLogSink() : fp_(fopen("/dev/lp0", "a")) {
    PCHECK(fp_ != nullptr) << "Failed to open /dev/lp0";
  }
  ~LinePrinterLogSink() {
    fputc('\f', fp_);
    PCHECK(fclose(fp_) == 0) << "Failed to close /dev/lp0";
  }
  void Send(const absl::LogEntry& entry) override {
    for (absl::string_view line :
         absl::StrSplit(entry.text_message_with_prefix(), absl::ByChar('\n'))) {
      // Overprint severe entries for emphasis:
      for (int i = static_cast<int>(absl::LogSeverity::kInfo);
           i <= static_cast<int>(entry.log_severity()); i++) {
        absl::FPrintF(fp_, "%s\r", line);
      }
      fputc('\n', fp_);
    }
  }

 private:
  FILE* const fp_;
};
```

A `LogSink` receives two copies of each `FATAL` message: one without a
stacktrace, and then one with. This quirk allows some diagnostic data to be
observed even if stacktrace collection fails or takes too long. The process will
terminate once the `LogSink` returns, i.e., there's no need for the sink to call
`abort()`.

Any logging that takes place in a registered `LogSink` or in a function called
by a registered `LogSink` is sent only to `stderr` and not to any registered
`LogSink`s so as to avoid infinite recursion.

### `stderr` Output {#stderr}

A `LogSink` that writes to `stderr` is included and registered by default.
globals.h declares some knobs that control which severity levels this sink
writes to stderr and which it discards.

## Configuration and Flags

There are a small number of runtime configuration knobs with accessors in
globals.h.  An optional `:flags` target is provided which defines Abseil flags
that control these knobs from the command-line.  If this target is not linked
in, logging does not depend on Abseil flags (nor vice-versa).

If `ABSL_MIN_LOG_LEVEL` is defined as a preprocessor macro at build-time,
logging at any severity less than its value (converted to `absl::LogSeverity`)
is removed and fatal statements (e.g. `CHECK`, `LOG(FATAL)`) terminate silently.
Expressions in logged messages are not evaluated, and string literals streamed
to such statements are typically stripped as dead code.  If this stripping is to
be relied upon, the unit tests in stripping_test.cc should be run regularly with
the toolchain and flags as the build you want stripped.  This behavior is beyond
the scope of what's guaranteed by the C++ standard, so it cannot be guaranteed
by Abseil.

## FAQ {#FAQ}

### How do I make my type streamable into `LOG()`? {#streaming}

For a class type, define an `AbslStringify()` overload as a `friend` function
template for your type. The logging library will check for such an overload when
formatting user-defined types.

```cpp
namespace foo {

class Point {
  ...
  template <typename Sink>
  friend void AbslStringify(Sink& sink, const Point& point) {
    absl::Format(&sink, "(%d, %d)", point.x, point.y);
  }

  int x;
  int y;
};

// If you can't declare the function in the class it's important that the
// AbslStringify overload is defined in the SAME namespace that defines Point.
// C++'s lookup rules rely on that.
enum class EnumWithStringify { kMany = 0, kChoices = 1 };

template <typename Sink>
void AbslStringify(Sink& sink, EnumWithStringify e) {
  absl::Format(&sink, "%s", e == EnumWithStringify::kMany ? "Many" : "Choices");
}

}  // namespace foo
```

`AbslStringify()` can also use `absl::StrFormat`'s catch-all `%v` type specifier
within its own format strings to perform type deduction. `Point` above could be
formatted as `"(%v, %v)"` for example, and deduce the `int` values as `%d`.

For more details regarding `AbslStringify()` and its integration with other
libraries, see https://abseil.io/docs/cpp/guides/abslstringify.

Note: Types that implement `operator<<(std::ostream &, T)` can also be streamed
into `LOG()` but it is recommended that users implement `AbslStringify()` as it
has greater compatibility with other string formatting libraries.

### Why does logging use macros and not functions?

There are several reasons the logging system uses macros:

*   Until C++20, which introduces `std::source_location`, it's impossible to
    portably capture source filename and line number at a function call without
    spelling out `__FILE__` and `__LINE__` or hiding their spelling in a macro.

*   `CHECK()` uses stringification to include the source code text of the failed
    condition in the failure message. There's no way to do this in a function.

*   `CHECK(bar()) << foo();` does not evaluate `foo()` when `bar()` returns
    `true`. Likewise `LOG(INFO) << foo();` does not evaluate `foo()` if
    `ABSL_MIN_LOG_LEVEL` is `kWarning`. Functions can't do this.

### Okay, but how does `LOG(ERROR)` not use the name `ERROR`? It's right there! {#hygiene}

`LOG(severity)` is a preprocessor macro whose definition looks like
`LONG_INTERNAL_MACRO_NAME_##severity`. The `##` preprocessor operator
concatenates tokens, so writing `LOG(ERROR)` is just like writing
`LONG_INTERNAL_MACRO_NAME_ERROR`. The preprocessor works from left to right, so
it expands `LOG()` before it inspects `ERROR`, and after expanding `LOG()` there
is no longer an `ERROR` token to expand.

`LONG_INTERNAL_MACRO_NAME_ERROR` in turn expands to something like
`::internal_namespace::LogMessage(__FILE__,
__LINE__, ::absl::LogSeverity::kError)`, which does not use the name `ERROR`
either.

`LONG_INTERNAL_MACRO_NAME_LEVEL(x)` is a function-like macro of one argument;
this is how `LOG(LEVEL(x))` works.

This is also why misspelling a severity level, e.g. `LOG(WARN)` (this should be
`WARNING`), produces a diagnostic about `LONG_INTERNAL_MACRO_NAME_WARN` not
being defined rather than about `WARN` not being defined.
