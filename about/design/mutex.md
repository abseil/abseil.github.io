---
title: absl::Mutex Design Notes
layout: about
sidenav: side-nav-design.html
type: markdown
---

# Design Note: `absl::Mutex`
Abseil uses and has published its own `absl::Mutex` abstraction in place of the
C++ library's `std::mutex` implementation. Such a decision is not advocated
lightly. This design note attempts to lay out all of the issues surrounding
`absl::Mutex` vs. `std::mutex` in light of usage at Google, while also noting
the API differences, performance issues, and extra features we've found useful.
We also discuss the refactoring costs and portability issues that influenced our
decision to stick with our implementation and open-source it.

Given that background we hope to reason about short and long term plans for a
mutex vocabulary type within Google and Abseil, and the implications of having
`absl::Mutex` and `std::mutex` live alongside each other going forward.

## API Issues

`absl::Mutex` provides its own `absl::Condition` abstraction. The interplay
between `absl::Mutex` and `absl::Condition`, especially in APIs like
`absl::Mutex::Await()` and `absl::Mutex::LockWhen()`, is different than the
standard mutex / condition model.

<table>
  <tr>
    <th>absl::Mutex Usage</th>
    <th>std::mutex Usage</th>
  </tr>
  <tr>
    <td>worker.cc</td>
    <td>worker.cc</td>
  </tr>
  <tr>
    <td>
<pre>
void Finish() {
  shared_lock_->Lock();
  shared_state_ += 1;
  shared_lock_->Unlock();
}
</pre>
    </td>
    <td>
<pre>
void Finish() {
  shared_lock_->lock();
  shared_state_ += 1;
  shared_lock_->unlock();
  shared_cv_->notify_one();
}
</pre>
    </td>
  </tr>
  <tr>
    <td>waiter.cc</td>
    <td>waiter.cc</td>
  </tr>
  <tr>
    <td>
<pre>
void Wait() {
  shared_lock_>Lock();
  shared_lock_->Await(Condition([this]() {
      return shared_state_ == 1;
  }));
  shared_lock_->Unlock();
}
</pre>
    </td>
    <td>
<pre>
void Wait() {
  shared_lock->lock();
  shared_cv_->wait(*shared_lock_, []() {
    return shared_state_ == 1;
  });
  shared_lock->unlock();
}
</pre>
    </td>
  </tr>
</table>

Note in particular that the condition is only needed in the waiter in the
Abseil version, and it is impossible to forget to notify about a state update.
In conjunction with added annotations (provided in
`absl/base/thread_annotations.h`) and enforcement of locking behavior by
[TSAN](https://clang.llvm.org/docs/ThreadSanitizer.html), this significantly
reduces programming errors: the API is harder to misuse. The general feeling in
discussions about `absl::Mutex` has been “We prefer this API.”

## Performance Issues

It has been proposed that having a combination Reader/Writer lock by default is
unnecessarily complex; if the lock isn’t held for long, no benefit acrues, but
the machinery and complexity for tracking readers and writers is in place
regardless.

That said, microbenchmark comparisons between base `absl::Mutex` and
`std::mutex` look equivalent &mdash; any performance penalty is equalled by the
`std::mutex` implementation.

## Extra Features

Aside from API compatibility, `absl::Mutex` contains a number of extra features
that are not supported in `std::mutex` and which would be painful to lose within
Google if we somehow shifted to `std::mutex`. These additional features include:

* Deadlock detection<br/>
  `absl::Mutex` tracks locking order and thread IDs to identify potential
  deadlocks. This functionality is duplicated by TSAN, but is enabled in far
  more of our builds.
* Contention tracking / reporting<br/>
  We track the amount of time that each `absl::Mutex` is actually contended
  (held by T1 while T2 is trying to acquire it), and make that information
  available for profiling.  We plan to improve access to this data in a future
  release.
* Reader/Writer locks<br/>
  The `std::mutex` class does not support shared (read-only) holds on a lock.
  This functionality is available only beginning in C++17 as a separate
  `std::shared_mutex` class.  `absl::Mutex` supports both patterns directly.

## Refactoring Costs

As a side effect of the API differences (like the unusual handling of
`absl::Condition`) and the fact that `absl::Mutex` has reader/writer
functionality built into itself, the idea of converting `absl::Mutex` to
`std::mutex` is seriously complex. We are providing our `absl::Mutex` because
we believe in it; its API provides less error-prone and more efficient usage
than the standard, in our opinion. However, we would be remiss to ignore the
concern that refactoring had on our decision, and we provide it here because it
may indeed affect your decision down the road.

An `absl::Mutex` is passed through Google interfaces many times, leading to the
(yet unsolved) problem of synchronizing batches of changes across interfaces. At
least for Mutexes that are used across translation units, it may require some
variation of whole-program analysis to identify which mutex features are used
for any given mutex. Rewriting such code is then a matter of expanding a single
`absl::Mutex` into a `std::mutex` and some number of other types (e.g.
`std::shared_mutex`, etc.) and then threading that package of variables through
whatever interfaces are necessary.

This is arguably one of the most complicated large-scale refactoring any
software organization envisions. More specifically: a lot of this refactoring
had no precedent, so this would have been largely have been a research task. Any
upsides would have to be very strong in order to justify such a change. We
decided the upsides were not that pressing.

## Portability

Even now, 5 years on from C++11, MSVC has at least one significant issue with
`std::mutex` compatibility: the lack of a `constexpr` constructor for
`std::mutex`. An upcoming API tweak to `absl::Mutex` will include just such a
`constexpr` interface, which is heavily used within Google. Lacking such a
construction is a problem for any large-scale code base that wants to statically
initialize a large number of mutexes.

## Going Forward

Code that requires portability on Windows and that isn’t built to specifically
avoid all need for a `constexpr` mutex cannot currently rely on the standard.
Moving Abseil code (and Google code) to the standard would have been
phenomenally expensive.

But all those things aside, the prime motivation for our support of
`absl::Mutex`, and the reason we are offering it to the open-source community,
is that we prefer our API and think it provides some crucial features. As well,
usage of our `absl::Mutex` is easily and less error-prone than the standard
offering.

If at some point in the future it becomes easier to perform a migration from
`absl::Mutex` to the standard, and the standard solves the problems we mention
here, we may revisit our assumptions, but in all likelihood we will support
`absl::Mutex` indefinitely.