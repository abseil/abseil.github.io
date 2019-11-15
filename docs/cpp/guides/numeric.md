---
title: "The Numeric Library"
layout: docs
sidenav: side-nav-cpp.html
type: markdown
---

# The Numeric Library

The `//absl/numeric` library provides only one header file at this time:

* int128.h provides 128-bit integer types

## 128-bit Integers

The `int128.h` header file defines signed and unsigned 128-bit integer types.
The APIs are meant to mimic intrinsic types as closely as possible, so that any
forthcoming standard type can be a drop-in replacement. A key difference is that
some categories of conversion are explicit, as noted below.

### `uint128`

The `uint128` type defines an unsigned 128-bit integer supporting the following:

*   Implicit conversion from integral types
*   Explicit conversion to integral types
*   Explicit conversion to and from floating point types
*   Overloads for `std::numeric_limits`

Additionally, if your compiler supports the `__int128` type extension, `uint128`
is interoperable with that type.

128-bit integer literals are not yet a part of the C++ language. As a result, to
construct a 128-bit unsigned integer with a value greater than or equal to 2^64,
you should use the `absl::MakeUint128()` factory function.

Examples:

```cpp
uint64_t a;

// Implicit conversion from uint64_t OK
absl::uint128 v = a;

// Error: Implicit conversion to uint64_t not OK
uint64_t b = v;

// Explicit conversion to uint64_t OK
uint64_t i = static_cast<uint64_t>(v);

// Construct a value of 2^64
absl::uint128 big = absl::MakeUint128(1, 0);

// Get the high and low 64 bits of a uint128
uint64_t high = absl::Uint128High64(v);
uint64_t low = absl::Uint128Low64(v);
```

### `int128`

The `int128` type defines a signed 128-bit integer supporting the following:

*   Implicit conversion from signed integral types and unsigned types narrower
    than 128 bits
*   Explicit conversion from unsigned 128-bit types
*   Explicit conversion to integral types
*   Explicit conversion to and from floating point types
*   Overloads for `std::numeric_limits`

Additionally, if your compiler supports the `__int128` type extension, `int128`
is interoperable with that type.

128-bit integer literals are not yet a part of the C++ language. As a result, to
construct a 128-bit signed integer with a value greater than or equal to 2^64,
you should use the `absl::MakeInt128()` factory function.

Examples:

```cpp
int64_t a;

// Implicit conversion from int64_t OK
absl::int128 v = a;

// Error: Implicit conversion to int64_t not OK
int64_t b = v;

// Explicit conversion to int64_t OK
int64_t i = static_cast<int64_t>(v);

// Construct a value of 2^64
absl::int128 big = absl::MakeInt128(1, 0);

// Get the high and low 64 bits of an int128
int64_t high = absl::Int128High64(v);
uint64_t low = absl::Int128Low64(v);
```
