---
title: Abseil Fundamentals
layout: docs
sidenav: side-nav-cpp.html
type: markdown
---

This guide covers a variety of Abseil APIs and header files that are
collectively known as "base" files. These header files reside in the
`absl/base` directory. Technically, these files are not a cohesive
"library" in the normal sense. What distinguishes them as base files is
that they have no outside dependencies; `absl/base` header files only
depend on other `absl/base` header files. The base library contains
fundamental code that all other Abseil code depends on. As a result, the
content of base are kept to the minimum of what is absolutely necessary.

## Base Library Contents

This base library consists of configuration files, some required Abseil
utilities for core code, and initialization primitives.

The Base library's configuration header files consist of the following:

* `config.h` provides macros for determining platform and compiler support.
* `policy_checks.h` enforces Abseil policies that can be enforced at build time,
  such as minimum compiler and library versions.
* `port.h` provides miscellaneous APIs for creating portable code.

See [Platforms](#platforms) below for more information.

The Base library's Abseil utility header files consist of the following:

* `casts.h` provides a few useful extensions for performing safer type casts
* `macros.h` provides macros used within Abseil code for language features

See [Abseil Utilities](#utilities) below for more information.

The Base library's concurrency-related files, which are included in "base"
because they are fundamental to initialization and thread management, consist
of the following:

* `call_once.h`
* `thread_annotations.h`

These APIs are documented separately within the
[Concurrency Guide](concurrency.md) rather than within this guide, because they
are strongly related to the other abstractions within that guide.

## Platforms {#platforms}

Abseil contains a number of header files designed to determine platform and
compiler support and portability.

### Feature Check Macros

At compile time, we sometimes need to conditionally compile code based on
whether a language feature is provided by the underlying platform or compiler
for various purposes, such as portability or performance. In such cases, we
define *feature check macros* in `absl/config.h` to check whether the feature is
available or missing. Introducing a feature check macro is preferable to writing
a complex conditional directly because it explicitly states which feature it is
checking and makes the code more readable and maintainable.

Two types of feature check macros exist:

* Compiler checks
* Platform checks

In Abseil, feature check macros are named with an `ABSL_*` prefix and defined to
1 for a “true” state, and undefined for a “false” state. Defining them in this
manner allows you to use either `#if` or `#ifdef` constructs interchangeably.

Example:

```cpp
#ifdef ABSL_HAVE_FEATURE_FOO
#error "ABSL_HAVE_FEATURE_FOO cannot be overridden."
#elif <complex preprocessor conditional>
#define ABSL_HAVE_FEATURE_FOO 1
#endif
```

#### Using Feature Check Macros

Feature check macros are used to conditionally compile code.

Example:

```cpp
#if ABSL_HAVE_FEATURE_FOO  // or #ifdef ABSL_HAVE_FEATURE_FOO
// Handle the case where feature foo is available.
#else
// Handle the case where feature foo is missing.
#endif
```

#### Writing Your Own Feature Check Macros

Feature check macros are not allowed to be overridden (-D) on the compiler
command line. They should only be derived from pre-defined macros, other feature
check macros, or build configuration macros. For reusability, a feature check
macro should only be added to `absl/base/config.h` if it is used in at least
three distinct modules.

Note: #if and #ifdef have different results when a macro is defined to 0. We explicitly states that a feature check macro should be undefined for “false” state so both #if and #ifdef can be used interchangeably. However, #if is preferred over #ifdef because it is more flexible in the way that it handles both undefined and defined to 0.

Note: `#if` and `#ifdef` have different results when a macro is defined to `0`.
We explicitly state that a feature check macro should be undefined for a
“false” state so both `#if` and `#ifdef` can be used interchangeably.

When writing preprocessor conditionals, you can either whitelist all platforms
where a given feature is available, or blacklist all platforms where a given
feature is missing. Either option has pros and cons:

|----| whitelist |blacklist|
|----|------------|----------|
|pros|Generally safe, and more likely to build on a new platform.|The compilation fails if a new platform doesn’t support the feature.|
|cons|The whitelist needs to be extended for each new platform.|Compilation might succeed but runtime behavior might be unexpected, if the interface exists but the implementation is problematic.|

When choosing a whitelist or blacklist approach, think about what is likely to
happen when a new platform is added and which approach is easier to maintain the
invariant of your module.

Some examples:

If you are working around a compiler bug or a missing C++ feature in the
standard library implementation, you probably want to blacklist the combinations
where the feature is missing. When a new platform is added, you can assume it is
standards-compliant, and your unit test will fail if it is not.

If you are relying on a low-level OS feature for better functionality (more
logging, better debugging context), you probably want to white-list the
operating systems that claim to support this feature. When a new OS is added,
you can assume the feature is missing, and your module will continue to work
with minimum functionality. If desired, a developer can decide to opt-in by
extending the whitelist.

## Abseil Utilities {#utilities}

### Abseil Macros

### Casting Utilities