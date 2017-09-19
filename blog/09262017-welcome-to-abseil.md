---
title: Welcome to Abseil!
layout: blog
sidenav: side-nav-blog.html
type: markdown
---

## #1 - Introducing Abseil
### A New Common Libraries Project

[Titus Winters](mailto:titus@google.com) - 09-26-2017

Today we are open-sourcing Abseil, a collection of libraries drawn from the
most fundamental pieces of Google’s internal codebase.  These libraries are the
nuts-and-bolts that underpin almost everything that Google runs.  Bits and
pieces of these APIs are embedded in most of our Open Source projects, and now
we have collected them all together into one comprehensive and maintained
project.  Abseil encompasses the most basic building blocks of Google’s
codebase: code that is production tested and will be fully maintained for years
to come.

By adopting these new Apache-licensed libraries, you can reap the benefit of
years (over a decade in many cases) of our design and optimization work in this 
space: our past experience is baked in. Just as interesting: we’ve also baked
in our plans for the future.  Several types in Abseil’s C++ libraries are
“pre-adoption” versions of C++17 types like `string_view` and `optional` -
implemented in C++11 to the greatest extent possible.  We look forward to
moving more and more of our code to match the current standard, and using these
new vocabulary types helps us do that transition.  Importantly, in C++17 mode
these types are merely aliases to the standard, ensuring that you only ever
have one type for `optional` or `string_view` in a project at a time.  Put
another way: Abseil is focused on the engineering task of providing APIs that
work over time.

As the most-fundamental pieces of vocabulary in C++ and Python, Abseil consists
of libraries that will grow to underpin other Google-backed OSS projects like
gRPC, Protobuf, and TensorFlow.  We love those projects, and we love the users
of those projects - we want to ensure smooth usage for these things over time.
In the next few months we’ll introduce new distribution methods to incorporate
these projects as a collection into your project.

Continuing with the “over time” theme, Abseil will promise compatibility with
major compilers, platforms, and standard libraries for several years.
Generally speaking our rule is “5 years without a good reason” - MSVC only gets
2-3 years right now because we depend so heavily on C++11 features that were
not well supported until 2015.  Our 5-year promise also applies to language
version: we assume everyone builds with C++11 at this point.  In 2019 we’ll
start talking about dropping C++11 support - once we’ve got a 5-year history
for C++14 we need to start cutting legacy support.  This 5-year horizon is part
of our balance between “support everything” and “provide modern implementations
and APIs”. 

Highlights of the initial release include:

* Zero configuration:  most platforms (OS, compiler, architecture) should just 
  work
* [Pre-adoption for C++17 types](/about/design/std-drop-ins): `string_view`, 
  `optional`, `any`.  We’ll follow up with `variant` soon.
* Our primary synchronization type: []`absl::Mutex`](/about/design/mutex) has
  an elegant interface and has been extensively optimized for our production
  requirements.
* Efficient support for handling time: `absl::Time` and absl::Duration are
  conceptually similar to `std::chrono` types, but are concrete (not class 
  templates) and have defined behavior in all cases.  Additionally, our 
  clock-sampling API `absl::Now()` is more heavily optimized than most standard 
  library calls for `std::chrono::system_clock::now()`.
* String handling routines: among internal users, we’ve been told that 
  releasing `absl::StrCat()`, `absl::StrJoin()`, and `absl::StrSplit()` would 
  itself be a big improvement for the open-source C++ world.

The project has support for C++ and some Python. Over time we’ll tie those two 
projects together more closely with shared logging and command-line flag 
infrastructure. To start contributing, please see our contribution guidelines
and [fork us on github](https://github.com/abseil).  Check out our
[documentation](/index) and how to [get in touch with us](/community). 

