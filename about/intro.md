---
title: "Introduction to Abseil"
layout: about
sidenav: side-nav-about.html
type: markdown
---

# Introduction to Abseil

Welcome to Abseil! Abseil is an open-source collection of C++ code (compliant to
C++17) designed to augment the C++ standard library. This document introduces
Abseil and provides an overview of the code we're providing.

## Table of Contents

- [Codemap](#codemap)
- [License](#license)
- [Links](#links)

## Codemap

The Abseil codebase consists of the following C++ library components:

*   [`base`](https://github.com/abseil/abseil-cpp/tree/master/absl/base) Abseil
    Fundamentals<br /> The `base` library contains initialization code and other
    code which all other Abseil code depends on. Code within `base` may not depend
    on any other code (other than the C++ standard library).
*   [`algorithm`](https://github.com/abseil/abseil-cpp/tree/master/absl/algorithm)
    <br /> The `algorithm` library contains additions to the C++ `<algorithm>`
    library and container-based versions of such algorithms.
*   [`container`](https://github.com/abseil/abseil-cpp/tree/master/absl/container)
    <br /> The `container` library contains additional STL-style containers.
*   [`debugging`](https://github.com/abseil/abseil-cpp/tree/master/absl/debugging)
    <br /> The `debugging` library contains code useful for enabling leak
    checks, and stacktrace and symbolization utilities.
*   [`hash`](https://github.com/abseil/abseil-cpp/tree/master/absl/hash)
    <br /> The `hash` library contains the hashing framework and default hash
    functor implementations for hashable types in Abseil.
*   [`memory`](https://github.com/abseil/abseil-cpp/tree/master/absl/memory)
    <br /> The `memory` library contains memory management facilities that
    augment C++'s `<memory>` library.
*   [`meta`](https://github.com/abseil/abseil-cpp/tree/master/absl/meta)
    <br /> The `meta` library contains type checks similar to those available in
    the C++ `<type_traits>` library.
*   [`numeric`](https://github.com/abseil/abseil-cpp/tree/master/absl/numeric)
    <br /> The `numeric` library contains 128-bit integer types as well as
    implementations of C++20's bitwise math functions.
*   [`strings`](https://github.com/abseil/abseil-cpp/tree/master/absl/strings)
    <br /> The `strings` library contains a variety of strings routines and
    utilities.
*   [`synchronization`](https://github.com/abseil/abseil-cpp/tree/master/absl/synchronization)
    <br /> The `synchronization` library contains concurrency primitives (Abseil's
    `absl::Mutex` class, an alternative to `std::mutex`) and a variety of
    synchronization abstractions.
*   [`time`](https://github.com/abseil/abseil-cpp/tree/master/absl/time)
    <br /> The `time` library contains abstractions for computing with absolute
    points in time, durations of time, and formatting and parsing time within
    time zones.
*   [`types`](https://github.com/abseil/abseil-cpp/tree/master/absl/types)
    <br /> The `types` library contains non-container utility types.
*   [`utility`](https://github.com/abseil/abseil-cpp/tree/master/absl/utility)
    <br /> The `utility` library contains utility and helper code.

## License

The Abseil C++ library is licensed under the terms of the Apache
license. See [LICENSE](https://github.com/abseil/abseil-cpp/blob/master/LICENSE)
for more information.

## Links

For more information about Abseil:

* Walk through the Abseil [C++ Quickstart](/docs/cpp/quickstart) to set up your
  development environment and test out the code.
* Read [Why Adopt Abseil](philosophy) to understand our design
  philosophy.
* Peruse our [Abseil Compatibility Guidelines](compatibility) to
  understand both what we promise to you, and what we expect of you in return.
