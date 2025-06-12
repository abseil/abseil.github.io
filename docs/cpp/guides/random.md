---
title: "The Abseil Random Library"
layout: docs
sidenav: side-nav-cpp.html
type: markdown
---

# The Abseil Random Library

The Abseil Random library provides functions and utilities for generating
pseudorandom data. This library is designed to be used as a replacement for the
random number generators and distribution functions within the
[`<random>`](http://en.cppreference.com/w/cpp/numeric/random) library, while
maintaining compatibility with that library.

The Abseil Random library provides several advantages over `<random>`:

* **Improved algorithms**<br/>
  The Abseil Random library provides improved pseudorandom algorithms, and
  allows us to adopt new algorithms as they become available. Random value
  generation is an area of active research, and today's algorithms initialize
  more quickly, generate values faster, and produce sequences that are
  statistically more difficult to guess.
* **Easy construction of well-seeded generators**<br/>
  Abseil's bit generators require no constructor arguments to be seeded
  properly. Providing the initial state for a random value generator (ie.
  _"seeding"_) is a nontrivial task which often requires knowledge of the
  underlying bit-generation algorithm. When seeded, Abseil bit generators
  exhibit [Process Stability](#seed-stability).

* **Concise sampling syntax**<br/>
  Abseil's Random library provides a more concise syntax than `<random>` by
  representing distributions as functions rather than objects, while still
  decoupling bit generation from distribution sampling.

To get started, add the following `#include`, and analogous dependency within
your build file.

```c++
#include "absl/random/random.h"
```

## Bit Generators and Distribution Functions

The Abseil Random library provides a variety of **distribution function
templates**, which produce randomly sampled values from particular
distributions. They obtain their randomness from a user-supplied **uniform
random bit generator** (URBG, or **bit generator** for short), which should be
treated as an opaque object unless you're implementing a distribution function.
`absl::BitGen` is the preferred bit generator for most use cases.

```c++
absl::BitGen bitgen;
size_t index = absl::Uniform(bitgen, 0u, elems.size());
double fraction = absl::Uniform(bitgen, 0, 1.0);
bool coin_flip = absl::Bernoulli(bitgen, 0.5);
```

### Never Use A Random Bit Generator Directly

Bit generators produce values with the function-call operator, but this
interface should never be used directly in application code.

Properly sampling from a distribution can be surprisingly subtle; it requires
knowledge of the underlying URBG algorithm, and the range of values that it
produces. This range of values may or may not be the full space of values
representable by the output data type. Getting these details wrong can result in
biased sampling.

```c++ {.bad}
// AVOID: Invoking a bit generator's call operator directly. If bitgen() produces
// values in the range [0,7], then this code will produce 1 and 2 twice as often
// as other values.
uint32_t die_roll = 1 + (bitgen() % 6);
```

```c++ {.good}
// BETTER: Use a distribution function instead:
uint32_t die_roll = absl::Uniform(absl::IntervalClosed, bitgen, 1, 6);
```

Always use the Abseil Random library's distribution functions instead.

### Reuse Generators When Possible

Avoid continuously re-instantiating bit generators. URBG instances have state
which is designed to generate a sequence, and state initialization may involve
a lot of CPU cycles. It's better to reuse generator instances unless
those generators will be called very infrequently.

```c++  {.bad}
for (auto& elem : v_) {
  // AVOID: Creating a new absl::BitGen instance in a loop.
  absl::BitGen gen;
  elem = absl::Uniform(gen, 0, 1.0);
}
```

```c++  {.good}
// BETTER: Reuse absl::Bitgen instances.
absl::BitGen gen;
for (auto& elem : v_) {
  elem = absl::Uniform(gen, 0, 1.0);
}
```

### Controlling The Output Type Of `absl::Uniform()`

The most common use case for a random value library is also the most simple:
"Give me a number between _A_ and _B_".

```c++
int digit = absl::Uniform(gen, 0, 10);  // Samples an integer from [0, 10)
```

or perhaps:

```c++
double less_than_1 = absl::Uniform(gen, 0, 1.0);  // Samples from [0.0, 1.0)
```

or if we want to explicitly specify the desired numerical type, then perhaps:

```c++
// Casts arguments to the specified type, before sampling.
auto index = absl::Uniform<size_t>(gen, 0, v.size());
```

In the absence of an explicitly specified return type, the `absl::Uniform()`
function will use the more general of the two endpoints' data types. Note that
if neither of these types can represent the other without loss of precision,
then the function call will not compile.

```c++
size_t index = absl::Uniform(gen, 0u, v.size());      // Both are unsigned types
auto index = absl::Uniform<size_t>(gen, 0, v.size()); // Also fine
```

```c++
size_t index = absl::Uniform(gen, 0, v.size());       // Error: int vs size_t
```

### Controlling The Interval Bounds Of `absl::Uniform()`

You might sometimes find that sampling from the half-open distribution `[a, b)`
isn't a natural fit for your application. For such cases, we allow endpoint
semantics to be explicitly specified, by providing one of the following
identifiers as the first function call argument:

```c++
absl::IntervalClosed      // Sample from [a, b]
absl::IntervalOpen        // Sample from (a, b)
absl::IntervalOpenClosed  // Sample from (a, b]
absl::IntervalClosedOpen  // Sample from [a, b) … (Default)
```

Some examples might include:

```c++
int die_roll = absl::Uniform(absl::IntervalClosed, gen, 1, 6);
double jitter = absl::Uniform(absl::IntervalOpen, gen, -0.25, 0.25);
```

Choose whichever endpoints and semantics most naturally fit to your use case.

One final note - Omitting the endpoints when sampling an unsigned integer
provides a shorthand syntax for sampling from the entire type.

```c++
auto byte = absl::Uniform<uint8_t>(bitgen);  // From [0, 255]
```

## `BitGenRef`: A Type-Erased URBG Interface

An instance of the `absl::BitGenRef` class can be thought of as a type-agnostic
"reference" to an
[URBG](https://en.cppreference.com/w/cpp/named_req/UniformRandomBitGenerator)
instance. Functions which accept an `absl::BitGenRef` can be invoked using any
type of URBG, such as `absl::BitGen`, `absl::InsecureBitGen`, etc.

```c++
int TakesBitGenRef(absl::BitGenRef bitgen) {
  int v = absl::Uniform<int>(bitgen, 0, 1000);
}
```

`absl::BitGenRef` has implicit conversion constructors from any `URBG&`. A
`absl::BitGenRef` does *not* copy or own the underlying URBG, to which it
points, and so the underlying URBG *must* outlive the `BitGenRef` instance.

### Testing Random Behavior with `MockingBitGen`

Importantly, `absl::BitGenRef` allows mocking through the compatible
`absl::MockingBitGen` type. When testing we might want to mock to provide
deterministic results. The `MockingBitGen` provides such a mock for URBG
objects:

```c++
absl::MockingBitGen bitgen;

ON_CALL(absl::MockUniform<int>(), Call(bitgen, 1, 10000))
    .WillByDefault(Return(20));
EXPECT_EQ(absl::Uniform<int>(bitgen, 1, 10000), 20);

EXPECT_CALL(absl::MockUniform<double>(), Call(bitgen, 0.0, 100.0))
    .WillOnce(Return(5.0))
    .WillOnce(Return(6.5));
EXPECT_EQ(absl::Uniform(bitgen, 0.0, 100.0), 5.0);
EXPECT_EQ(absl::Uniform(bitgen, 0.0, 100.0), 6.5);
```

`MockingBitGen` has full support for Googletest matchers and actions.

## Frequently Asked Questions

### Which Bit Generator Type Is Right For My Application? {#which-bitgen}

Abseil provides `absl::BitGen` as a good default choice for random number
generation. An `absl::BitGen` is well seeded by default, so seeding operations
are not necessary, it has a large cycle-length, good diffusion of state, and is
reasonably fast.

It is reasonable to use `absl::InsecureBitGen` in tests or when using a URBG in
small isolated tasks such as in `std::shuffle`. Otherwise, default to using
`absl::BitGen` or `util_random::SharedBitGen` except when a low memory footprint
is critical, or benchmarks indicate a measurable improvement in application
performance.

### Why Do You Recommend `absl::BitGen` Over `absl::InsecureBitGen`?

The use of values produced by insecure bit generators in security-sensitive
contexts may introduce occasional (but dangerous) security issues. Although
`absl::BitGen` is not suitable for cryptographic applications such as key
generation, it provides guarantees strong enough to be resilient to misuse.

### How should Bit Generators be seeded?

A random bit generator is built on a recursive method where an internal hidden
state generates variates (outputs) as well as the next internal state.
Initialization of this hidden state is called **seeding**, which maps a sequence
of values, "the seed", onto the internal state of the bit generator. In C++ the
class [`std::seed_seq`](https://en.cppreference.com/w/cpp/numeric/random/seed_seq)
provides a common algorithm for doing this mapping. To generate truly random
seeds, the entropy typically comes from an OS entropy pool, which is available
via `std::random_device`.

In Abseil, both `absl::BitGen` and `absl::InsecureBitGen` are well seeded *by
default* so no additional seeding is requred, and use of `std::random_device` is
unnecessary. These generators acquire seed data from an an underlying entropy
pool managed by the [Randen](https://arxiv.org/abs/1810.02227) pseudorandom
generator, initially seeded from `/dev/urandom`.

```c++ {.good}
// GOOD: No need to provide additional seed to absl::BitGen.
absl::BitGen gen;
```

When seeding other random bit generators, prefer using multiple values in the
seed as well as allowing `std::seed_seq` to handle combining the values rather
than pre-merging them to a single value. Using a `std::seed_seq` with an
`absl::BitGen` is allowed and will incorporate those values plus additional
salting value to initialize the underlying state; please refer to the
[section on stability](#seed-stability) for more information.

```c++  {.bad}
// AVOID: Combining seed values outside of std::seed_seq.
uint32_t seed = MyHash(a) + MyHash(b) + MyHash(c);
std::mt19937 gen(seed);
```

```c++ {.good}
// BETTER: Allow std::seed_seq to combine seed values.
std::seed_seq my_seed_seq{a, b, c};
absl::BitGen gen(my_seed_seq);
```

When available, an Abseil URBG is generally an excellent replacement for short
lived instances like the following:

```c++ {.bad}
// AVOID: Initializes a large-state PRNG with a single word from std::random_device
std::random_device rd;
std::mt19937 gen(rd());

std::shuffle(data.begin(), data.end(), gen);
```

```c++ {.good}
// BETTER: Use a well-seeded PRNG by default.
absl::InsecureBitGen g;
std::shuffle(data.begin(), data.end(), g);
```

### Why Is My Generator Producing Different Values Between Re-runs, Even With An Explicit Seed?

The Abseil libraries are continuously updated, so values produced from one
seed sequence can change at any time. Abseil tries to prevent dependencies on
these mappings from accumulating by mixing the seed data with nondeterministic
data. The same `std::seed_seq` will always produce the same generator within the
same process, but the results will vary vary between executions!

```c++
std::seed_seq my_seed_seq{1, 2, 3};
absl::BitGen gen(my_seed_seq);
ABSL_LOG(INFO) << "Fraction: " << absl::Uniform(gen, 0, 1.0);
```

```shell
blaze test :my_unit_test
…
INFO  Fraction: 0.2578

blaze test :my_unit_test
…
INFO  Fraction: 0.012732
```

If you believe that your generator requires stability beyond the lifetime of its
process execution, please refer to the
[section on stability](#seed-stability).

### What About Instances Shared Across Multiple Threads?

Like the C++ standard library random engines, neither `absl::BitGen` nor
`absl::InsecureBitGen` are thread safe.

Efficiently leveraging a bit generator shared between multiple threads can be
tricky and subtle. Use of locally-instantiated generators are preferred to
global application-owned bit generators protected by a `Mutex` and shared across
multiple threads.

### Can I Use Abseil's Distribution Functions With Other Bit Generator Types?

Yes - the distribution functions are compatible with any type conforming to the
[`UniformRandomBitGenerator`](http://en.cppreference.com/w/cpp/named_req/UniformRandomBitGenerator)
named requirement, as defined by C++11. This includes `std::` types (e.g.
`std::minstd_rand` and `std::mt19937_64`).

### I Need My Variate Sequences To Be The Same Every Time!

We recognize that there are use cases which inherently require universally
stable (ie. seed-stable) variate generation, but this represents a narrow class
of applications within Google. Such use cases require stability of both
generator algorithms and distribution algorithms; in some cases, they require
this stability across multiple platforms, as well. Providing this would
completely freeze our ability to update and improve the Abseil Random library
for the (much larger) class of applications which neither require nor benefit
from these constraints. We hope to revisit the question of how to provide for
these use cases in the future, but for now, we (by design) offer no API that
indefinitely provides the same Seed→Sequence<sub>Variate</sub> mappings.

## Stability of Generated Sequences {#seed-stability}

Most applications and unit tests do not need to explicitly depend on the
sequence of variates generated by a given seed. If you believe that your binary
is an exceptional use case, Abseil Random may not be the right library for you.
That said, there is method to our "nondeterministic-seed" madness, and it's
worth outlining.

### Motivation

Our experience has taught us that random value generators are the ultimate
victims to [Hyrum's Law](http://hyrumslaw.com). The details of a generator's
implementation (i.e. the algorithm for generating values) is effectively
equivalent to its interface (i.e. the values generated). There have been
instances in which attempts to improve existing algorithms, such as the routine
for sampling pseudorandom floating-point values, have been foiled by thousands
of unit tests throughout Google which have become dependent on the sequences of
values generated. Thus, the API and implementation for previous iterations of
generators within Google is, in many respects, effectively frozen in place and
cannot be improved.

### Classes of Generator Stability

In order to prevent this from befalling the Abseil Random library, we have
implemented a scheme whereby the seed material used to derive the initial state
of a generator (`absl::BitGen`, `absl::InsecureBitGen`) is mixed with
non-deterministic data. We refer to the conditions under which a generator
promises to produce the same variates from a fixed seed sequence, as the
*stability* of the generator.

In the course of our discussions, we found it useful to define the following
categories of generator stability:

*   **Process Stability**: Given a fixed seed sequence *S*, and a collection of
    generator-instances *g<sub>1</sub>(S), …, g<sub>n</sub>(S)* constructed
    within the same process execution, all generators *g<sub>k</sub>* will
    produce the same sequences of variates.
*   **Seed Stability**: Given a fixed seed sequence *S*, and a collection of
    generator instances *g<sub>1</sub>(S), …, g<sub>n</sub>(S)*, all generators
    *g<sub>k</sub>* will produce the same sequence of variates, across all
    instances of any binaries.

### Guarantees provided by the Abseil Random library {#guarantees}

Our generator types provide **Process Stability**.

To seed an Abseil bit generator for
process stability, pass a `std::seed_seq` as the constructor parameter:

```c++
// Seeding an absl::BitGen for process stability.
std::seed_seq my_seed_seq{a, b, c};
absl::BitGen gen(my_seed_seq);
```

There is currently **no generator type in the Abseil Random library which
provides Seed Stability**. The motivation for this decision is as much
philosophical as it is practical: The legitimate use cases for an eternally
unchanging pseudorandom sequence are uncommon within Google.

The Abseil family of distribution classes and distribution functions (e.g.
`absl::Uniform()`) should be considered to have
**Process Stability**.
We hope to provide support for seed-stable distributions in the future, but at
the moment, no API from the Abseil Random library guarantees this contract.
