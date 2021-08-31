---
title: "absl::StrFormat()"
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
*   Supports Abseil types such as `absl::Cord` natively and can be extended to
    support other types.
*   Much faster (generally 2 to 3 times faster) than native `printf` functions
*   Streamable to a variety of existing sinks
*   Extensible to custom sinks

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
#include "absl/strings/str_format.h"

std::string s = absl::StrFormat("Welcome to %s, Number %d!", "The Village", 6);
EXPECT_EQ("Welcome to The Village, Number 6!", s);
```

The `StrFormat()` format string should usually be declared `constexpr`\*; as a
result, if you need to provide it as a variable, use an `absl::string_view`
instead of a `std::string`:

```cpp
// Won't compile, not constexpr (and the `std::string` can't be declared constexpr).
std::string format_string = "Welcome to %s, Number %d!";
std::string s = absl::StrFormat(format_string, "The Village", 6);

// This will compile.
constexpr absl::string_view kFormatString = "Welcome to %s, Number %d!";
std::string s = absl::StrFormat(kFormatString, "The Village", 6);
```

Requiring the format string to be `constexpr` allows compile-time checking of
the format strings.

NOTE: \* a format string must either be declared `constexpr` or dynamically
formatted using an `absl::ParsedFormat` type. See
[Advanced Formatting](#advanced) below.

### Conversion Specifiers

The `str_format` library follows the POSIX syntax as used within the
[POSIX `printf()` family specification][1], which specifies the makeup of a
format conversion specifier. A format conversion specifier is a string of the
following form:

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
    *   `c` for character values
    *   `s` for string values
    *   `d` or `i` for integer values, including enumerated type values
    *   `o` for unsigned integer conversions, including enumerated type values,
        into octal values
    *   `x` or `X` for unsigned integer conversions, including enumerated type
        values, into hex values
    *   `u` for unsigned integer values
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
absl::StrFormat("%*.*f", 5, 2, 1.63451) -> " 1.63"  // Same as "%5.2f"

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
std::string s = absl::StrFormat("%2$s, %3$s, %1$s!", "vici", "veni", "vidi");
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

## Advanced Formats {#advanced}

Format strings that are very frequently used or performance-critical can be
specified using an `absl::ParsedFormat`. An `absl::ParsedFormat` represents a
pre-parsed `absl::FormatSpec` with template arguments specifying a collection of
conversion specifiers.

In C++11 and C++14, these conversion specifiers are restricted to single char
values (e.g. `d`); in C++17 or later, you may also specify one or more
`absl::FormatConversionCharSet` enums (e.g. `absl::FormatConversionCharSet::d`
or `absl::FormatConversionCharSet::d | absl::FormatConversionCharSet::x` using
the bitwise-or combination.

Some enums specify whole conversion groups:

*   `absl::FormatConversionCharSet::kIntegral` = `d | i | u | o | x | X`
*   `absl::FormatConversionCharSet::kFloating` = `a | e | f | g | A | E | F | G`
*   `absl::FormatConversionCharSet::kNumeric` = `kIntegral | kFloating`
*   `absl::FormatConversionCharSet::kString` = `s`
*   `absl::FormatConversionCharSet::kPointer` = `p`

These type specifiers will be checked at compile-time. This approach is much
faster than reparsing `const char*` formats on each use.


```cpp
// Verified at compile time.
static const auto* const format_string =
    new absl::ParsedFormat<'s','d'>("Welcome to %s, Number %d!");
absl::StrFormat(*format_string, "TheVillage", 6);

// Verified at runtime.
auto format_runtime = absl::ParsedFormat<'d'>::New(format_string);
if (format_runtime) {
  value = absl::StrFormat(*format_runtime, i);
} else {
  ... error case ...
}

// C++17 allows extended formats to support multiple conversion characters per
// argument, specified via a combination of `FormatConversionCharSet` enums.
using MyFormat = absl::ParsedFormat<absl::FormatConversionCharSet::d |
                                    absl::FormatConversionCharSet::x>;
MyFormat GetFormat(bool use_hex) {
  if (use_hex) return MyFormat("foo %x bar");
  return MyFormat("foo %d bar");
}

```

Pre-compiled formats can also be used as a way to pass formats through API
boundaries in a type-safe manner. The format object encodes the type information
in its template arguments to allow compile-time checking in the formatting
functions.

Example:

```cpp
// Note: this example only compiles in C++17 and above.
class MyValue {
 public:
  // MyValueFormat can be constructed from a %d or a %x format and can be
  // used with any argument type that can be formatted with %d or %x.
  using MyValueFormat = absl::ParsedFormat<absl::FormatConversionCharSet::d |
                                           absl::FormatConversionCharSet::x>;
  const MyValueFormat& GetFormat(int radix) const {
    return radix == RADIX_HEX ? format_x_ : format_d_;
  }
 private:
   const MyValueFormat format_d_{"%6d"};
   const MyValueFormat format_x_{"%8x"};
};

std::string PrintIt(const MyValue& foo) {
  return absl::StringF(foo.GetFormat(mode), my_int_value_);
}
```

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
std::string& absl::StrAppendFormat(&dest, format, ...)
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
if (FILE* file_handle = fopen("myfile.txt","w"; file_handle != nullptr) {
  int result =
      absl::FPrintF(file_handle, "%s", "C:\\Windows\\System32\\");
  return result;
}
```

## User-Defined Formats

The `str_format` library provides customization utilities for formatting
user-defined types using `StrFormat()`. As with most type extensions, you should
own the type you wish to extend.

To extend formatting to your custom type, provide an `AbslFormatConvert()`
overload as a free (non-member) function within the same file and namespace of
that type, usually as a `friend` definition. The `str_format` library will check
for such an overload when formatting user-defined types using `StrFormat()`.

An `AbslFormatConvert()` overload should have the following signature:

```cpp
absl::FormatConvertResult<...> AbslFormatConvert(
    const X& value,
    const absl::FormatConversionSpec& conversion_spec,
    absl::FormatSink *output_sink);
```

* The `absl::FormatConvertResult` return value holds the set of
  `absl::FormatConversionCharSet` values valid for this custom type. A return
  value of `true` indicates the conversion was successful; if `false` is
  returned, `StrFormat()` will produce an empty string and this result will be
  propogated to `FormatUntyped()`.
* `absl::FormatConversionSpec` holds the fields pulled from the user string as
  they are processed. See "Conversion Specifiers" above for full documentation
  on this format.
* `absl::FormatSink` holds the formatted string as it is built.

The `absl::FormatConversionSpec` class also has a number of member functions to
inspect the returned conversion character specification:

* `conversion_char()` returns the basic conversion character for this format
  operation.
* `width()` and `precision()` indicate that the conversion operation should
  adjust the resulting width or precision of the result.
* `is_basic()` indicates that no additional conversion flags are included in the
  conversion, including any for modifying the width or precision. This method is
  useful for optimizing conversions via a fast path.
* `has_left_flag()` indicates whether the result should be left justified,
  through use of a '-' character in the format string. E.g. "%-s"
* `has_show_pos_flag()` indicates whether a sign column is prepended to the
  result for this conversion character in the format string, even if the result
  is positive, through use of a '+' character in the format string. E.g. "%+d"
* `has_show_pos_flag()` indicates whether a mandatory sign column is added to
  the result for this conversion character, through use of a space character
  (' ') in the format string. E.g. "% i"
* `has_alt_flag()` indicates whether an "alternate" format is applied to the
  result for this conversion character. E.g. "%#h"
* `has_zero_flag()` indicates whether zeroes should be prepended to the result
  for this conversion character instead of spaces, through use of the '0'
  character in the format string. E.g. "%0f"

These member functions can be used to select how to process conversion
operations encountered in the source format strings.

An example usage within a user-defined type is shown below:

```cpp
struct Point {

  ...
  // StrFormat support is added to the Point class through an
  // AbslFormatConvert() friend declaration.
  //
  // FormatConvertResult indicates that this formatting extension will accept
  // kIntegral ( d | i | u | o | x | X) or kString (s) specifiers. Successful
  // conversions will return `true`.
  friend absl::FormatConvertResult<absl::FormatConversionCharSet::kString |
                                   absl::FormatConversionCharSet::kIntegral>
  AbslFormatConvert(const Point& p,
                    const absl::FormatConversionSpec& spec,
                    absl::FormatSink* s) {
    if (spec.conversion_char() == absl::FormatConversionChar::s) {
      // If the conversion char is %s, produce output of the form "x=1 y=2"
      s->Append(absl::StrCat("x=", p.x, " y=", p.y));
    } else {
      // If the conversion char is integral (%i, %d ...) , produce output of the
      // form "1,2". Note that no padding will occur here.
      s->Append(absl::StrCat(p.x, ",", p.y));
    }
    return {true};
  }

  int x;
  int y;
};
```

## Custom Sinks

```cpp
bool absl::Format(&dest, format, ...)
```

Similar to `absl::StrAppendFormat`, but the output is an arbitrary destination
object that supports the `RawSink` interface. To implement this interface,
provide an overload of `AbslFormatFlush()` for your sink object:

```cpp
void AbslFormatFlush(MySink* dest, absl::string_view part);
```

where `dest` is the pointer passed to `absl::Format()`. This is usually
accomplished by providing a free function that can be found by ADL.

The library already provides builtin support for using sinks of type
`std::string`, `std::ostream`, and `absl::Cord` with `absl::Format()`.

Note: Remember that only the type owner should write extensions like this. An
overload for the type `MySink` should **only** be declared in the header that
declares `MySink`, and in the same namespace as `MySink`. If a particular type
does not support this extension ask the owner to write one, or make your own
wrapper type that supports it.

[1]: http://pubs.opengroup.org/onlinepubs/9699919799/functions/fprintf.html
