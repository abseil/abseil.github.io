---
title: "Civil Time in Abseil"
layout: blog
sidenav: side-nav-blog.html
published: true
permalink: blog/20181010-civil-time
type: markdown
category: blog
excerpt_separator: <!--break-->
---
By [Greg Miller](mailto:jgm@google.com), [Bradley White](mailto:bww@google.com),
and [Shaindel Schwartz](mailto:shaindel@google.com)

Almost every spring and fall there are news headlines about software that
misbehaved during a daylight-saving transition. In much of the world, DST
transitions occur multiple times per year, yet it is still a veritable
minefield of latent bugs due to the complexities inherent in reasoning
about civil-time discontinuities. To avoid these problems, a civil-time
library must present the programmer with a correct — yet simplified — model
that makes expressing the desired intent easy and writing bugs more obvious.

To that end, we are very pleased to introduce a new feature for the Abseil
time library — civil time support. This update adds a set of constructs and
functions that are used to represent and perform computations with civil
times.

<!--break-->

## Abseil Time Constructs

When discussing time, we refer to two representations: absolute time, which
represents a specific instant in time, and civil time, which represents the
year, month, day, hour, minute and second (YYYY-MM-DD hh:mm:ss) of local,
human-scale time. A “date,” for example, is a civil time - the legal, local
name for the time that we are describing. A time zone defines the
relationship between an absolute time and the civil time to which it
corresponds: 

<img src="/docs/cpp/guides/images/time-concepts.png" style="margin:5px;"
  alt="Absolute and Civil Time Relationships"/>
  
The Abseil time library provides six new classes for representing civil times:

* `absl::CivilSecond`
* `absl::CivilMinute`
* `absl::CivilHour`
* `absl::CivilDay`
* `absl::CivilMonth`
* `absl::CivilYear`

These are all ["value types"][regular-types] that enable easy and type-safe
computations with civil times of varying alignment. They give you a clear
vocabulary with which you can easily express your intent to the compiler
and fellow humans.

## Converting Between Absolute and Civil Times

The Abseil time library provides a set of functions to convert an absolute
`absl::Time` and an `absl::TimeZone` to a civil time:

* `absl::ToCivilSecond()`
* `absl::ToCivilMinute()`
* `absl::ToCivilHour()`
* `absl::ToCivilDay()`
* `absl::ToCivilMonth()`
* `absl::ToCivilYear()`

```cpp
absl::Time t = ...;
absl::TimeZone tz = ...;
absl::CivilDay cd = absl::ToCivilDay(t, tz);
```

The Abseil time library also provides the `FromCivil()` function to convert a
civil time of any alignment and an `absl::TimeZone` to an absolute `absl::Time`:

```cpp
absl::FromCivil()
absl::CivilSecond cs = ...;
absl::TimeZone tz = ...;
absl::Time t = absl::FromCivil(cs, tz);
```

## More Information

For more complete information, see the [Abseil time library documentation][time-docs].
Complete reference documentation is available within the
[Abseil time library header files][time-library].

[regular-types]: /blog/20180531-regular-types
[time-docs]: /docs/cpp/guides/time
[time-library]: https://github.com/abseil/abseil-cpp/tree/master/absl/time
