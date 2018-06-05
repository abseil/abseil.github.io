---
title: Introduction to Abseil
layout: about
sidenav: side-nav-about.html
type: markdown
---

Welcome to Abseil! Abseil is an open-source collection of C++ code (compliant to
C++11) designed to augment the C++ standard library. This document introduces
Abseil and provides an overview of the code we're providing.

## Table of Contents

- [Codemap](#codemap)
- [License](#license)
- [Links](#links)

## Codemap

The Abseil codebase consists of the following C++ library components:

* [`base`](https://github.com/abseil/abseil-cpp/tree/master/absl/base) Abseil
  Fundamentals<br /> The `base` library contains initialization code and other
  code which all other Abseil code depends on. Code within `base` may not depend
  on any other code (other than the C++ standard library).
* [`algorithm`](https://github.com/abseil/abseil-cpp/tree/master/absl/algorithm)
  <br /> The `algorithm` library contains additions to the C++ `<algorithm>`
  library and container-based versions of such algorithms.
* [`container`](https://github.com/abseil/abseil-cpp/tree/master/absl/container)
  <br /> The `container` library contains additional STL-style containers.
* [`debugging`](https://github.com/abseil/abseil-cpp/tree/master/absl/debugging)
  <br /> The `debugging` library contains code useful for enabling leak
  checks. Future updates will add stacktrace and symbolization utilities.
* [`memory`](https://github.com/abseil/abseil-cpp/tree/master/absl/memory)
  <br /> The `memory` library contains C++11-compatible versions of
  `std::make_unique()` and related memory management facilities.
* [`meta`](https://github.com/abseil/abseil-cpp/tree/master/absl/meta)
  <br /> The `meta` library contains C++11-compatible versions of type checks
  available within C++14 and C++17 versions of the C++ `<type_traits>` library.
* [`numeric`](https://github.com/abseil/abseil-cpp/tree/master/absl/numeric)
  <br /> The `numeric` library contains C++11-compatible 128-bit integers.
* [`strings`](https://github.com/abseil/abseil-cpp/tree/master/absl/strings)
  <br /> The `strings` library contains a variety of strings routines and
  utilities, including a C++11-compatible version of the C++17
  `std::string_view` type.
* [`synchronization`](https://github.com/abseil/abseil-cpp/tree/master/absl/synchronization)
  <br /> The `synchronization` library contains concurrency primitives (Abseil's
  `absl::Mutex` class, an alternative to `std::mutex`) and a variety of
  synchronization abstractions.
* [`time`](https://github.com/abseil/abseil-cpp/tree/master/absl/time)
  <br /> The `time` library contains abstractions for computing with absolute
  points in time, durations of time, and formatting and parsing time within
  time zones.
* [`types`](https://github.com/abseil/abseil-cpp/tree/master/absl/types)
  <br /> The `types` library contains non-container utility types, like a
  C++11-compatible version of `absl::optional`.

## License

The Abseil C++ library is licensed under the terms of the Apache
license. See [LICENSE](https://github.com/abseil/abseil-cpp/blob/master/LICENSE)
for more information.

## Links

For more information about Abseil:

* Walk through the Abseil [C++ Quickstart](/docs/cpp/quickstart) to set up your
  development environment and test out the code.
* Read [Why Adopt Abseil](/about/philosophy) to understand our design
  philosophy.
* Peruse our [Abseil Compatibility Guidelines](/about/compatibility) to
  understand both what we promise to you, and what we expect of you in return.
