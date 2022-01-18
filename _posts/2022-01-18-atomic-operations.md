---
title: "The Danger of Atomic Operations"
layout: blog
sidenav: side-nav-blog.html
published: true
permalink: blog/01222022-atomic-operations
type: markdown
category: blog
excerpt_separator: <!--break-->
---

By [Ashley Hedberg](mailto:ahedberg@google.com), Software Engineer

The C++ Standard provides a library for performing fine-grained atomic
operations (e.g. `std::atomic`). Engineers sometimes reach for these
atomic operations in the hope to introduce some lock-free mechanism,
or to introduce clever tricks to improve performance. At Google, we’ve
found -- more often than not -- that such attempts lead to code that
is difficult to get right, hard to understand, and can often introduce
subtle and sometimes dangerous bugs.

We’ve now published a guide on the danger of these atomic operations,
and are publishing it to Abseil as a general programming guide. Atomic
operations should be used only in a handful of low-level data
structures which are written by a few experts and then reviewed and
tested thoroughly. Most programmers make mistakes when they attempt
direct use of atomic operations. Even when they don't, the resulting
code is hard for others to maintain.

For more information, check out
[The Danger of Atomic Operations](https://abseil.io/docs/cpp/atomic_danger).

