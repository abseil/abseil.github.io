---
title: Strings Library
layout: docs
sidenav: side-nav-cpp.html
type: markdown
---

The `absl/strings` library provides classes and utility functions for
manipulating and comparing strings, converting other types (such as integers)
into strings, or evaluating strings for other usages. Additionally, the
`strings` library also contains utility functions for "string-like" classes that
store data within contiguous memory.

This document outlines highlights and general use cases for the `strings`
library. For more detailed information about specific classes, functions, and
fields, consult source documentation within the particular header file.

Although "strings" are often thought of as a standard type in C++, they are not
a built-in type, but instead are provided in the Standard Library through the
`std::string` class. Fundamentally, a string consists of a size, and an array of
`char` characters.

## The `absl::string_view` Container {#string_view}

Oftentimes, you need to access string data, but you don't need to own it, and
you don't need to modify it. For this reason, Abseil defines an
`absl::string_view` class, which points to a contiguous span of characters,
often part or all of another `std::string`, double-quoted string literal,
character array, or even another `string_view`. A `string_view`, as its name
implies, provides a read-only view of its associated string data.

Most C++ code has historically used either the (older) C `char*` pointer type or
the C++ `std::string` class to hold character data. Methods that wish to consume
data of both types would typically need to provide overloaded implementations if
they wanted to avoid copying data. A `string_view` also acts as a wrapper around
APIs that accept both types of character data; methods can simply declare that
they accept `absl::string_view`.

`string_view` objects are very lightweight, so you should always pass them by
value within your methods and functions; don't pass a `const absl::string_view
&`. (Passing `absl::string_view` instead of `const absl::string_view &` has the
same algorithmic complexity, but because of register allocation and parameter
passing rules, it is generally faster to pass by value in this case.)

As noted above, because the `string_view` does not own the underlying data
itself, it should only be used for read-only data. If you need to provide a
string constant to an external API user, for example, you would still internally
declare that string as `const char[]`; however, you would expose that data using
an `string_view`.

```cpp
// If an API declare a string literal as const char ...
const char kGreeting[] = "hi";

// API users could access this string data for reading using a string_view.
absl::string_view GetGreeting() { return kGreeting; }
```

A `string_view` is also suitable for local variables if you know that the
lifetime of the underlying object is longer than the lifetime of your
`string_view` variable. However, beware of binding it to a temporary value:

```cpp
// BAD use of string_view: lifetime problem
absl::string_view sv = obj.ReturnAString();

// GOOD use of string_view: str outlives sv
std::string str = obj.ReturnAString();
absl::string_view sv = str;
```

Due to lifetime issues, a `string_view` is usually a poor choice for a return
value and almost always a poor choice for a data member. If you do use one this
way, it is your responsibility to ensure that the `string_view` does not outlive
the object it points to.

A `string_view` may represent a whole string or just part of a string. For
example, when splitting a string, `std::vector<absl::string_view>` is a natural
data type for the output.

## `absl::StrSplit()` for Splitting Strings

The `absl::StrSplit()` function provides an easy way to split strings into
substrings. `StrSplit()` takes an input string to be split, a delimiter on which
to split the string (e.g. a comma `,`), and (optionally), a predicate to act as
a filter on whether split elements will be included in the result set.
`StrSplit()` also adapts the returned collection to the type specified by the
caller.

Examples:

```cpp
// Splits the given string on commas. Returns the results in a
// vector of strings. (Data is copied once.)
std::vector<std::string> v = absl::StrSplit("a,b,c", ',');  // Can also use ","
// v[0] == "a", v[1] == "b", v[3] == "c"

// Splits the string as in the previous example, except that the results
// are returned as `absl::string_view` objects, avoiding copies. Note that
// because we are storing the results within `absl::string_view` objects, we
// have to ensure that the input string outlives any results.
std::vector<absl::string_view> v = absl::StrSplit("a,b,c", ',');
// v[0] == "a", v[1] == "b", v[3] == "c"
```

`StrSplit()` splits strings using a passed *Delimiter* object. (See
[Delimiters](#delimiters) below.) However, in many cases, you can simply pass a
string literal as the delimiter (which will be implicitly converted to an
`absl::ByString` delimiter).

Examples:

```cpp
// By default, empty strings are *included* in the output. See the
// `absl::SkipEmpty()` predicate below to omit them{#stringSplitting}.
std::vector<std::string> v = absl::StrSplit("a,b,,c", ',');
// v[0] == "a", v[1] == "b", v[3] == "", v[4] = "c"

// You can also split an empty string
v = absl::StrSplit("", ',');
// v[0] = ""

// The delimiter need not be a single character
std::vector<std::string> v = absl::StrSplit("aCOMMAbCOMMAc", "COMMA");
// v[0] == "a", v[1] == "b", v[2] == "c"

// You can also use the empty string as the delimiter, which will split
// a string into its constituent characters.
std::vector<std::string> v = absl::StrSplit("abcd", "");
// v[0] == "a", v[1] == "b", v[2] == "c", v[3] = "d"
```

### Adaptation to Returned Types

One of the more useful features of the `StrSplit()` API is its ability to adapt
its result set to the desired return type. `StrSplit()` returned collections may
contain `std::string`, `absl::string_view`, or any object that can be explicitly
created from an `absl::string_view`. This pattern works for all standard STL
containers including `std::vector`, `std::list`, `std::deque`, `std::set`,
`std::multiset`, `std::map`, and `std::multimap`, and even `std::pair`, which is
not actually a container.

Examples:

```cpp
// Stores results in a std::set<std::string>, which also performs de-duplication
// and orders the elements in ascending order.
std::set<std::string> a = absl::StrSplit("b,a,c,a,b", ',');
// v[0] == "a", v[1] == "b", v[3] == "c"

// Stores results in a map. The map implementation assumes that the input
// is provided as a series of key/value pairs. For example, the 0th element
// resulting from the split will be stored as a key to the 1st element. If
// an odd number of elements are resolved, the last element is paired with
// a default-constructed value (e.g., empty string).
std::map<std::string, std::string> m = absl::StrSplit("a,b,c", ',');
// m["a"] == "b", m["c"] == "" // last component value equals ""

// Stores first two split strings as the members in a std::pair. Any split
// strings beyond the first two are omitted because std::pair can hold only two
// elements.
std::pair<std::string, std::string> p = absl::StrSplit("a,b,c", ',');
// p.first = "a", p.second = "b" ; "c" is omitted
```

### Delimiters

The `StrSplit()` API provides a number of "Delimiters" for providing special
delimiter behavior. A Delimiter implementation contains a `Find()` function that
knows how to find the first occurrence of itself in a given `absl::string_view`.
Models of the Delimiter concept represent specific kinds of delimiters, such as
single characters, substrings, or even regular expressions.

The following Delimiter abstractions are provided as part of the `StrSplit()`
API:

*   `absl::ByString()` (default for `std::string` arguments)
*   `absl::ByChar()` (default for a `char` argument)
*   `absl::ByAnyChar()` (for mixing delimiters)
*   `absl::ByLength()` (for applying a delimiter a set number of times)
*   `absl::MaxSplits()` (for splitting a specific number of times)

Examples:

```cpp
// Because a `string` literal is converted to an `absl::ByString`, the following
// two splits are equivalent.
std::vector<std::string> v = absl::StrSplit("a,b,c", ",");
std::vector<std::string> v = absl::StrSplit("a,b,c", absl::ByString(","));
// v[0] == "a", v[1] == "b", v[3] == "c"

// Because a `char` literal is converted to an `absl::ByChar`, the following two
// splits are equivalent.
std::vector<std::string> v = absl::StrSplit("a,b,c", ',');
// v[0] == "a", v[1] == "b", v[3] == "c"

std::vector<std::string> v = absl::StrSplit("a,b,c", absl::ByChar(','));
// v[0] == "a", v[1] == "b", v[3] == "c"

// Splits on any of the given characters ("," or ";")
vector<std::string> v = absl::StrSplit("a,b;c", absl::ByAnyChar(",;"));
// v[0] == "a", v[1] == "b", v[3] == "c"

// Uses the `absl::MaxSplits` delimiter to limit the number of matches a
// delimiter can have. In this case, the delimiter of a literal comma is limited
// to matching at most one time. The last element in the returned collection
// will contain all unsplit pieces, which may contain instances of the
// delimiter.
std::vector<std::string> v = absl::StrSplit("a,b,c", absl::MaxSplits(',', 1));
// v[0] == "a", v[1] == "b,c"

// Splits into equal-length substrings.
std::vector<std::string> v = absl::StrSplit("12345", absl::ByLength(2));
// v[0] == "12", v[1] == "34", v[3] == "5"
```

### Filtering Predicates

Predicates can filter the results of a `StrSplit()` operation by determining
whether or not a resultant element is included in the result set. A filtering
predicate may be passed as an *optional* third argument to the `StrSplit()`
function.

The predicates must be unary functions (or functors) that take a single
`absl::string_view` argument and return a bool indicating whether the argument
should be included (`true`) or excluded (`false`).

One example where using predicates is useful: filtering out empty substrings. By
default, empty substrings may be returned by `StrSplit()` as separate elements
in the result set, which is similar to the way split functions work in other
programming languages.

```cpp
// Empty strings *are* included in the returned collection.
std::vector<std::string> v = absl::StrSplit(",a,,b,", ',');
// v[0] == "", v[1] == "a", v[2] == "", v[3] = "b", v[4] = ""
```

These empty strings can be filtered out of the result set by simply passing the
provided `SkipEmpty()` predicate as a third argument to the `StrSplit()`
function. `SkipEmpty()` does not consider a string containing all whitespace to
be empty. For that behavior use the `SkipWhitespace()` predicate.

Examples:

```cpp
// Uses absl::SkipEmpty() to omit empty strings. Strings containing whitespace
// are not empty and are therefore not skipped.
std::vector<std::string> v = absl::StrSplit(",a, ,b,", ',', absl::SkipEmpty());
// v[0] == "a", v[1] == " ", v[2] == "b"

// Uses absl::SkipWhitespace() to skip all strings that are either empty or
// contain only whitespace.
std::vector<std::string> v = absl::StrSplit(",a, ,b,", ',',
                                            absl::SkipWhitespace());
// v[0] == "a", v[1] == "b"
```

## `absl::StrCat()` and `absl::StrAppend()` for String Concatenation

Most documentation on the usage of C++ strings mention that unlike other
languages, strings in C++ are mutable; however, modifying a string can be
expensive, as strings often contain a large amount of data, and many patterns
involve the creation of temporary copies, which may involve significant
overhead. Always look for ways to reduce creation of such temporaries.

For example, the following code is inefficient:

```cpp
// Inefficient code
std::string s1;
s1 = s1 + " another string";
```

The assignment operator above creates a temporary string, copies `s1` into that
temporary string, concatenates that temporary string, and then assigns it back
to `s1`. Instead use the optimized `+=` operator for such concatenation:

```cpp
// Efficient code
s1 += " another string";
```

Good compilers may be able to optimize the preceding inefficient code. However,
operations that involve more than one concatenation cannot normally avoid
temporaries:

```cpp
// Inefficient code
string s1 = "A string";
string another = " and another string";
s1 += " and some other string" + another;
```

For that reason, Abseil provides the `absl::StrCat()` and `absl::StrAppend()`
functions for efficiently concatenating and appending strings. `absl::StrCat()`
and `absl::StrAppend()` are often more efficient than operators such as `+=`,
since they don't require the creation of temporary `std::string` objects, and
their memory is preallocated during string construction.

```cpp
// Inefficient code
std::string s1 = "A string";
std::string another = " and another string";
s1 += " and some other string" + another;

// Efficient code
std::string s1 = "A string";
std::string another = " and another string";
absl::StrAppend(&s1, " and some other string", another);
```

For this reason, you should get in the habit of preferring `absl::StrCat()` or
`absl::StrAppend()` over using the concatenation operators.

### `absl::StrCat()`

`absl::StrCat()` merges an arbitrary number of strings or numbers into one
string, and is designed to be the fastest possible way to construct a string out
of a mix of raw C strings, `absl::string_view` elements, `std::string` value,
and boolean and numeric values. `StrCat()` is generally more efficient on string
concatenations involving more than one unary operator, such as `a + b + c` or `a
+= b + c`, since they avoid the creation of temporary string objects during
string construction.

```cpp
// absl::StrCat() can merge an arbitrary number of strings
std::string s1;
s1 = absl::StrCat("A string ", " another string", "yet another string");

// StrCat() also can mix types, including std::string, string_view, literals,
// and more.
std::string s1;
std::string s2 = "Foo";
absl::string_view sv1 = MyFunction();
s1 = absl::StrCat(s2, sv1, "a literal");
```

`StrCat()` provides automatic formatting for the following types:

*   `std::string`
*   `absl::string_view`
*   String literals
*   Numeric values (floats, ints)
*   Boolean values (convert to "0" or "1")
*   Hex values through use of the `absl::Hex()` conversion function

Floating point values are converted to a string using the same format used by
STL's std::basic_ostream::operator<<, namely 6 digits of precision, using "e"
format when the magnitude is less than 0.001 or greater than or equal to 1e+6.

You can convert to hexadecimal output rather than decimal output using the
`absl::Hex` type. To do so, pass `Hex(my_int)` as a parameter to `StrCat()` or
`StrAppend()`. You may specify a minimum hex field width using an
`absl::PadSpec` enum, so the equivalent of `StringPrintf("%04x", my_int)` is
`absl::StrCat(absl::Hex(my_int, absl::kZeroPad4))`.

### `absl::StrAppend()`

For clarity and performance, don't use `absl::StrCat()` when appending to a
string. Use `absl::StrAppend()` instead. In particular, avoid using any of these
(anti-)patterns:

```cpp
str.append(absl::StrCat(...))
str += absl::StrCat(...)
str = absl::StrCat(str, ...)
```

## `absl::StrJoin()` for Joining Elements within a String

Although similar to `absl::StrCat()` in some similar use cases,
`absl::StrJoin()` provides a more robust utility for joining a range of
elements, defining separator strings, and formatting the result as a string.

Ranges are specified by passing a container with `std::begin()` and `std::end()`
iterators, container-specific `begin()` and `end()` iterators, a
brace-initialized `std::initializer_list`, or a `std::tuple` of heterogeneous
objects. The separator string is specified as an `absl::string_view`.

Because the default formatter uses the `absl::AlphaNum` class,
`absl::StrJoin()`, like `absl::StrCat()`, will work out-of-the-box on
collections of strings, ints, floats, doubles, etc.

### Examples

```cpp
std::vector<string> v = {"foo", "bar", "baz"};
string s = absl::StrJoin(v, "-");
// Produces the string "foo-bar-baz"

// Joins the values in the given `std::initializer_list<>` specified using
// brace initialization. This pattern also works with an initializer_list
// of ints or `absl::string_view` -- any `AlphaNum`-compatible type.
string s = absl::StrJoin({"foo", "bar", "baz"}, "-");
// Produces the string "foo-bar-baz"

// Joins a collection of ints. This pattern also works with floats,
// doubles, int64s -- any `absl::StrCat()`-compatible type.
std::vector<int> v = {1, 2, 3, -4};
string s = absl::StrJoin(v, "-");
// Produces the string "1-2-3--4"

// Joins a collection of pointer-to-int. By default, pointers are
// dereferenced and the pointee is formatted using the default format for
// that type; such dereferencing occurs for all levels of indirection, so
// this pattern works just as well for `std::vector<int**>` as for
// `std::vector<int*>`.
int x = 1, y = 2, z = 3;
std::vector<int*> v = {&x, &y, &z};
string s = absl::StrJoin(v, "-");
// Produces the string "1-2-3"

// Dereferencing of `std::unique_ptr<>` is also supported:
std::vector<std::unique_ptr<int>> v
v.emplace_back(new int(1));
v.emplace_back(new int(2));
v.emplace_back(new int(3));
string s = absl::StrJoin(v, "-");
// Produces the string "1-2-3"

// Joins a `std::map`, with each key-value pair separated by an equals
// sign. This pattern would also work with, say, a
// `std::vector<std::pair<>>`.
std::map<string, int> m = {{"a", 1}, {"b", 2}, {"c", 3}};
string s = absl::StrJoin(m, ",", absl::PairFormatter("="));
// Produces the string "a=1,b=2,c=3"
```

### Join Formatters

`absl::StrJoin()` uses "Formatters" to format the elements to be joined (and
defaults to an `AlphaNumFormatter()` if no formatter is specified. A Formatter
is a function object that is responsible for formatting its argument as a string
and appending it to a given output string. Formatters may be implemented as
function objects, lambdas, or normal functions. You may provide your own
Formatter to enable `absl::StrJoin()` to work with arbitrary types.

The following is an example of a custom Formatter that simply uses
`std::to_string()` to format an integer as a string:

```cpp
struct MyFormatter {
  void operator()(string* out, int i) const {
    out->append(std::to_string(i));
  }
};
```

You would use the above formatter by passing an instance of it as the final
argument to `absl::StrJoin()`:

```cpp
std::vector<int> v = {1, 2, 3, 4};
string s = absl::StrJoin(v, "-", MyFormatter());
// Produces the string "1-2-3-4"
```

The following standard formatters are provided within the `StrJoin()` API:

*   `AlphaNumFormatter()` (the default)
*   `StreamFormatter()` formats its arguments using the << operator.
*   `PairFormatter()` formats a `std::pair` by putting a given separator between
    the pair's `.first` and `.second` members.
*   `DereferenceFormatter()` formats its argument by dereferencing it and then
    applying the given formatter. This formatter is useful for formatting a
    container of pointer-to-T. This pattern often shows up when joining repeated
    fields in protocol buffers.

## `absl::Substitute()` for String Substitution

Formatting strings for display to users typically has different needs.
Traditionally, most C++ code used built-in functions such as `sprintf()` and
`snprintf()`; these functions have some problems in that they don't support
`absl::string_view` and the memory of the formatted buffer must be managed.

```cpp
// Bad. Need to worry about buffer size and null-terminations.

string GetErrorMessage(char *op, char *user, int id) {
  char buffer[50];
  sprintf(buffer, "Error in %s for user %s (id %i)", op, user, id);
  return buffer;
}

// Better. Using absl::StrCat() avoids the pitfalls of sprintf() and is faster.
string GetErrorMessage(absl::string_view op, absl::string_view user, int id) {
  return absl::StrCat("Error in ", op, " for user ", user, " (", id, ")");
}

// Best. Using absl::Substitute() is easier to read and to understand.
string GetErrorMessage(absl::string_view op, absl::string_view user, int id) {
  return absl::Substitute("Error in $0 for user $1 ($2)", op, user, id);
}
```

`absl::Substitute()` combines the efficiency and type-safe nature of
`absl::StrCat()` with the argument-binding of conventional functions like
`sprintf()`. `absl::Substitute` uses a format string that contains positional
identifiers indicated by a dollar sign ($) and single digit positional ids to
indicate which substitution arguments to use at that location within the format
string.

```cpp
string s = Substitute("$1 purchased $0 $2. Thanks $1!", 5, "Bob", "Apples");
// Produces the string "Bob purchased 5 Apples. Thanks Bob!"

string s = "Hi. ";
SubstituteAndAppend(&s, "My name is $0 and I am $1 years old.", "Bob", 5);
// Produces the string "Hi. My name is Bob and I am 5 years old."
```

Note however, that `absl::Subtitute()`, because it requires parsing a format =
string at run-time, is slower than `absl::StrCat()`. Choose `Substitute()` over
`StrCat()` only when code clarity is more important than speed.

### Differences from `StringPrintf()`

`absl::Substitute` differs from `StringPrintf()` in the following ways:

*   The format string does not identify the types of arguments. Instead, the
    arguments are implicitly converted to strings.
*   Substitutions in the format string are identified by a '$' followed by a
    single digit. You can use arguments out-of-order and use the same argument
    multiple times.
*   A '$$' sequence in the format string means output a literal '$' character.
*   `absl::Substitute()` is significantly faster than `StringPrintf()`. For very
    large strings, it may be orders of magnitude faster.

### Supported Types

`absl::Substitute()` understands the following types:

*   `absl::string_view`, `std::string`, `const char*` (null is equivalent to "")
*   `int32_t`, `int64_t`, `uint32_t`, `uint64_t`
*   `float`, `double`
*   `bool` (Printed as "true" or "false")
*   pointer types other than char* (Printed as `0x<lower case hex string>`,
    except that null is printed as "NULL")

## `absl::StrContains()` for String Matching

The Abseil strings library also contains simple utilities for performing string
matching checks. All of their function parameters are specified as
`absl::string_view`, meaning that these functions can accept `std::string`,
`absl::string_view` or nul-terminated C-style strings.

```cpp
// Assume "msg" is a line from a logs entry
if (absl::StrContains(msg, "ERROR")) {
  *has_error = true;
}
if (absl::StrContains(msg, "WARNING")) {
  *has_warning = true;
}
```

Note: The order of parameters in these functions is designed to mimic the order
an equivalent member function would exhibit; e.g. `s.Contains(x)` ==>
`absl::StrContains(s, x)`.

## Converting to and from Numeric Types {#numericConversion}

Specialty functions for converting strings to numeric types within the
`absl/strings` library are defined within [numbers.h](numbers.h). The following
functions are of particular use:

*   `absl::SimpleAtoi()` converts a string into integral types.
*   `absl::SimpleAtof()` converts a string into a float.
*   `absl::SimpleAtod()` converts a string into a double.
*   `absl::SimpleAtob()` converts a string into a boolean.

For conversion of numeric types into strings, use `absl::StrCat()` and
`absl::StrAppend()`. You can use `StrCat/StrAppend` to convert `int32`,
`uint32`, `int64`, `uint64`, `float`, and `double` types into strings:

```cpp
string foo = StrCat("The total is ", cost + tax + shipping);
```
