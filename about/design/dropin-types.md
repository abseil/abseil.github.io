---
title: Abseil and Pre-adopted std:: types
layout: about
sidenav: side-nav-about.html
type: markdown
---

Abseil’s initial release includes several types that mimic the API of C++17 
vocabulary types: `absl::string_view`, `absl::any`, and `absl::optional`.

Like everything else currently in Abseil, these types only require C++11.
Where there are API designs that require C++14 or C++17, we’ve tried to ensure 
that those unsupported uses manifest as build breaks (not behavioral changes). 
This helps to ensure that upgrading from the pre-adopted version in absl to the 
standard version in std is always smooth. 

Once your codebase has upgraded to a version of the standard that supports 
these types, you’ll want to start using the standard version rather than the 
pre-adopted version.  This introduces a new technical challenge: types are 
conceptually expensive.

Consider the following scenarios:

* You have an implicit conversion to `absl::optional`. We cannot add an
  implicit conversion between `absl::optional` and `std::optional` - your build
  will break. (Also it would potentially be inefficient in surprising ways.)
* You have a specialization for `absl::optional` or `std::optional` but not
  both. Converting the rest of your code to work around that specialization 
  safely may be challenging.
* Similarly, you have an overload for `absl::optional` or `std::optional`.

In the end, the cost of having two nearly-identical types could turn out to be 
prohibitive. Instead, we dodge this issue by never having two types at the
same time: in builds where, for example, `std::optional` exists, the Abseil 
version will merely be an alias. In builds where there is no `std::optional`, 
`absl::optional` will be defined independently.  This means that in any build 
mode, `absl::optional` is a valid type but if `std::optional` exists, that is 
the underlying type.

With this design in mind, `absl::optional` becomes nothing more than an 
alternate spelling for `std::optional` in builds where the standard version 
exists. Since both spellings represent the same underlying type, we don’t need 
to worry about implicit conversions, specializations, or overloads: there is 
only one type in play.

Under Abseil’s general policy of “5 year support”, roughly 5 years after C++17 
is supported on all major platforms, we’ll stop providing C++14 support and 
thus stop providing `absl::optional`. At that point we will ship a tool (likely 
a clang-tidy plugin) to identify use of `absl::optional` and convert the 
spelling to `std::optional` - but since these are typedefs this will be a no-op 
change.

We expect to use this pre-adoption strategy repeatedly in the coming years, to 
provide pre-adoption versions of standard library facilities for users that 
can’t quite catch up to the current standard - or that require compatibility 
with others that are stuck behind.  Just remember: it’s a 5 year horizon.

