---
title: "The Abseil str_format Library"
layout: blog
sidenav: side-nav-blog.html
published: true
permalink: blog/20180620-strformat
type: markdown
category: blog
excerpt_separator: <!--break-->
---

By [Juemin Yang](mailto:jueminyang@google.com), Abseil Engineer

Abseil now includes a type-safe string formatting library: `str_format`.
The `str_format` library is a typesafe replacement for the family of
`printf()` string formatting routines within the `<cstdio>` standard
library header. The `str_format` library provides most of the functionality
of `printf()` type string formatting and a number of additional benefits:

* Type safety, including native support for `std::string` and `absl::string_view`
* Reliable behavior independent of standard libraries
* Support for the POSIX positional extensions
* Supports google3 types such as Cord, natively and can be extended to support other types.
* Much faster (generally 2 to 3 times faster) than native `printf` functions
* Streamable to a variety of existing sinks
* Extensible to other future sinks

For more information, consult Abseil's [StrFormat Guide](/docs/cpp/guides/format)
If you are interested in the design of this library,
check out our [StrFormat Design Notes](/about/design/strformat).


