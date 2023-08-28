---
title: "AbslStringify"
layout: docs
sidenav: side-nav-cpp.html
type: markdown
---

# AbslStringify

Author: phoebeliang@

The `AbslStringify()` extension point is a lightweight mechanism that allows
users to format user-defined types as strings. User-defined types that provide
an `AbslStringify()` definition are able to be formatted with libraries such as:

*   [StrFormat](format)
*   [Abseil Strings](strings) (including `absl::StrCat` and
    `absl::Substitute`)
*   [Abseil Logging](logging)
*   [GoogleTest](https://github.com/google/googletest/blob/master/docs/index.md)

Important: As with most type extensions, you should own the type you wish to
extend.

## Basic Usage

Let's say that we have a simple `Point` struct:

```cpp
struct Point {
  int x;
  int y;
};
```

If we want a `Point` to be formattable, we add a `friend` function template
named `AbslStringify()`:

```cpp
struct Point {
  template <typename Sink>
  friend void AbslStringify(Sink& sink, const Point& p) {
    absl::Format(&sink, "(%d, %d)", p.x, p.y);
  }

  int x;
  int y;
};
```

For enums, an `AbslStringify()` definition should be provided after the
definition of the `enum`:

```cpp
namespace foo {

enum class EnumWithStringify { kMany = 0, kChoices = 1 };

template <typename Sink>
void AbslStringify(Sink& sink, EnumWithStringify e) {
  switch (e) {
    case EnumWithStringify::kMany:
      sink.Append("kMany");
      break;
    case EnumWithStringify::kChoices:
      sink.Append("kChoices");
      break;
  }
}

}  // namespace foo
```

If you can't declare the function in the class it's important that
`AbslStringify()` is defined in the **same** namespace that defines Point. C++'s
look-up rules rely on that.

Now these types will print correctly as defined with all the supported
libraries.

Examples using `Point`:

```cpp
// Strings and StrFormat
absl::StrFormat("The point is %v", p);
absl::StrCat("The point is ", p);
absl::StrAppend(&str, p);
absl::Substitute("The point is $0", p);

// Logging
LOG(INFO) << "The point is " << p;

// GoogleTest
EXPECT_EQ(p, expected); // error message prints type according to AbslStringify
testing::PrintToString(p);
```

Important: When using `absl::StrFormat` for user-defined types, use the `%v`
type specifier to format using `AbslStringify()`; using `%s` is not supported.
See https://abseil.io/docs/cpp/guides/format for more details.

Additionally, an implementation of `AbslStringify()` using `absl::Format` can
use `%v` within the format string argument to perform type deduction. Our
`Point` above could be formatted as `"(%v, %v)"` for example, which would give
the same output as `"(%d, %d)"` in this case where we are formatting the `int`
values `x` and `y`.

Note: `CHECK_EQ(p, expected)` does not currently support `AbslStringify`-enabled
types. `CHECK(p == expected) << p << "==" << expected` can be used for similar
error-checking and logging capabilities.

For more information about `AbslStringify`'s integration with any of these
libraries, please refer to the documentation of the relevant library.

### `AbslStringify`'s Sink

`AbslStringify`'s underlying `Sink` supports `Append` operations, as well as
`absl::Format`:

```cpp
// Append 3 copies of 'a'
sink.Append(3, 'a')

// Append "hello"
sink.Append("hello")

// Append "hello world"
absl::Format(&sink, "hello %s", "world")
```

Warning: User-defined sinks are not supported.

## Types with Built-In Support

### Protocol Buffers

Protocol buffer messages define `AbslStringify()` by default, so they can be
formatted by all libraries that use this extension point. This is an overall
smoother user experience over `DebugString()` as it produces less noisy code. It
is recommended that users format protocol buffers directly rather than
calling `DebugString()`.

```proto
message MyProto {
  optional string my_string = 1
}
```

```cpp
MyProto my_proto;
my_proto.set_my_string("hello world");

absl::StrCat("My proto is: ", my_proto);
absl::StrFormat("My proto is: %v", my_proto);
LOG(INFO) << "My proto is: " << my_proto;
EXPECT_THAT(my_proto, EqualsProto(expected_proto))
```
