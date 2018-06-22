---
title: absl::StrFormat()
layout: docs
sidenav: side-nav-cpp.html
type: markdown
---

# absl::StrFormat()

The `str_format` library is a typesafe replacement for the family of `printf()`
string formatting routines within the `<cstdio>` standard library header. The
`str_format` library provides most of the functionality of `printf()` type
string formatting and a number of additional benefits:

*   Type safety, including native support for `std::string` and
    `absl::string_view`
*   Reliable behavior independent of standard libraries
*   Support for the POSIX positional extensions
*   Much faster (generally 2 to 3 times faster) than native `printf` functions
*   Streamable to a variety of existing sinks

Additionally, the library includes replacements for `printf()`, `fprintf()`, and
`snprintf()`.

## Basic Usage

The main `StrFormat()` function is a variadic template that returns a string
given a `printf()`-style *format string* and zero or more additional arguments.
Use it as you would `sprintf()`.

The format string generally consists of ordinary character data along with one
or more format conversion specifiers (denoted by the `%` character). Ordinary
character data is returned unchanged into the result string, while each
conversion specification performs a type substitution from `StrFormat()`'s other
arguments.

`StrFormat()` returns an empty string on error, and is marked as
`ABSL_MUST_USE_RESULT`.

Example:

```cpp
string s = absl::StrFormat("Welcome to %s, Number %d!", "The Village", 6);
EXPECT_EQ("Welcome to The Village, Number 6!", s);
```

The `StrFormat()` format string should usually be declared `constexpr`\*; as a
result, if you need to provide it as a variable, use an `absl::string_view`
instead of a `std::string`:

```cpp
// Won't compile, not constexpr (and strings can't be declared constexpr).
std::string formatString = "Welcome to %s, Number %d!";
std::string s = absl::StrFormat(formatString, "The Village", 6);

// This will compile.
constexpr absl::string_view formatString = "Welcome to %s, Number %d!";
string s = absl::StrFormat(formatString, "The Village", 6);
```

Requiring the format string to be `constexpr` allows compiler-time checking of
the format strings.

NOTE: \* a format string must either be declared `constexpr` or dynamically
formatted using a `ParsedFormat` type. See the forthcoming "Advanced StrFormat
Usage' guide for information on dynamic formatting.

### Conversion Specifiers

The `str_format` library follows the POSIX syntax as used within the [POSIX
`printf` specification][1], which specifies the makeup of a format conversion
specifier. A format conversion specifier is a string of the following form:

*   The `%` character
*   An optional positional specifier of the form `n$`, where `n` is a
    non-negative, positive value. (E.g. `3$`, `10$`, etc.). Note that positional
    modifiers are fully supported in `StrFormat`; they are a POSIX extension and
    not part of standard `printf` notation.
*   An optional set of justification and padding flags:
    *   `-` to left-justify the result. (Right-justification is the default.)
    *   `+` to force prepending a plus sign to positive results. (Minus signs
        are always prepended.)
    *   ` ` (space) to prepend spaces to the result of a signed conversion. (`+`
        takes precedence over spaces).
    *   `#` to use an alternative form of conversion for certain specifiers.
        (E.g. Using `#` on a hex conversion will prepend `0x` or `0X` to hex
        string results.)
    *   `0` (zero) to pad leading zeros for integer and floating-point
        conversions. (Zero-padding is ignored for integers if precision is
        explicitly specified.) This flag is ignored if `-` is used.
*   An optional integer value of the form `n` to specify the minimum width of
    the result, or <code>*<i>variable</i></code> to use a variable of type `int`
    to specify this value.
*   An optional precision value specified as `.n`, where `n` is a integral
    value, or <code>.*<i>variable</i></code> to use a variable of type `int` to
    specify this value.
*   A length modifer to modify the length of the data type. In `StrFormat()`,
    these values are ignored (and not needed, since `StrFormat()` is type-safe)
    but are allowed for backwards compatibility:
    *   `hh`, `h`, `l`, `ll`, `L`, `j`, `z`, `t`, `q`
*   A type-specifier:
    *   `c` for characters
    *   `s` for strings
    *   `d` or `i` for signed integers
    *   `o` for unsigned integer conversions into octal
    *   `x` or `X` for unsigned integer conversions into hex
    *   `u` for unsigned integers
    *   `f` or `F` for floating point values into decimal notation
    *   `e` or `E` for floating point values into exponential notation
    *   `a` or `A` for floating point values into hex exponential notation
    *   `g` or `G` for floating point values into decimal or exponential
        notation based on their precision
    *   `p` for pointer address values
    *   `n` for the special case of writing out the number of characters written
        to this point.

NOTE: the `n` specifier within the `printf` family of functions is unsafe.
`StrFormat()` allows use of `%n` only when capturing such values within a safe
`FormatCountCapture` class. See example below.

Examples:

```cpp
// Characters
absl::StrFormat("%c", 'a') -> "a"
absl::StrFormat("%c", 32)  -> " "
absl::StrFormat("%c", 100) -> "d"

// Strings
absl::StrFormat("%s", "Hello!") -> "Hello!"

// Decimals
absl::StrFormat("%d", 1)    -> "1"
absl::StrFormat("%02d", 1)  -> "01"       // Zero-padding
absl::StrFormat("%-2d", 1)  -> "1 "       // Left justification
absl::StrFormat("%0+3d", 1) -> "+01");    // + specifier part of width

// Octals
absl::StrFormat("%o", 16)   -> "20"
absl::StrFormat("%o", 016)  -> "16"       // literal octal
absl::StrFormat("%#o", 016) -> "016"      // alternative form

// Hex
absl::StrFormat("%x", 16)    -> "10"
absl::StrFormat("%x", 0x16)  -> "16"
absl::StrFormat("%#x", 0x16) -> "0x16"    // alternative form
absl::StrFormat("%X", 10)    -> "A"       // Upper-case

// Unsigned Integers
absl::StrFormat("%u", 16) -> "16"
absl::StrFormat("%u", -16) -> "4294967280"

// Floating Point
// Default precision of %f conversion is 6
absl::StrFormat("%f", 1.6)       -> "1.600000" // Width includes decimal pt.
absl::StrFormat("%05.2f", 1.6)   -> "01.60"
absl::StrFormat("%.1f", 1.63232) -> "1.6"      // Rounding down
absl::StrFormat("%.3f", 1.63451) -> "1.635"    // Rounding up

// Exponential Notation
// Default precision of a %e conversion is 6
// Default precision of exponent is 2
// Default sign of exponent is +
absl::StrFormat("%e", 1.6)    -> "1.600000e+00"
absl::StrFormat("%1.1e", 1.6) -> "1.6e+00"

// Hex Exponents
absl::StrFormat("%a", 3.14159) -> "0x1.921f9f01b866ep+1"

// Floating Point to Exponential Notation
absl::StrFormat("%g", 31415900000) -> "3.14159e+10"

// Pointer conversion
int* ptr = 9;
absl::StrFormat("%p", ptr) -> "0x7ffdeb6ad2a4";

// Positional Modifiers
string s = absl::StrFormat("%2$s, %3$s, %1$s!", "vici", "veni", "vidi");
EXPECT_EQ(s, "veni, vidi, vici!");

// Character Count Capturing
int n = 0;
std::string s = absl::StrFormat(
    "%s%d%n", "hello", 123, absl::FormatCountCapture(&n));
EXPECT_EQ(8, n);
```

### Type Support

`StrFormat()` intrinsically supports all of these fundamental C++ types:

*   Characters:
    *   `char`
    *   `signed char`
    *   `unsigned char`
*   Integers:
    *   `int`
    *   `short`
    *   `unsigned short`
    *   `unsigned`
    *   `long`
    *   `unsigned long`
    *   `long long`
    *   `unsigned long long`
*   Floating-point:
    *   `float`
    *   `double`
    *   `long double`

Unlike the `printf` family of functions, `StrFormat()` doesn't rely on callers
encoding the exact types of arguments into the format string. (With `printf()`
this must be carefully done with length modifiers and conversion specifiers -
such as `%llu` encoding the type `unsigned long long`.) In the `str_format`
library, a format conversion specifies a broader C++ conceptual category instead
of an exact type. For example, `%s` binds to any string-like argument, so
`std::string`, `absl::string_view`, and `const char*` are all accepted.
Likewise, `%d` accepts any integer-like argument, etc.

## PrintF Replacements

In addition to the `std::sprintf()`-like `StrFormat()` function, `str_format.h`
also provides a number of drop-in replacements for `std::printf()`,
`std::fprintf()` and `std::snprintf()`:

*   `absl::PrintF()`
*   `absl::FPrintF()`
*   `absl::SNPrintF()`

These functions are all analogs to the C builtin functions. In particular, they
take the same arguments, return an `int` with the same semantics and can set
`errno`. Use these functions as you would use any printf variant.

Example:

```cpp

absl::PrintF("Trying to request TITLE: %s USER: %s\n", title, user);
```

## Appending to a String

The `absl::StrAppendFormat()` function allows you to perform `printf`-like
formatting to an existing `&dest` string, appending the formatted string to it.
`StrAppendFormat()` returns `*dest` as a convenience for chaining purposes.

Example:

```cpp
string& absl::StrAppendFormat(&dest, format, ...)
```

## Writing to a Stream

`absl::StreamFormat()` returns an object that can be efficiently streamed to a
`std::ostream`, such as I/O or files.

NOTE: the returned object must be used immediately. That is, do not retain it in
an 'auto' variable.

Example:

```cpp
//  Stream to standard output
std::cout << absl::StreamFormat("name: %-20.4s: quota: %7.3f", name, quota);

// Stream to a file
FILE * fileHandle;
fileHandle = fopen("myfile.txt","w");
if (fileHandle!=nullptr)
{
  int result =
      absl::FPrintF(fileHandle, "%s", "C:\\Windows\\System32\\");
  return result;
}
```

[1]: http://pubs.opengroup.org/onlinepubs/9699919799/utilities/printf.html
