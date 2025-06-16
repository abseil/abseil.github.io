---
title: "Abseil Stringify"
layout: blog
sidenav: side-nav-blog.html
published: true
permalink: blog/11152022-stringify
type: markdown
category: blog
excerpt_separator: <!--break-->
---

By [Phoebe Liang](mailto:phoebeliang@google.com), Abseil Engineer

We are pleased to introduce an easier way to format user-defined types as strings in
Abseil: `AbslStringify()`. This API allows user-defined types to be printed more
easily using `absl::StrFormat()` and `absl::StrCat()`. 

To “stringify” a custom type, define a friend function template named
`AbslStringify(`):

```cpp
struct Point 
  template <typename Sink>
  friend void AbslStringify(Sink& sink, const Point& p) {
    absl::Format(&sink, "(%d, %d)", p.x, p.y);
  }

  int x;
  int y;
}
```

`absl::StrCat()` will work right out of the box like so:  

```cpp
absl::StrCat("The point is ", p);
```

To print custom types with `absl::StrFormat()`, use the new type specifier `%v`: 

```cpp
absl::StrFormat("The point is %v", p);
```

`%v` uses type deduction to print an argument and supports any user-defined type
that provides an `AbslStringify()` definition. Most types that are supported
natively by `absl::StrFormat()` are also supported by `%v`. For a full list of
supported types, see the [StrFormat Guide](https://abseil.io/docs/cpp/guides/format). 
