---
title: Type Libraries
layout: docs
sidenav: side-nav-cpp.html
type: markdown
---

This guide covers a variety of Abseil libraries related to types, including:

* `numeric`
* `algorithm`
* `container`
* `types`
* `meta`


## The Numeric Library

The `//absl/numeric` library provides only one header file at this time:

* int128.h provides 128-bit integer types

### 128-bit Integers

The `int128.h` header file defines 128-bit integer types, for use until
intrinsic 128-bit types are part of the C++ standard. Currently, this file
defines only one type: `uint128`, an unsigned 128-bit integer; a signed 128-bit
integer is forthcoming.

#### `uint128`

The `uint128` type defines an unsigned 128-bit integer. The API is meant to
mimic an intrinsic type as closely as possible, so that any forthcoming
`uint128_t` can be a drop-in replacement. (`uint128` will be removed once C++
supports such a type.)

Note: code written with this type will continue to compile once `uint128_t`
is introduced, provided the replacement helper functions `Uint128(Low|High)64()`
and `MakeUint128()` are made.

A `uint128` supports the following:

* Implicit constructio* `algorithm`n from integral types
* Explicit conversion to integral types

Additionally, if your compiler supports the `__int128` type extension, `uint128`
is interoperable with that type.

128-bit integer literals are not yet a part of the C++ language. As a result,
to construct a 128-bit unsigned integer with a value greater than 2^64, you will
need to use the `absl::MakeUint128()` factory function.

Examples:

```cpp
uint64_t a;

// Implicit conversion from uint64_t OK
uint128 v = a;

// Error: Implicit conversion to uint64_t not OK
uint64_t b = v;

// Explicit conversion to uint64_t OK
uint64_t i = static_cast<uint64_t>(v);

// Construct a value of 2^64
absl::uint128 big = absl::MakeUint128(1, 0);
```

## The Algorithm Library

## The Container Library

## The Types Library

## The Meta Library