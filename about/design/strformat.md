---
title: "StrFormat Design Notes"
layout: about
sidenav: side-nav-design.html
type: markdown
---

# StrFormat Design Notes

The Abseil `str_format` library is a suite of classes and functions that
collectively serve as a type-safe C++ implementation of C's `std::printf()`
suite.

The Abseil `str_format` library provides the following benefits:

*   Reliable Behavior Independent of Libc
    *   Printf behavior varies between C standard library implementations. ANSI
        C, C99, POSIX, Glibc, and MSVC all have subtle differences in formatting
        support. The API includes extensions like argument position selectors
        (e.g. `"%2$d"`) that would not be supported on the native `vsnprintf`
        variant in MSVC. Some useful conversions would produce unreliable output
        or fail silently on those platforms. `absl::StrFormat()` is the same
        everywhere.
*   Extensible to formatting of user-defined types.
    *   This includes string-like types. We can print them directly without
        going through inefficient and possibly dangerous patterns like
        `std::string(my_string_view).c_str()`.
*   Safe
    *   Does not suffer `va_list`'s distortion of argument boundaries, which can
        leak data.
    *   Type mismatches yield runtime error reports, not undefined behavior.
*   Futureproof
    *   Traditionally, length modifiers embedded in the conversion format
        strings are distributed through caller code, and become a major
        difficulty when changing the range or signedness of an existing API
        type. The Abseil `str_format` library allows those length modifiers
        but ignores them, so arguments can change type without affecting caller
        code.
*   Fast
    *   Supports precompiled conversions.
    *   Can stream output piecewise to `std::ostream` sinks instead of requiring
        the use, for example, of temporary strings within wrapper functions.
    *   We can use faster, say, `dtoa` algorithms because we control the
        implementation.
*   Maintainable and Composable API
    *   Can be changed without an upstream process.
    *   Existing `vsnprintf` are all written in C, and extremely hard to read.
    *   The destination is an abstract interface, so customizable app-level
        accelerations are possible.
    *   Composable from reusable parts, enabling new entry point definitions.

Every effort was made to support or address the spec for [POSIX
printf][posix_printf], including facilities such as positional specifiers not
found in standard C and C++.

## Type Safety

A libc-based printf function can be extremely unsafe, since argument boundaries
are not preserved by `va_list`. If the size of the type indicated by the format
string doesn't match the size of the object placed into the `va_list` by the
caller, `std::printf()` can print data that is not meant to be printed, or print
garbage.

```cpp
std::printf("%llx %d %s", 1, 2, s)
```

could print some garbage from the stack, because the first argument isn't wide
enough to fill its `va_list` slot.

Compile-time format string checking helps us out here but it cannot be relied on
for safety. There are very basic scenarios that it cannot validate. The
`str_format` library has the ability to evaluate arguments as exactly the types
they were passed as, without the dangers of C-style casting necessitated by the
C stdarg feature. If that type is convertible to the type expected by the
conversion specifier, we can convert safely. Otherwise, it can return an error.
It never has to guess at the size and layout of an input argument.

## Differences from `printf()`

There are some cases where `StrFormat()` behaves differently from the specified
behavior of `std::printf()`. Some cases that were *undefined* behavior under
`std::printf()` are omitted from the discussion.

*   Locale is currently ignored. The comma separator flag `'` has no effect.
*   Implicit promotion of integral types

    In `std::printf()`, all small integral types are promoted to `int` or
    `unsigned` on their way into the `va_list`, retaining their signedness. They
    are then demoted again by length modifiers (e.g. `%hu`), hopefully to the
    original type.

    In contrast, `absl::StrFormat()` will fully retain the argument type. When
    printing a signed integer with an unsigned conversion, like `%x` or `%u`,
    the value is not widened, but only converted to its unsigned equivalent,
    preserving its bitwise value. Printing a signed number with an unsigned
    format is dodgy in the first place. Formatting of negative values with an
    unsigned conversion yields undefined behavior in `std::printf()`, so
    divergence from printf-style output here should be acceptable.

*   Implicit promotion of float to double

    A `float` argument is implicitly converted to `double` by the C varargs
    convention. This does not happen in `absl::StrFormat()`, but as long as
    every `float` value can be held in a `double` (this is the case), there
    should be no noticeable effect.

## Implementation Simplicity

The implementation of `absl::StrFormat()` is modular and composed. Its
components are individually tested and reusable.

*   The implementation of `vfprintf.c` (the engine for `printf`-formatting) is
    usually pretty tough reading. In C, an implementation cannot depend on
    inlining or template functions, so there's a lot of repetition and gotos,
    sometimes abstracted with macros.

*   The [GLIBC implementation][glibc_vfprintf] relies heavily on macros, and is
    a 2000-line function.

*   The [FreeBSD implementation][fbsd_vfprintf] is much cleaner, but is more
    limited in functionality and still 700 lines long.

We have several systems that have a printf-like vararg API for logging. The
building blocks of `absl::StrFormat()` are reusable in such contexts. A public
interface explicitly supports callers who have specialized `FormatArg` objects,
format strings, and data sinks.

As an extension, `absl::Format()` can append to objects other than strings,
allowing them to use a domain-appropriate buffering or reallocation strategy as
the formatting progresses.

Simple hooks can be written to support efficient printing to any data sink.

## Errors

The `str_format` library contains a family of functions. While
`absl::StrFormat()` returns a string (and is analagous to `std::sprintf()`),
`absl::PrintF()` provides `std::printf()` type behavior and can return errors.
In debug builds, we can log or die when a format doesn't exactly match its input
parameter types. Other variants can have better error handling. Variants of the
`absl::StrFormat()` entry points can be developed to produce better error
handling.

## References

1.  The [POSIX printf][posix_printf] spec.
1.  The [`boost::format`][boost_format] library, streams-based, not exactly
    POSIX compliant. Some fancy extensions, doesn't support arg-specified width
    or precision. Also very slow at about 5x slower than raw streams.
1.  A proposal for [std::putf][isocpp_putf], a streams-based printf that's
    exactly POSIX compliant. Interesting. Only about 2x slower than raw streams.
1.  mknejp's shot at compile-time parsed std;: iostream formats.
1.  [`SafeSprintf`][safe_snprintf]: Supports only int, uint, string, pointer.
    Part of Chromium. Ignores width specs. Async safe.
1.  Miro Knejp's simpler [library][mknejp] in response to std::putf, features
    precompilation.
1.  Facebook Folly includes a [Format library][folly_format] using Python-style
    syntax.

## Notes:

NOTE: "How to Print Floating-Point Numbers Accurately" by Guy L. Steele,
Jr. and Jon L. White [Proc. ACM SIGPLAN '90, pp. 112-126].

[fbsd_vfprintf]: http://svnweb.freebsd.org/base/stable/9/lib/libc/stdio/vfprintf.c?view=markup "FreeBSD vfprintf"
[glibc_vfprintf]: http://sourceware.org/git/?p=glibc.git;a=blob;f=stdio-common/vfprintf.c;hb=HEAD "GLIBC vfprintf"
[posix_printf]: http://pubs.opengroup.org/onlinepubs/009695399/functions/printf.html
[boost_format]: http://www.boost.org/doc/libs/1_54_0/libs/format/doc/format.html
[isocpp_putf]: http://www.open-std.org/JTC1/SC22/WG21/docs/papers/2013/n3716.html
[safe_snprintf]: https://codereview.chromium.org/18656004/
[mknejp]: https://github.com/mknejp/std-format
[folly_format]: https://github.com/facebook/folly/blob/master/folly/docs/Format.md
