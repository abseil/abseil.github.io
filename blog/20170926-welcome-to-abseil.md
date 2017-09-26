---
title: Welcome to Abseil!
layout: blog
sidenav: side-nav-blog.html
type: markdown
---

## #1 - Introducing Abseil
### A New Common Libraries Project


By [Titus Winters](mailto:titus@google.com), Abseil Lead

Today we are open sourcing [Abseil](https://abseil.io), a collection of 
libraries drawn from the most fundamental pieces of Google's internal codebase. 
These libraries are the nuts-and-bolts that underpin almost everything that 
Google runs. Bits and pieces of these APIs are embedded in most of our open 
source projects, and now we have brought them together into one comprehensive 
project. Abseil encompasses the most basic building blocks of Google's 
codebase: code that is production tested and will be fully maintained for years 
to come.

Our C++ code repository is available at
[https://github.com/abseil/abseil-cpp](https://github.com/abseil/abseil-cpp).

By adopting these new Apache-licensed libraries, you can reap the benefit of years (over a decade in many cases) of our design and optimization work in this space. Our past experience is baked in.

Just as interesting, we've also prepared for the future: several types in
 Abseil's C++ libraries are "pre-adoption" versions of C++17 types like 
 [`string_view`](http://en.cppreference.com/w/cpp/string/basic_string_view) and 
 [`optional`](http://en.cppreference.com/w/cpp/utility/optional) - implemented 
 in C++11 to the greatest extent possible. We look forward to moving more and 
 more of our code to match the current standard, and using these new vocabulary 
 types helps us make that transition. Importantly, in C++17 mode these types 
 are merely aliases to the standard, ensuring that you only ever have one type 
 for `optional` or `string_view` in a project at a time. Put another way: 
 Abseil is focused on the engineering task of providing APIs that remain stable 
 **over time**.

Consisting of the foundational C++ and Python code at Google, Abseil includes 
libraries that will grow to underpin other Google-backed open source projects 
like [gRPC](https://grpc.io/), [Protobuf](https://github.com/google/protobuf) 
and [TensorFlow](https://www.tensorflow.org/). We love those projects, and we 
love the users of those projects - we want to ensure smooth usage for these 
things over time. In the next few months we'll introduce new distribution 
methods to incorporate these projects as a collection into your project.

Continuing with the "over time" theme, Abseil aims for compatibility with major 
compilers, platforms and standard libraries for approximately 5 years. Our 
5-year target also applies to language version: we assume everyone builds with 
C++11 at this point. (In 2019 we'll start talking about requiring C++14 as our 
base language version.) This 5-year horizon is part of our balance between 
"support everything" and "provide modern implementations and APIs." 

Highlights of the initial release include:

* Zero configuration: most platforms (OS, compiler, architecture) should just 
  work.
* [Pre-adoption for C++17 types](/about/design/dropin-types): `string_view`, 
  `optional`, `any`. We'll follow up with `variant` soon.
* Our primary synchronization type, [`absl::Mutex`](/about/design/mutex), has 
  an elegant interface and has been extensively optimized.
* Efficient support for handling time: `absl::Time` and `absl::Duration` are 
  conceptually similar to `std::chrono` types, but are concrete (not class 
  templates) and have defined behavior in all cases. Additionally, our 
  clock-sampling API `absl::Now()` is more heavily optimized than most standard 
  library calls for `std::chrono::system_clock::now()`.
* String handling routines: among internal users, we've been told that 
  releasing `absl::StrCat()`, `absl::StrJoin()`, and `absl::StrSplit()` would 
  itself be a big improvement for the open source C++ world.

The project has support for C++ and some Python. Over time we'll tie those two 
projects together more closely with shared logging and command-line flag 
infrastructure. To start contributing, please see our contribution guidelines 
and fork us on [GitHub](https://github.com/abseil/). Check out our 
[documentation](/docs) and [community page](/community) for information on how 
to contact us, ask questions or contribute to Abseil. 
