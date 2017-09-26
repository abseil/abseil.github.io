---
title: Abseil's Compatibility Guidelines
layout: about
sidenav: side-nav-about.html
type: markdown
---

## Abseil Compatibility Guidelines

<p class="note">This is our <b>initial release of Abseil</b>, as of September
26, 2017. For a period until November 1, 2017 (about one month in duration),
we will not be guaranteeing the guidelines spelled out below, though
we will make a best effort to do so, as we resolve any issues we discover
from the initial release.</p>


This document details what we expect from well-behaved users, and what
we will offer in exchange. Any usage of Abseil libraries outside of
these technical boundaries may result in breakage when upgrading to
newer versions of Abseil.  

Put another way: don't do things that make Abseil API maintenance
tasks harder, and we promise not to break you if at all possible. If
you misuse Abseil APIs, you're on your own.

### What Users Must (And Must Not) Do

* **Do not depend on a compiled representation of Abseil.** We do not
  promise any ABI compatibility &mdash; we intend for Abseil to be
  built from source, hopefully from head. The internal layout of our
  types may change at any point, without notice. Building Abseil in
  the presence of different C++ standard library types may change
  Abseil types, especially for pre-adopted types (string_view,
  variant, etc) &mdash; these will become typedefs and their ABI will
  change accordingly.
* **Run Tooling / Follow Directions when Updating.** We will always
  strive to not break API compatibility. If we feel that we must, we
  will provide a compiler-based refactoring tool to assist in the
  upgrade, along with directions for how to execute the update. Most
  often these happen in the form: update to version N (where old and
  new APIs co-exist), run tool to convert between old and new APIs. In
  the rare instance where tooling cannot be produced, we'll provide as
  much information as we can about what to look for and how to resolve
  issues. (Remember: any time we are making a change publicly we're
  also doing the work to update the 250MLoC+ internal Google codebase
  &mdash; we very rarely do such refactoring that cannot be
  automated.)
* **Do not rely on dynamic unloading.** We consistently use patterns
  that may not be friendly to dynamic unloading of shared libraries.
  We make no claims that any of this code is usable in a system with
  regular unloading of such libraries.
* **Not all Abseil libraries are suitable for dynamic loading.** Some
  libraries have startup/initialization requirements and may not be
  suitable for dynamic loading.  We will try to be clear about which
  libraries are OK for dynamic loading. However we don't generally
  deploy code in this fashion, mistakes are possible, and the normal
  argument of "This code is production hardened" does not apply in
  such usage.
* **You may not open namespace `absl`.** You are not allowed to define
  additional names in namespace `absl`, nor are you allowed to
  specialize anything we provide. We expect there may eventually be
  templates that are valid extension points provided by Abseil &mdash;
  there are not currently. (This is similar to the restriction in the
  C++ standard &mdash; there are very few things you are allowed to do
  in namespace `std`.)
* **You may not depend on the signatures of Abseil APIs.** You cannot
  take the address of APIs in Abseil (that would prevent us from
  adding overloads without breaking you). You cannot use
  metaprogramming tricks to depend on those signatures either. (This
  is also similar to the restrictions in the C++ standard.)
* **You may not forward declare Abseil APIs.** This is actually a
  sub-point of "do not depend on the signatures of Abseil APIs" as
  well as "do not open namespace `absl`", but can be surprising. Any
  refactoring that changes template parameters, default parameters, or
  namespaces will be a breaking change in the face of
  forward-declarations.
* **Do not depend on Argument-Dependent Lookup (ADL) when calling
  Abseil APIs.** Even if it happens to build, calling
  `StrCat(foo, bar);` with two
  `absl::string_view` params is a bad idea &mdash; when building C++17
  mode, the associated namespace will no longer be `absl` and will
  instead be `std` and your code will break.  More generally: just
  don't do it, we may need to shift things around internally, please
  don't depend on namespace details.
* **Do not depend upon internal details.** This should go without
  saying: if something is in a namespace or filename/path that
  includes the word "internal", you are not allowed to depend upon it.
  It's an implementation  detail. You cannot friend it, you cannot
  include it, you cannot mention it or refer to it in any way.
* **Include What You Use.** We may make changes to the internal `#include`
  graph for Abseil headers - if you use an API, please include the relevant
  header file directly.
* **Do not make unqualified calls in the global namespace.** A call like `f(a);`
  for a function `f` in the global namespace can become ambiguous if/when we add
  `absl::f` (especially if `a` is an Abseil type). We generally do not recommend
  you use the global namespace for anything. If you must, please qualify any
  call that accepts a type provided by Abseil.

### What We Promise

* **We will support our code for at least 5 years**. We will support language
  versions, compilers, platforms, and workarounds as needed for 5 years after
  their replacement is available, when possible. If it is technically infeasible
  (such as support for MSVC before 2015, which has limited C++11 functionality),
  those will be noted specifically. After 5 years we will stop support and may
  remove workarounds. `ABSL_HAVE_THREAD_LOCAL` is a good example: the base 
  language feature works on everything except XCode prior to XCode 8 ; once
  XCode 8 is out for 5 years, we will drop that workaround support.
* **We will not break API compatibility.** If we must, we will ship a tool to
  automate the upgrade to a preferred API. We will never break that API in a
  single change - we believe in non-atomic refactoring. We will introduce the
  new API and the tool, wait some time, and then remove the old.
* **We promise to provide good forward-compatibility with the C++
  standard.**
* **We promise at least the basic-exception guarantee.** Although
  Google is part of the minority of the C++ community that doesn't use
  exceptions, we recognize that it **is** a minority and believe that
  code is often better when it's exception-safe. We've done our best
  to make things exception-safe. However, we won't contort things to
  support all possible exceptions &mdash; if you have a hash functor
  or `operator==` that throws, we may just mark it `noexcept` instead.
