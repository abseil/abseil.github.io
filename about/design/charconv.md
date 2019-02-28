---
title: "`charconv` Design Notes"
layout: about
sidenav: side-nav-design.html
type: markdown
---

# `charconv` Design Notes

The Abseil `charconv` library provides C++11-compatible vesion of the C++17
`<charconv>` library header, adding light-weight parsers and formatters for
arithmetic types. In specific, this library contains a C++11-compatible version
of `std::from_chars` to convert from a string to an arithmetic type (in this
case a `double`). This design note describes the algorithm used for that
conversion and design decisions made in its implementation.

## `from_chars` Overview

The `absl::from_chars()` algorithm will convert any decimal floating-point
string to the exact representable double that is nearest to the value of the
input string. (In the case of ties, we round to the representation whose
mantissa is even.)

To make an initial guess in the `absl::from_chars` decimal-to-binary conversion,
we do hand-rolled floating point math using a `uint128` to store our mantissa.

To determine whether this initial guess is guaranteed to be the correctly
rounded value, or instead if we must resort to high-precision integer math to
make this determination, we establish lower bounds on the number of bits of
accuracy we will get out of our multiplication.

## Hand-rolled Floating Point

We represent our hand-rolled `float` values as the product of an integer (the
mantissa) and a power of two. (We do not store a radix point). These values are
calculated according to the constraints noted below.

### Mantissas

The algorithm always reads the mantissa as an integer, doing a decimal-point
adjustment if necessary. (For example, `1.25e-1` is calculated as `125e-3`.)

We will read up to 19 significant digits of mantissa from the input. Significant
digits beyond this point are dropped, in which case the integral mantissa we use
in calculations is a truncated representation of the true value. The
relationship in this case is:

`DM_true = DM_trunc + DM_error` (DM is intended as an abbreviation for
"decimal mantissa").

Where `DM_trunc` is an integer in the range `[10**18, 10**19)`, and `DM_error`
is a real number in the range `(0.0, 1.0)`.

### Powers of Ten

The algorithm relies on a lookup table of powers of ten, stored in our internal
floating-point representation. For each power of ten in the range of our
calculation, we have a precalculated mantissa and exponent, such that `10**N` is
approximately `EM[N] * 2**EE[N]`. `EM` is chosen to be a lower bound guess. The
exact bounds are: (EM and EE are intended as abbreviations for "exponent
mantissa" and "exponent exponent".)

```
EM * 2**EE <= 10**N < (EM + 1) * 2**EE
```

For values of N between 0 and 27 inclusive, the representation `EM * 2**EE` is
exact. For numbers outside this range, EM is a truncated representation of the
true value.

The error bound relationship is:

```
EM_true = EM_trunc + EM_error
```

Where `EM_trunc` is an integer in the range `[2**63, 2**64)`, and `EM_error` is
a real number in the range `[0.0, 1.0)`. (When N is less than 0 or greater than
27, `EM_error` is nonzero.)

## Calcluating Error Bounds

To generate an initial floating point guess, we multiply the parsed mantissa by
the appropriate power of ten. This gives us a `uint128` value, but due to errors
in truncation for both the mantissa and power of ten value, we may only rely on
a certain number of bits of precision. We calculate this error bounds below.

### Inexact Decimal Mantissa

When the input mantissa is inexact, our calculated binary mantissa will be

```
guess = DM_trunc * EM_trunc
```

But the exact value of the mantissa should be

```
exact = (DM_trunc + DM_error) * (EM_trunc + EM_error)
```

which means our guess has an error of

```
error = exact - guess

error = DM_trunc * EM_error + EM_trunc * DM_error + DM_error * EM_error
```

Because both our mantissa and exponent are truncated from the actual value, our
guess is low, and error is always positive.

`DM_trunc` and `EM_trunc` have minimum values as described above, which ensure
that the integer `guess` has no fewer than 123 significant bits.

Likewise, because all arguments in `error` have an upper bound, we can plug
these values in and deduce that `error < 2**65`, or in other words that our
error affects no more than the low 65 significant bits of our product.

Therefore, the high 58 bits of our product are either the correct high 58 bits
of the true product, or are one less than the correct value (in the case that
the addition of the error value carries into these bits).

A double precision IEEE float only has 53 bits of significant mantissa. The
remaining five bits can usually tell us the correct rounding direction.

If the low five bits are in the range `0b00000` to `0b01110`, then we know the
correct rounding direction is down, and the high 53 bits of our product are the
correct binary mantissa bits for our conversion. Likewise, if the low five bits
are in the range `0b10001` to `0b11111`, we know the correct rounding direction
is up.

More subtly, if the low five bits are `0b10000`, we would normally have to
decide whether the correct rounding direction is "up" or "toward even". However,
this code path requires that our mantissa is inexact, so we know that `DM_error`
is nonzero, and so also is `error`. The correct value must therefore be some
epsilon greather than the value in our high 58 bits, and the correct rounding
direction must be up as well.

Only if the low five bits are `0b01111` does the error prevent us from guessing
a rounding direction. In this case we must resort to exact integer math.

### Exact Decimal Mantissa, Inexact Power of Ten

When the input mantissa is 19 or fewer digits wide (the common case), then our
error bounds are lessened:

```
guess = DM_true * EM_trunc

exact = DM_true * (EM_trunc + EM_error)

error = DM_true * EM_error
```

Because `EM_trunc` is at least `2**63`, and because `EM_error` is less than one,
we know that our guess is no less than `DM_true << 63` and our error is no
greater than `DM_true`. From this, we can establish that the high 63 bits of our
product are reliable: again, they are either exact or one less than correct (in
the case of carry).

The rounding considerations are the same as before, except for the larger number
of bits we can consider.

### Exact Decimal Mantissa, Exact Power of Ten

When the input mantissa in 19 and the decimal exponent is between 0 and 27
inclusive, then there is no truncation error, and our product is exact.

The high 53 bits are our guess, and the remaining bits are used to choose the
correct rounding direction. If the remaining bits are exactly `0b10000000...`,
then we should round to even. (That is, if the low bit of our 53-bit guess is a
0, we round down; if it's a 1, we round up.)

## Handling Rounding Ambiguities

In the case where the above algorithm cannot determine a rounding direction, we
must resort to high-precision integer math.

The idea is to calculate the exact value of the real number that lies halfway
between the two adjacent candidate double representations, and compare that to
the exact value of the parsed input. The result of this comparison tells us the
rounding direction.

The comparison we are calculating is:

```
binary_mantissa * 2**binary_exponent <=> decimal_mantissa * 10**decimal_exponent
```

In the case where `binary_exponent` and/or `decimal_exponent` are negative, they
can be moved to the other side of the equation to make the exponent positive. In
this way, our calculation contains only integers.

Further memory can be saved by converting the power of 10 to
`5**decimal_exponent * 2**decimal_exponent`, and cancelling out the powers of 2
where possible. The powers of 2 result in a single left shift; left shifts of
greater than 32 bits can be represented by virtual word shifts; we need not
actually reserve room for the all-bits-zero `uint32_t`s that result.

A design goal of `absl::from_chars` is to avoid memory allocations. To do this,
we use fixed size big-integer math, with enough memory reserved on the stack to
avoid overflow. Because the size of the decimal mantissa is controlled by the
caller of `from_chars`, we must truncate this input.

We only need to read enough digits from the decimal_mantissa so that we can
capture the exact decimal representation of any real number halfway between two
floats. The largest such numbers live near zero. The number halfway between
`DBL_MIN` and the next representable double has an exact decimal mantissa of 768
digits. Therefore we only have to read 768 significant decimal digits to
correctly calculate rounding direction.

There is a pathological input case which takes a number halfway between two
representable reals which would normally round down, and appending to its
mantissa a very long run of 0s followed by a nonzero digit. This extra digit
should change the rounding direction. To account for this case without needing
to read arbitrary precision mantissas, we use a sticky digit strategy. If the
768th significant digit is a '0' or '5', and if any of the dropped digits beyond
this point are nonzero, we adjust the 768th digit upward to a '1' or '6'. This
causes us to choose the correct rounding direction in all cases, without
requiring extra storage.

Arbitrary 768-digit integers require 2552 bits of precision, which can be stored
in a big integer class comprised of 80 `uint32_t`s.

Note that during scanning, we adjust the input so the mantissa is an integer.
The largest representable double is less than `1.8e308`, so once we have read
more than 308 significant digits from the mantissa, the decimal exponent has
necessarily been adjusted to be negative, so we will never overflow by
multiplying a very big int by a power of 5. (The power of 5 will have been moved
to the other side of the equation. Our initial guess routine detects obvious
cases of overflow and underflow and short circuits, avoiding falling to useless
big-integer math.)

As an easy future optimization, we could reduce the number of significant digits
we read dynamically, based on the power of two exponent in our initial guess.
The farther we are from the extremes, the fewer digits of precision are needed
to exactly represent a real number between two doubles.
