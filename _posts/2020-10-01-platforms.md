---
title: Abseil Platform Support Update
layout: blog
sidenav: side-nav-blog.html
published: true
permalink: blog/20201001-platforms
type: markdown
category: blog
excerpt_separator: <!--break-->
---

### Abseil Platform Support Update

By [Derek Mauro](mailto:dmauro@google.com), Abseil Engineer

[In September 2017, Abseil made the following support
promise](https://abseil.io/about/compatibility):

<i>We will support our code for at least 5 years. We will support language
versions, compilers, platforms, and workarounds as needed for 5 years after
their replacement is available, when possible. If it is technically infeasible
(such as support for MSVC before 2015, which has limited C++11 functionality),
those will be noted specifically. After 5 years we will stop support and may
remove workarounds. `ABSL_HAVE_THREAD_LOCAL` is a good example: the base
language feature works on everything except Xcode prior to Xcode 8 ; once
Xcode 8 is out for 5 years, we will drop that workaround support.
</i>

<!--break-->

The ability to evolve over time has long been a goal of the Abseil project, and
supporting older platforms comes with the cost of not being able to take
advantage of new features, and not being able to get the best performance
possible. With this is mind, the [September 2020 LTS release
branch](https://github.com/abseil/abseil-cpp/tree/lts_2020_09_23) will be the
last to support the following compilers:

* GCC 4.9
* Clang 3.6

We will soon remove our continuous integration tests for these compilers.

### Preparing for the Future

Of our supported platforms and compilers, the last to facilitate support for
C++14 was Microsoft Visual C++ 2017, which was released on March
7, 2017. Therefore, Abseil will only support C++11 (and Microsoft Visual C++
2015) until March 7, 2022. We will do one final Long Term Support release in
March of 2022, at which point we will announce that it is the final LTS release
to support C++11. We strongly recommend all users begin moving to C++14 or newer
as soon as possible and not wait for this LTS release, however.

In addition, the following support changes will occur in the near future:

* Clang 3.8, which replaced Clang 3.7, was released March 8, 2016. Therefore, we
intend to drop support for Clang 3.7 after March 8, 2021.
* GCC 6.1, which replaced the GCC 5 series, was released on April
27, 2016. Therefore, we intend to drop support for the GCC 5 series after April
27, 2021.
