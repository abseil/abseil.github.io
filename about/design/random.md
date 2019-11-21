The Abseil Random library is a collection of classes and function templates
which provide an API for generating random numbers. In these design notes we
will focus on the parts of the library which provide meaningful additions to the
standard library `<random>` header. For information on the design of `<random>`
consider watching these talks:

*   [What C++ Programmers Need To Know About `<random>`](https://youtu.be/6DPkyvkMkk8)
    from CppCon 2016 by _Walter E. Brown_.
*   [I Just Wanted A Random Integer](https://youtu.be/4_QO1nm7uJs) from CppCon
    2016 by _Cheinan Marks_.
*   [rand() Considered Harmful](https://youtu.be/8hREcJ4CFKI) from GoingNative
    2013 by _Stefan T. Lavavej_.

## Bit Generators

Most users are not experts in random number generation and do not know if they
want `std::minstd_rand` or `std::mt19937`. While it is important and necessary
to have these capabilities available for experts, in our experience, for most
users it suffices to provide a single default bit generator type `absl::BitGen`.

### Good Defaults

Seeding random bit generators is surprisingly difficult to get right, and often
requires intimate knowledge of the bit generation algorithm used in the
generators implementation. While we provide the standard facility for seeding
(via
[`std::seed_seq`](https://en.cppreference.com/w/cpp/numeric/random/seed_seq)),
we do not want the average user to concern themselves with the details of
seeding. For this reason, `absl::BitGen` and `absl::InsecureBitGen` have default
constructors which are well-seeded with random data. That is, simply default
constructing an `absl::BitGen` does the right thing.

### Non-determinism

Non-determinism is strongly baked into the design of the bit generators provided
by the Abseil Random library. A default-constructed `absl::BitGen` will be
seeded with OS-level entropy when it is available. Consequently two
`absl::BitGen`s in the same binary will yield different sequences of generated
bits. Rerunning the same binary will again produce different sequences.

Within the same binary, two bit generators constructed with the same seed
sequence will generate the same sequence of bits. However, this sequence is not
deterministic. Rerunning the same binary, the two generators will once again
agree with each other, but they will not generate the the same sequence of bits
as they did on the first binary execution.

The reasoning for this design choice is subtle, but important. While it often
seems like determinism is a useful property for random number generation, our
experience tells us that most users require determinism most often as a
mechanism for testing.

If bit generators are deterministic, whether or not such determinism is
promised as part of the API, users come to rely on it. With sufficiently
many users, it becomes impossible to make any change to the bit generation API
without breaking someone. (See[Hyrum's Law](http://hyrumslaw.com)). By
introducing guaranteed non-determinism, we hope to fight against Hyrum's Law,
allowing us to safely make improvements to our bit generators in the future.

## Distribution Function Templates

Abseil provides functions templates for getting results out of distributions.
There are two reasons for this design. First, in some instances we want to
provide a different API than the standard library to be explicit[^explicit]
about the meanings of certain inputs. For example,

```c++
absl::BitGen gen;
absl::string_view kHello = "Hello, Abseil Random!";

// Using the standard library API.  Remember that both endpoints are always
// included.
std::uniform_int_distribution die_dist<int>(1, 6);
int die_roll1 = die_dist(gen);

std::uniform_int_distribution index_dist<size_t>(size_t{0}, kHello.size() - 1);
char c1 = kHello[index_dist(gen)];

// Using Abseil Random.  Specify the interval bounds explicitly.
// Roll a fair die.
int die_roll2 = absl::Uniform<int>(__absl::IntervalClosedClosed__, gen, 1, 6);

// Pick a random character from the string.
size_t index = absl::Uniform<size_t>(absl::IntervalClosedOpen,
                                     gen, 0, kHello.size());
char c2 = kHello[index];
```

We provide similar functions (named `absl::Bernoulli`, `absl::Gaussian`, etc.)
for other distributions in
[absl/random/distributions.h](https://github.com/abseil/abseil-cpp/tree/master/absl/random/distributions.h).

The second benefit of these function templates is that they provide a useful
extension point to enable testing application code that uses Abseil Random.

## Testing

In addition to the bit generators discussed above, we also provide
`absl::MockingBitGen` which works with all the distribution function templates
mentioned above.  Instead of calling out to the underlying distribution, they
return values which can be mocked using GoogleTest infrastructure.

```c++
absl::MockingBitGen gen;

ON_CALL(absl::MockUniform<int>(), gen, testing::_, testing::Lt(100))
    .WillByDefault(testing::Return(17));

EXPECT_EQ(absl::Uniform(gen, absl::IntervalClosedClosed, 0, 25), 17);
EXPECT_EQ(absl::Uniform(gen, absl::IntervalClosedClosed, 0, 50), 17);
EXPECT_EQ(absl::Uniform(gen, absl::IntervalClosedClosed, 0, 75), 17);
```

This approach has a number of benefits. First, it gives test authors the ability
to set a particular value as the result of a distribution sample, not just out
of the bit generator. This allows users to easily test uncommon cases:

```cpp
using ::testing::_;
using ::testing::Lt;
using ::testing::Return;

int ComputeValue(absl::BitGenRef gen) {
  if (absl::Bernoulli(gen, 0.00001)) {
    return 10;
  } else {
    return 0;
  }
}

TEST(ComputeValueTest, UnlikelyCase) {
  absl::MockingBitGen gen;
  ON_CALL(absl::MockBernoulli(), Call(gen, Lt(0.01))
      .WillByDefault(Return(true));

  // The value `10` can be returned by ComputeValue, but it is highly unlikely.
  // With absl::MockingBitGen, we have a hook to get deterministic coverage of
  // this case.
  EXPECT_EQ(ComputeValue(gen), 10);
}
```

Another key benefit to this approach is that testing code will use neither a
production bit generator, nor an actual distribution object. At first glance
this may seem to be of marginal utility, but this has the benefit of freeing the
implementations of both bit generators and distribution implementations to
change over time, as tests will not come to rely on specific values produced by
these generators.

There is one notable drawback to this approach: It requires interfaces to
either type-erase the bit generator (so that either `absl::MockingBitGen` or
another bit generator can be passed in), or to itself take a bit generator type
as a template parameter. The type `absl::BitGenRef` is used to do type erasure
here and is (cheap but) not free, even when a real bit generator is being used.
We believe the facilities provided are well worth the cost.

[^explicit]: Part of the reasoning behind wanting this explicitness is that this
    library grew out of a previous code that always used half-open
    intervals. Because distributions in `<random>` always use closed
    intervals, to avoid confusion, we wanted to be explicit about the
    meanings of the interval bounds.
