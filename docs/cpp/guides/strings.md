---
title: Strings Library
layout: docs
sidenav: side-nav-cpp.html
type: markdown
---

The `//absl/strings` library provides classes and utility functions for
manipulating and comparing strings, converting other types (such as integers)
into strings, or evaluating strings for other usages.
Additionally, the `strings` library also contains utility functions for
"string-like" classes that store data within contiguous memory.

This document outlines highlights and general use cases for the `//absl/strings`
library. For more detailed guidance about specific classes, functions, and
fields, consult source documentation within the particular header file.

## Bytes or Strings?

Although "strings" are often thought of as a standard type in C++, they are not
a built-in type, but instead are provided in the Standard Library (in C++11
through the `std::string` class). Fundamentally, a string consists of a size,
and an array of `char` characters.

Both outside and inside Google, the `char` data type is often used not only to
store character data, but also arbitrary binary data. Google code often uses
strings to hold such arbitrary data. As a result, the Google `strings` library
also contains a fair amount of byte manipulation functions and utilities (such
as `absl::ByteSink` and `absl::ByteSource`).

<p class="note">Arbitrary series of bytes are often declared as of type
<code>unsigned char *</code> outside Google. Within Google, signedness is never
assumed, however, and arithmetic is never performed on types unless they are
explicitly noted as <code>signed</code>.</p>

## The `absl::string_view` Container {#string_view}

Most C++ code has historically used either the (older) C `char*` pointer type
or the C++ `std::string` class to hold character data. Methods that wish to
consume data of both types would typically need to provide overloaded
implementations. For this reason, Google defines an `absl::string_view` class
which acts as a wrapper around both implementations. Methods can simply declare
that they accept `string_view`, which can be initialized as `const char*` or
`const std::string&`.

The data referred to by an `absl::string_view` is immutable; functions should
only declare that they accept `absl::string_view` if they do not need to modify
the data. `absl::string_view`s are very lightweight, so you should always pass
them by value within your methods and functions via a copy; don't pass a
`const absl::string_view &`. (Passing `absl::string_view` instead of
`const absl::string_view &` has the same algorithmic complexity, but because of
register allocation and parameter passing rules, it is generally faster to pass
by value in this case.)

If you need to provide or accept string data to or from code outside your
project, use an `absl::string_view` to ensure that either implementation is
compatible. Note that the `absl::string_view` does not own the underlying data
itself; an `absl::string_view` should only be used for read-only data. If you
need to provide a string constant to an external API user, for example, you
would still internally declare that string as `const char*`; however, you would
expose that data using a `absl::string_view`.

~~~~ {.prettyprint .lang-cpp}
// Declare the string literal as const char*
const char* kGreeting = "hi";

// API users could access this string data for reading using a string_view.
absl::string_view GetGreeting() { return kGreeting; }
~~~~

A collection of `absl::string_view` elements is also generally useful when
marshalling data from strings into some other format. The `absl::Split()`
function, for example, stores its constituent pieces in a
`std::vector<absl::string_view>`, requiring only allocation for the
vector storage.

## Splitting Strings {#stringSplitting}

Use the `absl::StrSplit()` function defined in `absl/strings/str_split.h` to
split strings into substrings. This function takes an input string to be split
and a delimiter on which to split the string as arguments. `absl::StrSplit()`
adapts the returned collection to the type specified by the caller. A few
examples appear below:

~~~~ {.prettyprint .lang-cpp}
// Splits on commas. Stores in vector of string_view (no copies).
vector<absl::string_view> v = absl::StrSplit("a,b,c", ",");

// Splits on commas. Stores in vector of string (data copied once).
vector<std::string> v = absl::StrSplit("a,b,c", ",");

// Splits on any of the given characters ("," or ";")
using strings::delimiter::AnyOf;
vector<std::string> v = absl::StrSplit("a,b;c", AnyOf(",;"));

// Stores in various containers (also works w/ string_view)
set<std::string> s = absl::StrSplit("a,b,c", ",");
multiset<string> s = absl::StrSplit("a,b,c", ",");
list<std::string> li = absl::StrSplit("a,b,c", ",");
~~~~

See [str_split.h](str_split.h) for more details.

## Joining Strings {#stringJoining}

Several functions for joining strings exist within the `//absl/strings` library.
The following are the most commonly used.

-   `absl::StrCat()` concatenates a series of strings and creates a new
    `std::string` object.
-   `absl::StrAppend()` appends to an existing `std::string` object.
-   `strings::Join()` joins a collection of elements with the given separator
    string between each element. The elements in the collection may be strings,
    ints, floats, any StrCat-compatible type.

`absl::StrCat()` and `absl::StrAppend()` are more efficient than operators such
as `+=`, since they don't require the creation of temporary `std::string`
objects during string construction.

~~~~ {.prettyprint .lang-cpp}
// Inefficient code
std::string s1 = "A string";
std::string another = " and another string";
s1 += " and some other string" + another;

// Efficient code
std::string s1 = "A string";
std::string another = " and another string";
absl::StrAppend(&s1, " and some other string", another);
~~~~

For this reason, you should get in the habit of preferring `absl::StrCat` or
`absl::StrAppend` over using the concatenation operators.

## String Substitution

Formatting strings for display to users typically has different needs.
Traditionally, most C++ code used built-in functions such as `sprintf()` and
`snprintf()`; these functions have some problems in that they don't support
`absl::string_view` and the memory of the formatted buffer must be mananged.

Instead, `absl::Substitute()` combines the efficiency and type-safe nature of
`StrCat()` with the argument-binding of conventional functions like `sprintf()`.

~~~~ {.prettyprint .lang-cpp}
// Bad. Need to worry about buffer size and null-terminations.
char buffer[50];

string GetErrorMessage(char *op, char *user, int id) {
   sprintf(buffer, "Error in %s for user %s (id %i)", op, user, id);
   return buffer;
}

// Better. Using absl::StrCat() avoids the pitfalls of sprintf() and is faster.
string GetErrorMessage(absl::string_view op, absl::string_view user, int id) {
  return absl::StrCat("Error in ", op, " for user ", user, "(", id, ")");
}

// Best. Using absl::Substitute() is easier to read and to understand.
string GetErrorMessage(absl::string_view op, absl::string_view user, int id) {
  return absl::Substitute("Error in $0 for user $1 ($2)", op, user, id);
}
~~~~

## Converting to and from Numeric Types {#numericConversion}

Specialty functions for converting between strings and numeric types within the
`//absl/strings` library are defined within [numbers.h](numbers.h). The
following functions are of particular use:

-   `absl::SimpleItoa()` and `absl::SimpleFtoa()` convert integral and
    floating-point types, respectively, to their string representations.
-   `absl::SimpleAtoi()` converts a string into integral types. (A
    `absl::SimpleAtof()` function is forthcoming.)

As well, `absl::StrCat()` and `absl::StrAppend()` operate on types other than
just `std::string`, `absl::string_view` or `char \*`. You can use
`StrCat/StrAppend` to convert int32, uint32, int64, uint64, float, and double
types into strings:

~~~~ {.prettyprint .lang-cpp}
string foo = StrCat("The total is ", cost + tax + shipping);
~~~~
