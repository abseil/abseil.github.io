---
title: "The Meta Library"
layout: docs
sidenav: side-nav-cpp.html
type: markdown
---

# The Meta Library

This `meta` library contains C++14-compatible versions of standard
[`<type_traits>`][type_traits] API functions for determining the characteristics
of types. Such traits can support type inference, classification, and
transformation, as well as make it easier to write templates based on generic
type behavior.

> WARNING: use of many of the constructs in this header will count as "complex
> template metaprogramming", so before proceeding, please carefully consider the
> Style Guide's [advice on template metaprogramming][style-guide-templates].
>
> Using template metaprogramming to detect or depend on API features is brittle
> and not guaranteed. Neither the standard library nor Abseil provides any
> guarantee that APIs are stable in the face of template metaprogramming. Use
> with caution.

## Type Trait Usage

Type traits in C++ provide compile-time inspection of the properties of types.
This header file contains two sets of abstractions:

*   C++14 compatible versions of `<type_traits>` methods that either aren't
    available in C++14, or which have incomplete compiler support.
*   C++14 compatible definitions of C++17 `<type_traits>` aliases

## Type Traits Class Templates

*   `absl::void_t` provides a version of the C++17 `std::void_t` utility
    metafunction.
*   `absl::conjunction`, `absl::disjunction` and `absl::negation` provide
    versions of the C++17 abstractions for performing compile-time logical
    operations.
*   `absl::is_trivially_destructible`,
    `absl::is_trivially_default_constructible`, `absl::is_trivially_assignable`,
    and `absl::is_trivially_copy_assignable` provide versions of these type
    traits metafunctions that include fixes for platforms that did not
    fully-implement them.

[type_traits]: https://en.cppreference.com/w/cpp/header/type_traits
[style-guide-templates]: https://google.github.io/styleguide/cppguide.html#Template_metaprogramming
