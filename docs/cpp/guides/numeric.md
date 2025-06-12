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

The `uint128` type represents an unsigned 128-bit integer. The API is meant to
mimic an intrinsic integer type as closely as possible, so that any forthcoming
`uint128_t` can be a drop-in replacement.

The `uint128` type supports the following:

*   Implicit conversion from integral types
*   Overloads for `std::numeric_limits`

However, a `uint128` differs from intrinsic integral types in the following
ways:

* It is not implicitly convertible to other integral types, including other
  128-bit integral types. Conversions must be explicit.
* It requires explicit construction from and conversion to floating point types.
* The type traits `std::is_integral<uint128>::value` and
  `std::is_arithmetic<uint128>::value` are both `false`.

Additionally, if your compiler supports the `__int128` type extension, `uint128`
is interoperable with that type, though `uint128` will not be a typedef in this
case. (Abseil checks for this compatibility through the
`ABSL_HAVE_INTRINSIC_INT128` macro.)

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

The `int128` type defines a signed 128-bit integer. The API is meant to
mimic an intrinsic integer type as closely as possible, so that any forthcoming
`int128_t` can be a drop-in replacement.

The `int128` type supports the following:

*   Implicit conversion from signed integral types and unsigned types narrower
    than 128 bits
*   Overloads for `std::numeric_limits`

However, an `int128` differs from intrinsic integral types in the following
ways:

* It is not implicitly convertible to other integral types, including other
  128-bit integral types. Conversions must be explicit.
* It requires explicit construction from and conversion to floating point types.
* The type traits `std::is_integral<int128>::value` and
  `std::is_arithmetic<int128>::value` are both `false`.

If your compiler supports the `__int128` type extension, `int128` is
interoperable with that type, though `int128` will not be a typedef in this
case. (Abseil checks for this compatibility through
the `ABSL_HAVE_INTRINSIC_INT128` macro.)

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
