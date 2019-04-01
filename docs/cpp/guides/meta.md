---
title: "The Meta Library"
layout: docs
sidenav: side-nav-cpp.html
type: markdown
---

# The Meta Library

This `meta` library contains C++11-compatible versions of standard
`<type_traits>` API functions for determining the characteristics of types. Such
traits can support type inference, classification, and transformation, as well
as make it easier to write templates based on generic type behavior.

See https://en.cppreference.com/w/cpp/header/type_traits

>WARNING: use of many of the constructs in this header will count as "complex
>template metaprogramming", so before proceeding, please carefully consider
>https://google.github.io/styleguide/cppguide.html#Template_metaprogramming
>
>Using template metaprogramming to detect or depend on API
>features is brittle and not guaranteed. Neither the standard library nor
>Abseil provides any guarantee that APIs are stable in the face of template
>metaprogramming. Use with caution.

## Type Trait Usage

Type traits were introduced in C++11 to provide compile-time inspection of the
properties of types. This header file contains two sets of abstractions:

* C++11 compatible versions of `<type_traits>` methods that were either not
  supported or in C++11 or were not fully-supported.
* C++11 compatible definitions of C++14 and C++17 `<type_traits>` aliases

## Type Traits Class Templates

* `absl::void_t` provides a version of the C++17 `std::void_t` utility
  metafunction.
* `absl::conjunction`, `absl::disjunction` and `absl::negation` provide versions
  of the C++17 abstractions for performing compile-time logical operations.
* `absl::is_trivially_destructible`, `absl::is_trivially_default_constructible`,
  `absl::is_trivially_assignable`, and `absl::is_trivially_copy_assignable`
  provide versions of these type traits metafunctions that include fixes for
  platforms that did not fully-implement them.

## C++14 `_t` type aliases

The Abseil `meta` library provides C++11 versions of `<type_traits>` aliases
added to C++14. These aliases allow you to more easily (and intuitively) get
the type of a `type_traits` class template.

For example:

```cpp
// decay_t is the type of std::decay<T>
template <typename T>
using decay_t = typename std::decay<T>::type;
```

The Abseil `meta` library provides aliases for the following type traits that
yield a type:

* `absl::remove_cv_t`
* `absl::remove_const_t`
* `absl::remove_volatile_t`
* `absl::add_cv_t`
* `absl::add_const_t`
* `absl::add_volatile_t`
* `absl::remove_reference_t`
* `absl::add_lvalue_reference_t`
* `absl::add_rvalue_reference_t`
* `absl::remove_pointer_t`
* `absl::add_pointer_t`
* `absl::make_signed_t`
* `absl::make_unsigned_t`
* `absl::remove_extent_t`
* `absl::remove_all_extents_t`
* `absl::aligned_storage_t`
* `absl::decay_t`
* `absl::enable_if_t`
* `absl::conditional_t`
* `absl::common_type_t`
* `absl::underlying_type_t`
* `absl::result_of_t`
