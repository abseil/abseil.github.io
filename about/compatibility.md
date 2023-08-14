---
title: "Abseil Compatibility Guidelines"
layout: about
sidenav: side-nav-about.html
type: markdown
---

# Abseil Compatibility Guidelines

Abseil follows Google's
[Foundational C++ Support Policy](https://opensource.google/documentation/policies/cplusplus-support)
and
[OSS Library Breaking Change Policy](https://opensource.google/documentation/policies/library-breaking-change).

In general, we avoid making backwards incompatible changes to our C++ APIs (see
below for the definition of "API"). Sometimes such changes yield benefits to our
customers, in the form of better performance, easier-to-understand APIs, and/or
more consistent APIs. When these benefits warrant it, we will announce these
changes prominently in our commit messages as well as in the release notes for
[LTS releases](https://github.com/abseil/abseil-cpp/releases). Nevertheless, we
have found that at scale,
[every change is potentially a breaking change](https://www.hyrumslaw.com/) for
some user. Though we take reasonable efforts to prevent this, it is possible
that backwards incompatible changes go undetected and, therefore, undocumented.
We apologize if this is the case and welcome feedback or
[bug reports](https://github.com/abseil/abseil-cpp/issues) to rectify the
problem.

Users following our recommended live-at-head approach should always be able to
temporarily pin their builds to a previous commit in our Git history.

Each LTS release should be considered to be a new major version of the library.
Previous LTS releases of the library will remain available on the
[GitHub Releases page](https://github.com/abseil/abseil-cpp/releases). In many
cases, you will be able to use an older version even if a newer version has
changes that you are unable (or do not have time) to adopt.

We request that our users adhere to the following guidelines to avoid
accidentally depending on parts of the library we do not consider to be part of
the public API and therefore may change (including removal) without notice:

## C++ Symbols and Files

-   **Do not depend upon internal details.** If something is in a namespace,
    file, directory, or simply contains the string `internal`, `impl`, `test`,
    `detail`, `benchmark`, `sample`, or `example`, unless it is explicitly
    called out, it is not part of the public API. It's an implementation detail.
    You cannot friend it, you cannot include it, you cannot mention it or refer
    to it in any way.
-   **Include What You Use.** For every symbol (type, function variable, or
    macro) that you use, directly `#include` the Abseil header file that exports
    the declaration of that symbol. This will prevent breakages due to changes
    in the `#include` graph for Abseil headers.
-   **Do not rely on dynamic unloading.** We consistently use patterns that may
    not be friendly to dynamic unloading of shared libraries. We make no claims
    that any of this code is usable in a system with regular unloading of such
    libraries.
-   **Not all Abseil libraries are suitable for dynamic loading.** Some
    libraries have startup or initialization requirements and may not be
    suitable for dynamic loading. We will try to be clear about which libraries
    are OK for dynamic loading. However we don’t generally deploy code in this
    fashion, mistakes are possible, and the normal argument of "This code is
    production hardened" does not apply in such usage.
-   **You may not open namespace `absl`.** You are not allowed to define
    additional names in namespace `absl`, nor are you allowed to specialize
    anything we provide. When we do provide extension points, (for example,
    `AbslHash()` or `AbslStringify()`), they will be explicitly documented as an
    [extension point](https://abseil.io/tips/218).
-   **Do not depend on the signatures of Abseil APIs.** You cannot take the
    address of APIs in Abseil (that would prevent us from adding overloads
    without breaking you). You cannot use metaprogramming tricks to depend on
    those signatures either. (This is also similar to the restrictions in the
    C++ standard.)
-   **Do not forward declare Abseil APIs.** This is actually a sub-point of "do
    not depend on the signatures of Abseil APIs" as well as "do not open
    namespace `absl`", but can be surprising. Any refactoring that changes
    template parameters, default parameters, or namespaces will be a breaking
    change in the face of forward-declarations.
-   **Avoid unnecessary dependency on Argument-Dependent Lookup (ADL) when
    calling Abseil APIs.** Some APIs are designed to work via ADL (e.g.
    `operator<<` for iostreams, unqualified swap in generic code, etc.) For most
    APIs, however, ADL is not part of the design. Calling functions from
    namespace `absl` via ADL, unless that is explicitly intended as part of the
    design, should be avoided. This is especially true for any function that
    accepts a pre-adopted type like `absl::string_view`: when the type changes
    to utilize the `std` version, its associated namespace will change and ADL
    will fail, resulting in build breaks. More generally: just don’t do it, we
    may need to shift things around internally, so please don’t depend on
    namespace details.
-   **Do not make unqualified calls in the global namespace.** A call like
    `f(a)`; for a function `f` in the global namespace can become ambiguous
    if/when we add `absl::f` (especially if a is an Abseil type). We generally
    do not recommend you use the global namespace for anything. If you must,
    please qualify any call that accepts a type provided by Abseil.

## What we mean by API

By "API" we mean the C++ API exposed by Abseil's public header files. We are
also talking only about **API** stability -- the **ABI** is subject to change
without notice. You should not assume that binary artifacts (e.g. static
libraries, shared objects, dynamically loaded libraries, object files) created
with one version of the library are usable with newer/older versions of the
library. The ABI may, and does, change on "minor revisions", and even patch
releases.

Applications developers interact with a C++ library through more than just the
C++ symbols and headers. They also need to reference the name of the library in
their build scripts. Depending on the build system they use this may be a CMake
target, a Bazel rule, a pkg-config module, or just the name of some object in
the file system.

As with the C++ API, we try to avoid breaking changes to these interface points.
Sometimes such changes yield benefits to our customers, in the form of bug
fixes, increased consistency across services, or easier to understand names.
When these benefits warrant it, we will announce these changes prominently in
our commit messages as well as in the release notes for
[LTS releases](https://github.com/abseil/abseil-cpp/releases). Nevertheless,
though we take reasonable efforts to prevent this, it is possible that backwards
incompatible changes go undetected and, therefore, undocumented. We apologize if
this is the case and welcome feedback or
[bug reports](https://github.com/abseil/abseil-cpp/issues) to rectify the
problem.

### Bazel rules

As with C++ symbols and files, Bazel rules that contain the the strings
`internal`, `impl`, `test`, `detail`, `benchmark`, `sample`, or `example`,
unless it is explicitly called out, are implementation details and should not be
depended on directly. In many cases we are able to use the
[`visibility`](https://bazel.build/concepts/visibility) attribute in our Bazel
rules to enforce this, however, the lack of a visibility restriction does not
override the implementation detail naming rules.

### CMake targets and packages

As with C++ symbols and files, CMake targets that contain the the strings
`internal`, `impl`, `test`, `detail`, `benchmark`, `sample`, or `example`,
unless it is explicitly called out, are implementation details and should not be
depended on directly.

### Documentation and Comments

The documentation (and its links) is intended for human consumption and not
third party websites, or automation (such as scripts scraping the contents). The
contents and links of our documentation may change without notice.

## Other Issues

We welcome the opportunity to improve our documentation. If the intended usage
of something isn't clear, you can always
[ask us a question](https://github.com/abseil/abseil-cpp/discussions) or create
a [GitHub issue](https://github.com/abseil/abseil-cpp/issues).
