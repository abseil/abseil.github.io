---
title: Abseil Fundamentals
layout: docs
sidenav: side-nav-cpp.html
type: markdown
---

This guide covers concepts common to all work in Abseil. The topics covered
within this guide are sort of a kitchen sink of the following:

* Important policy decisions and design patterns useful for Abseil code
* Useful fundamental code that all Abseil-derived code should know about
* Inner machinery required for fundamental Abseil code, but likely not important
  from a development standpoint

## Abseil Style Guidelines

Abseil code adheres to the official
[Google C++ Style Guide](https://google.github.io/styleguide/cppguide.html).
Additional constraints/concerns within Abseil code, where they diverge from the
above, appear below.

### Abseil Exception Policy

Google (rather famously) does not use exceptions within its production code. We
of course do not require that you adhere to such a policy. However, you should
be aware of some repercussions on your code base.

We do not believe there is good engineering reason for move constructors to
throw. At most, we will allow move constructors to throw because of allocation.
Within Abseil code, move constructors will not throw except because of
allocation if compiled without `-DABSL_ALLOCATOR_NOTHROW`. Holding move
constructors to this standard allows much better optimization, especially in
conjunction with standard library behavior (`std::vector` resizes much more
efficiently with non-throwing move constructors).

In general we will try to support exceptions in reasonable APIs and designs.
We are, however, opinionated about where exception-flexibility is trumped by
performance. We will try to be clear about where exceptions are a bad design
choice and mark things `noexcept` when possible. Do not confuse conceptual
support for exceptions with endorsement of exceptions in all places - if your
hash functor throws, you're on your own.

Be aware of the meaning of `noexcept`: this is not a promise that exceptions
do not happen, it is a promise that if an exception escapes that API, the
process will end with `std::terminate()`.

### Leak-Checking

Abseil code is designed to work with targets built with the LeakSanitizer
(LSan), a memory leak detector that is integrated within the AddressSanitizer
(ASan) as an additional component, or which can be used standalone. Leak
checking is enabled by default in all ASan builds.

For more information on the LeakSanitizer, see the
[Address Sanitizer docs](https://github.com/google/sanitizers/wiki/AddressSanitizerLeakSanitizer)

To enable LSan on your builds including Abseil code (using Bazel):

```
# Enable just LSan.
# Note that LSan requires Clang instead of gcc.
# You probably want to define a crosstool or bazel configuration to
# do this properly - provided for demonstration purposes only.
$ CC=clang BAZEL_COMPILER=llvm bazel build --copt=-DLEAK_SANITIZER \
    --linkopt=-fsanitize=leak *target*

# Enable ASan, which also includes LSan.
$ CC=clang BAZEL_COMPILER=llvm bazel build --copt=-DADDRESS_SANITIZER \
    --copt=-fsanitize=address --linkopt=-fsanitize=address= *target*
```

The `debugging/leak_check.h` header file contains several utility functions to
customize leak checking behavior within your code. Consult that header file for
more information.

## The Abseil Base Library

Fundamental Abseil code resides in the `absl/base` directory. Technically, these
files are not a cohesive "library" in the normal sense. What distinguishes them
as base files is that they have no outside dependencies; `absl/base` header
files only depend on other `absl/base` header files. The base library contains
fundamental code that all other Abseil code depends on. As a result, the
contents of base are kept to the minimum of what is absolutely necessary.

This base library consists of configuration files, some required Abseil
utilities for core code, and initialization primitives.

The Base library's configuration header files consist of the following:

* `policy_checks.h`<br />
  Enforces Abseil policies that can be enforced at build time,
  such as minimum compiler and library versions. For more information, consult
  the Abseil [Platforms Guide](/docs/cpp/platforms).
* `macros.h`<br />
  Provides macros used within Abseil code for language features.
* `optimization.h`
  <br /> provides several platform-dependent macros for implementing
  optimization techniques.
* `config.h`<br />
  Provides macros for determining platform and compiler support.
  For more information, consult the [Feature Check Macros](/docs/cpp/platforms/feature_checks)
  guide.

Additionally, the Base library includes one utility header file:

* `casts.h`<br />
  Provides a few useful extensions for performing safer type casts.

Consult that header file for more information.

The Base library's concurrency-related files, which are included in "base"
because they are fundamental to initialization and thread management, consist
of the following:

* `call_once.h`<br />
  Provides a primitive for ensuring a function is called exactly
  once, which is used during object initialization.
* `thread_annotations.h`<br />
  Provides a set of annotations to use within your code
  indentifying intended behavior in concurrent environments.

These APIs are documented separately within the
[Synchronization Guide](synchronization.md) rather than within this guide,
because they are strongly related to the other abstractions within that guide.