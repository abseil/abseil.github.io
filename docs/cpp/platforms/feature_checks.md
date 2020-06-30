---
title: "Feature Check Macros"
layout: docs
sidenav: side-nav-cpp.html
type: markdown
---

# Feature Check Macros

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

## Using Feature Check Macros

Feature check macros are used to conditionally compile code.

Example:

```cpp
#if ABSL_HAVE_FEATURE_FOO  // or #ifdef ABSL_HAVE_FEATURE_FOO
// Handle the case where feature foo is available.
#else
// Handle the case where feature foo is missing.
#endif
```

## Writing Your Own Feature Check Macros

Feature check macros are not allowed to be overridden (`-D`) on the compiler
command line. They should only be derived from pre-defined macros, other feature
check macros, or build configuration macros. For reusability, a feature check
macro should only be added to `absl/base/config.h` if it is used in at least
three distinct modules.

Note: `#if` and `#ifdef` have different results when a macro is defined to `0`.
We explicitly state that a feature check macro should be undefined for a
“false” state so both `#if` and `#ifdef` can be used interchangeably.

When writing preprocessor conditionals, you can either opt into use of a feature
by explicitly listing all platforms where a given feature is available, or opt
out by explicitly listing all platforms where a given feature is missing or
broken. Either option has pros and cons:

|      | opt-in                          | opt-out                             |
| ---- | ------------------------------- | ----------------------------------- |
| pros | Generally safe, and more likely | The compilation fails if a new      |
:      : to build on a new platform.     : platform doesn’t support the        :
:      :                                 : feature.                            :
| cons | The allow-list needs to be      | Compilation might succeed but       |
:      : extended for each new platform. : runtime behavior might be           :
:      :                                 : unexpected, if the interface exists :
:      :                                 : but the implementation is           :
:      :                                 : problematic.                        :

When choosing a opt-in or opt-out approach, think about what is likely to happen
when a new platform is added and which approach is easier to maintain the
invariant of your module.

Some examples:

If you are working around a compiler bug or a missing C++ feature in the
standard library implementation, you probably want to deny-list the combinations
where the feature is missing. When a new platform is added, you can assume it is
standards-compliant, and your unit test will fail if it is not.

If you are relying on a low-level OS feature for better functionality (more
logging, better debugging context), you probably want to allow-list the
operating systems that claim to support this feature. When a new OS is added,
you can assume the feature is missing, and your module will continue to work
with minimum functionality. If desired, a developer can decide to opt-in by
extending the allow-list.
