---
title: Synchronization Library
layout: docs
sidenav: side-nav-cpp.html
type: markdown
---

The Synchronization library includes abstractions and primitives for managing
tasks across different threads. This library encompasses the following
header files:

* `mutex.h`<br />
  Provides primitives for managing locks on resources. A mutex is the most
  important primitive in this library and the building block for most all
  concurrency utilities.
* `notification.h`<br />
  Provides a simple mechanism for notifying threads of events.
* `barrier.h` and `blocking_counter.h`<br />
  Provides synchronization abstractions for cumulative events.

The Abseil `base` library also includes a number of concurrency-related header
files:

* `base/thread_annotations.h`<br />
  Provides macros for documenting the locking policy of multi-threaded code, and
  providing warnings and errors for misuse of such locks.
* `base/call_once.h`<br />
  Provides an Abseil version of `std::call_once()` for invoking a callable
  object exactly once across all threads.

This document will cover all of the above.

## Synchronization Overview

In sequential (i.e. single-threaded) systems, we usually think of events as
happening in a specific total order: for any operations A and B, either A
happens before B, or B happens before A. In concurrent systems, this is no
longer the case: for some pairs of operations it may not be possible to say
which one happens earlier (i.e. events are only partially ordered), in which
case we say that they happen *concurrently*. Notice that this definition has
nothing to do with whether they "actually" happen simultaneously, but only with
whether we can *guarantee* that they won't.

Concurrent operations may conflict if they are not used (or designed) properly
within a multi-threaded environment, resulting in the following problems:

* Operations may require write access to shared resources. We call these issues
  *memory access* issues.
* Operations may need to occur in a specific order. We sometimes call these
  issues *synchronization* issues (although memory access issues are also
  synchronization issues).

In either case, lack of control on the shared resources or lack of control on
the operation order can lead to *race conditions*. The purpose of the
concurrency abstractions within this library is to address these issues and
avoid such race conditions.

### Memory Access Issues

Memory access issues are often addressed through a variety of means, including:

  * Making the shared resource private or read-only (for data where this is
    appropriate)
  * Converting the data access into a "message passing" scheme, to provide
    copies of the shared information for temporary use rather than direct
    access to the memory.
  * Locking access to the shared resource, typically for write operations, to
    prevent more than one user from reading or writing concurrently.
  * Using atomic operations to access to the shared resource, such as those
    provided by `std::atomic`. Note that the rules for properly applying atomic
    operations are quite complicated, which is one of many reasons you should
    avoid atomics.

Locking access to shared resources is usually addressed through
mutually-exclusive locks known as *mutexes*. Abseil provides its own `Mutex`
class for this purpose; similarly, the C++ standard library provides a
`std::mutex` class for the same purpose. (Reasons why we implement our own
`Mutex` class are discussed in [Mutex Design Notes](/about/design/mutex).)

Types that behave correctly regardless of the order, scheduling,
or interleaving of their operations are known as *thread-safe*. In most cases,
such types use mutexes and atomic operations underneath the hood
to guard access to the object's internal state.

See [Mutexes](#mutexes) below for more information.

### Synchronization Operations

Synchronization issues other than simple memory access issues are often more
complex and require abstractions specifically built to address the underlying
problem, (again, often through mutexes and atomic operations, which are quite
tricky to implement properly). Synchronization operations are designed to
control the order of events in different threads.

Keep in mind that operations on "thread-safe" types aren't necessarily
synchronization operations. When you read a value that another thread wrote, you
can't assume that the write happens before the read; they may happen
concurrently.

For example:

```cpp
foo::counter first, second;

void thread1() {
  first.Add(1);    // (a)
  second.Add(1);   // (b)
}

void thread2() {
  while (second.value() == 0) {
    sleep(10);
  }
  CHECK(first.value() == 1);   // ERROR
}
```

Even if foo::counter were thread-safe (and you wouldn't need to worry about data
races), you might think that the `CHECK()` will succeed, because line (a)
happens before line (b), and the `CHECK()` can't be reached until line (b) has
executed. However, unless `Add()` and `value()` are also synchronization
operations, none of the operations in thread1 need necessarily happen before any
of the operations in thread2, and that `CHECK()` may fail.

Abseil provides several synchronization abstractions. See
[Synchronization Operations](#other-synchronization-operations) for more 
information.

## Mutexes

The major primitive for use within concurrency tasks is a mutex, which is a
*mut*ually *ex*clusive lock that can be used to prevent multiple threads from
accessing and/or writing to a shared resource.

### `absl::Mutex` and `std::mutex`

Abseil provides its own `Mutex` class, and within Google, we use this class
instead of the similar `std::mutex`. `Mutex` provides most of the functionality
of `std::mutex` but adds the following additional features:

* `absl::Mutex` adds *conditional critical sections*, an alternative to
  condition variables. `Mutex::Await()` and `Mutex::LockWhen()` allow the client
  to wait for a condition without needing a condition variable; the client need
  not write the while-loop, nor need they use `Signal()`. (See
  [Condition](#conditional-critical-sections) below.)
* `Mutex`  intrinsically supports deadlock detection (when locks are not
  acquired in a consistent order). The deadlock detector is enabled by default
  in most non-opt build modes, and it can detect deadlock risks that even Clang's
  [Thread Sanitizer](https://clang.llvm.org/docs/ThreadSanitizer.html) misses.
  (See [Deadlock Detection](#deadlock-detection) below.)

Additionally, `absl::Mutex` can act as a reader-writer lock (like
`std::shared_mutex`) with special `ReaderLock()` and `ReaderUnlock()` functions.
(See [Reader-Writer Locks](#reader-writer-locks) below.)

We've found these features to be critically important for maintaining a large
and complex code base. We are not necessarily intending to compete with
`std::mutex` itself; if you find the features usable within your code base,
consider `absl::Mutex` and its utilities.

Like `std::mutex`, Abseil's Mutex is not re-entrant (also known as
non-recursive). As well, it does not provide strict FIFO behaviour or fairness
in the short term; to do so would require significant overhead. However, it
tends to be approximately fair in the long term.

### Mutex Basics

The `absl::Mutex` class implements a mutually exclusive lock on some
resource, allowing threads which also use the mutex to avoid concurrent access
to that resource, which is typically some variable or data structure with
associated invariants. For example, a financial transaction system may wish only
one writer to access certain data elements at one time. Mutexes are so common
that many words have been coined to describe their operation.

Each `Mutex` has two basic operations: `Mutex::Lock()` and `Mutex::Unlock()`.
Conceptually, it has just a single bit of abstract state: a boolean indicating
it is `true` (locked) or `false` (unlocked). When a `Mutex` is created, this
lock is initially `false` and the mutex is said to be *free* or *unlocked*.
`Lock()` blocks the caller until some moment when the mutex is free, and then
atomically changes this mutex state from `false` to `true`; the mutex is then
said to be *held* or *locked* by the caller. `Unlock()` sets this mutex state to
`false` once more.

Calling `Lock()` is often referred to as *locking* or *acquiring* a mutex, while
calling `Unlock()` is referred to as *unlocking* or *releasing* a mutex. An
action performed by a thread while holding a mutex is said to be performed
*under* the mutex. Data structures manipulated under the mutex, and their
invariants, are said to be *protected by* the mutex.

Clients of `Mutex` must obey these rules:

1.  Each time a thread acquires a `Mutex` it must later release it.
2.  A thread may not attempt to release a `Mutex` unless it holds it.
3.  A thread may not attempt to acquire an exclusive lock on a `Mutex` it
    already holds.

Because `Lock()` acts atomically to change the state of the state of the mutex,
we are guaranteed that, if these rules are followed, only one thread may hold a
mutex at any given time.

These rules must be followed both to prevent concurrent access to the protected
resource and avoid *deadlock*, in which a thread blocks waiting for a lock to be
released. The last rule prevents *self-deadlock*, when a holder of a mutex
attempts to acquire a mutex it already holds. Such mutexes are known as
non-recursive (or non-reentrant) mutexes.

These rules are best followed by bracketing regions of code with
matching calls to `Lock()` and `Unlock()` a mutex in the same procedure.
Such sections of code are called *critical regions*. Much Google C++ code uses
the helper class `MutexLock`, which through RAII automatically acquires a mutex
on construction and releases it when the lock goes out of scope.

### Mutexes and Invariants

Most mutexes are used to ensure some invariant state can only be changed
atomically while the mutex is held. The programmer is required to re-establish
the invariant before releasing the mutex; code can then assume the invariant
holds whenever acquiring the mutex, even in the face of updates that
*temporarily* invalidate the invariant during the critical section. However, one
cannot guarantee the invariant is true in a thread that does not hold the mutex,
because the mutex holder may be changing the monitored state at that moment.

For example, suppose `Mutex mu` protects the invariant that `a + b == 0`. This
code is then legal:

```cpp
mu.Lock();
assert(a + b == 0); // invariant assumed to hold
a++;                // invariant temporarily invalidated
b--;                // invariant restored before mu is released
mu.Unlock();
```

while this code is erroneous:

```cpp
mu.Lock();
assert(a + b == 0); // invariant assumed to hold
a++;                // invariant invalidated
mu.Unlock();        // BUG: mutex released while invariant invalid
mu.Lock();
b--;                // attempt to restore the invariant,
                    // but the damage is already done
mu.Unlock();
```

The following does not invalidate the invariant, but incorrectly assumes
it is true when the lock is not held:

```cpp
mu.Lock();
assert(a + b == 0); // correct: invariant assumed to hold
mu.Unlock();
assert(a + b == 0); // BUG: can't assume invariant without lock
```

The invariant holds only when evaluated on state observed within a single
critical section:

```cpp
mu.Lock();
assert(a + b == 0);    // correct: invariant assumed to hold
temp = a;              // takes a temporary copy of "a"
mu.Unlock();
mu.Lock();
assert(temp + b == 0); // BUG: can't assume invariant on state
                       // from two distinct critical sections
mu.Unlock();
```

### The `MutexLock` Wrapper

Forgetting to acquire and release locks on a `Mutex` often leads to errors in
your code. The Abseil concurrency library includes a `MutexLock` wrapper class
to make acquiring and releasing a `Mutex` easier. The class uses RAII to
acquire the mutex and automatically releases it when the class goes out of
scope.

Example:

```cpp
Class Foo {

  Foo::Bar* Baz() {
    MutexLock l(&lock_);
    ...
    return bar;
  }

  private:
    Mutex lock_;
  };
}
```

### Conditional Mutex Behavior

An Abseil `Mutex` can be configured to block threads until a certain condition
occurs. Such conditional behavior is accomplished in two ways: a traditional
*conditional variable* `CondVar` (similar to the `std::condition_variable`
available to `std::mutex`) or through a mechanism unique to Abseil's mutex:
*conditional critical sections*, using a `Mutex::Condition`.

Conditional Critical Sections (using the `Condition` construction) are generally
preferred as use of separate condition variables has proven to be error prone.
The `Mutex` contains a number of member functions (e.g. `Mutex::Await()`) that
are hard to get wrong. Generally, prefer use of `Condition`; in rare cases, when
there are multiple threads waiting on distinctly different conditions, however,
a battery of `CondVar`s may be more efficient.

#### Conditional Critical Sections

Abseil's `Mutex` has been extended through the addition of *conditional critical
sections*, an alternative to condition variables. Member functions such as
`Mutex::Await()` and `Mutex::LockWhen()` use intrinsic `Condition` predicates
to allow a client to wait for a condition without needing a condition variable;
the client need not write the while-loop, nor need they use `Signal()`.

Clients can imagine that a mutex contains an imaginary condition variable
`mu.cv`; with that assumption, these corresponding code fragments on the left
and right are equivalent:

<table width="100%">
  <tbody>
    <tr>
      <th>Conditional critical sections</th>
      <th>Condition variables</th>
    </tr>
    <tr>
      <td width="50%">
<pre>
mu.Lock();
... // arbitrary code A
mu.Await(Condition(f, arg));


... // arbitrary code B
mu.Unlock();

mu.LockWhen(Condition(f, arg));



... // arbitrary code C
mu.Unlock();</pre>
 </td>
      <td width="50%">
<pre>
mu.Lock();
... // arbitrary code A
while (!f(arg)) {
  mu.cv.Wait(&amp;mu);
}
... // arbitrary code B
mu.Unlock();

mu.Lock();
while (!f(arg)) {
  mu.cv.Wait(&mu);
}
... // arbitrary code C
 mu.Unlock();</pre>
 </td>
    </tr>
  </tbody>
</table>

When `LockWhen()` and `Await()` are used, the condition must be encapsulated in
a function (`f` in the examples) with a `void *` argument (or by a lambda). As
with condition variables, the condition must be a function of state protected by
the mutex. The minor inconvenience of requiring a function is rewarded by
eliminating the need for the condition variable and the while-loop, which are
now hidden inside the `Mutex` implementation.

Even better, `Mutex::Unlock()` will take care of calling `Signal` or
`SignalAll()` to wake waiters whose conditions are now true; its performance is
usually as good as or better than that achieved with a condition variable. Thus,
the example of the previous subsection could be written as:

```cpp
bool f(bool *arg) { return *arg; }

// Waiter
mu.LockWhen(Condition(f, &cond_expr));
// cond_expr now holds
...
mu.Unlock();

// Waker
mu.Lock();
Make_cond_expr_True();
// cond_expr now holds
mu.Unlock();
```

In rare cases, when many threads may be waiting with many different and
usually-false conditions, it may be better to use multiple condition variables.
In general, we recommend conditional critical sections for simplicity.

The call `mu.LockWhen(Condition(f, arg))` is equivalent to
`mu.Lock(); mu.Await(Condition(f, arg))`.  Similarly, the call
`mu.Await(Condition(f, arg))` is equivalent to
`mu.Unlock(); mu.LockWhen(Condition(f, arg))`.

The variants `LockWhenWithTimeout()` and `AwaitWithTimeout()` allow a thread to
wait either for a condition to become true or for some time to elapse. They each
return `true` if the condition is true:

```cpp
if (mu.LockWhenWithTimeout(Condition(f, &cond_expr), 1000 /*ms*/)) {
  // mu held; cond_expr true
} else {
  // mu held; cond_expr false; 1000ms timeout expired
}
mu.Unlock();
```

These calls are analogous to `cv.WaitWithTimeout()`.

#### `CondVar` Condition Variables

Condition variables serve the same purpose as conditional critical sections;
they are a means for blocking a thread until some condition has been satisfied.
Usually, conditional critical sections are easier to use, but condition
variables may be more familiar to programmers because they are included in the
POSIX standard and Java language.

Viewed in isolation, a condition variable allows threads to block and to be
woken by other threads. However, condition variables are designed to be used in
a specific way; a condition variable interacts with a mutex to make it easy to
wait for an arbitrary condition on state protected by the mutex.

Suppose that a thread is to wait for some boolean expression `cond_expr` to
become `true`, where the state associated with `cond_expr` is protected by a
mutex `mu`. The programmer would write:

```cpp
// Waiter
mu.Lock();
while (!cond_expr) {
  cv.Wait(&mu);
}
// cond_expr now holds
...
mu.Unlock();
```

The `Wait()` call atomically unlocks `mu` (which the thread must hold), and
blocks on the condition variable `cv`. When another thread signals the condition
variable, the thread will reacquire the `mu`, and go around the mandatory
while-loop to recheck `cond_expr`.

Another thread that makes cond_expr true might execute:

```cpp
// Waker
mu.Lock();
Make_cond_expr_True();
// cond_expr now holds
cv.Signal();
mu.Unlock();
```

The call to `Signal()` wakes at least one of the threads waiting on `cv`. Many
threads may be blocked on a condition variable at any given time; if it makes
sense to wake more than one such thread `SignalAll()` can be used. (The
`SignalAll()` functionality is often referred to as broadcast in other
implementations.)

A single condition variable can be used by threads waiting for different
conditions. However, in this case, `SignalAll()` must be used when any of the
conditions becomes `true`, because the `CondVar` implementation cannot otherwise
guarantee to wake the correct thread. It can be more efficient to use one
condition variable for each different condition; any number of condition
variables can be used with a single mutex.

Both `Signal()` and `SignalAll()` are efficient if there are no threads to wake.
Clients should call `Signal()` or `SignalAll()` inside the critical section that
makes the condition true.

The call `WaitWithTimeout()` allows a thread to wait until either a condition is
`true`, or until some time has elapsed. Like `Wait()`, `WaitWithTimeout()`
always reacquires the mutex before returning.

Example:

```cpp
static const int64 kMSToWait = 1000;  // we'll wait at most 1000ms
int64 ms_left_to_wait = kMSToWait;    // ms to wait at any given time
int64 deadline_ms = GetCurrentTimeMillis() + ms_left_to_wait;
mu.Lock();
while (!cond_expr && ms_left_to_wait > 0) {
  cv.WaitWithTimeout(&mu, ms_left_to_wait);
  ms_left_to_wait = deadline_ms - GetCurrentTimeMillis();
}
if (cond_expr) {
  // cond_expr true
} else {
  // cond_expr false; 1000ms timeout expired
}
mu.Unlock();
```

### Reader-Writer Locks

A reader-writer (shared-exclusive) lock has two locking modes. If the lock is
not free, it may be held either in write (a.k.a. exclusive) mode by a single
thread, or in read (a.k.a. shared) mode by one or more threads.

It is natural to use a reader-writer lock to protect a resource or data
structure that is read often, but modified infrequently. Critical sections that
modify the protected state must acquire the lock in write mode, while those that
merely read the state may acquire the lock in read mode.

Note: reader-writer locks can reduce lock contention in some situations, but
most locks are not contended enough for this to make a difference. When you use
shared locks, the onus is on you to ensure that the code in reader critical
sections really doesn't mutate the data (logically or physically), and any
mistakes here can lead to subtle race conditions.

Any `Mutex` can be used as a reader-writer lock.  The `Lock()` call acquires the
lock in write mode and must be paired with a call to `Unlock()`. The
`ReaderLock()` call acquires the lock in read mode and must be paired with a
call to `ReaderUnlock()`. `absl::Mutex` does not provide operations to convert
from a read lock to a write lock or vice versa without first releasing the lock.

Both condition variables and `mu.Await()` may be used with `Mutex` read-mode
critical sections as well as with write-mode critical sections.

`Mutex` does not allow readers to starve writers or vice versa. This leads to
the slightly surprising effect that a request for a read lock may block even if
the lock is already held by a reader. If this could not happen, a waiting writer
could be prevented ever from making progress by two or more readers that kept
the lock permanently in read mode, without any one holding the lock
indefinitely.

Beware that future maintainers may add mutations to "reader" critical sections
accidentally, thus introducing errors.  For example, self-optimizing data
structures such as splay trees or LRU caches may modify the data structure on
every read.  Even simple data structures may keep track of usage statistics.
Therefore, reader locks should be used with care, and their use should be easy
for developers to recognize. It can help to forbid modifications using a pointer
to a `const` data structure, though care must be still be exercised because of
C++'s `mutable` keyword.

We recommend using `Mutex` as a simple mutex initially; introduce reader locks
only when you know you have lock contention and you know that writes are
infrequent.

### Thread Annotations

The major drawbacks of `absl::Mutex` are drawbacks of any mutex type: you have
to remember to lock it before entering a critical section, you have to remember
to unlock it when you leave, and you have to avoid deadlock.

To help solve these problems, Abseil provides thread-safety annotations (in
`base/thread_annotations.h`) to specify which variables are guarded by which
mutexes, which mutexes should be held when calling which functions, what order
mutexes should be acquired in, and so forth. These constraints are then checked
at compile time, and although this mechanism is not foolproof, it does catch
many common `Mutex` usage errors. Besides being part of the code documentation,
annotations can also be used by the compiler or analysis tools to identify and
warn about potential thread safety issues.

#### Annotation Guidelines

Every data object (whether a global variable in namespace scope or a data member
in class scope) which requires protection from a mutex should have an annotation
`GUARDED_BY` indicating which mutex protects it:

```cpp
int accesses_ GUARDED_BY(mu_); // count of accesses
```

Every mutex should have a complementary comment indicating which variables and
also any non-obvious invariants it protects:

```cpp
Mutex mu_;       // protects accesses_, list_, count_
                 // invariant: count_ == number of elements in linked-list list_
```

Whenever a thread can hold two mutexes concurrently, either one (or both) of the
mutexes should be annotated with `ACQUIRED_BEFORE` or `ACQUIRED_AFTER` to
indicate which mutex must be acquired first:

```cpp
Mutex mu0_ ACQUIRED_BEFORE(mu1_); // protects foo_
```

If the mutex acquisition order is not consistent, deadlock may result. See
[Deadlock Detection](#deadlock-detection) for utilities within the Concurrency
library to detect deadlock.

Each routine should be annotated or have a comment indicating which mutexes must
and must not be held on entry. These annotations allow implementors to edit
routines without examining their call sites, and allows clients to use routines
without reading their bodies.

The annotations `EXCLUSIVE_LOCKS_REQUIRED`, `SHARED_LOCKS_REQUIRED`,
and `LOCKS_EXCLUDED` are used to document such information. Since we currently
use GCC's "attributes" to implement annotations, they can only be applied to the
function declarations, not the definitions (unless they are inside a class
definition).

If a routine acquires `mu`, we must annotate its declaration with
`LOCKS_EXCLUDED(mu)`:

```cpp
// Function declaration with an annotation
void CountAccesses() LOCKS_EXCLUDED(mu_);

// Function definition
void CountAccesses() {
  this->mu_.Lock();
  this->accesses_++;
  this->mu_.Unlock();
}
```

If a routine expects to be called with `mu` held, we must annotate it with
`EXCLUSIVE_LOCKS_REQUIRED(mu)` or `SHARED_LOCKS_REQUIRED(mu)` depending on
whether the routine needs a writer or reader lock:

```cpp
// Function declaration with an annotation
void CountAccessesUnlocked() EXCLUSIVE_LOCKS_REQUIRED(mu_);

// Function definition
void CountAccessesUnlocked() {
  this->accesses_++;
}
```

Without such annotations/comments, working with mutexes is significantly
harder.  We **strongly recommend** their use.

### Deadlock

A deadlock (sometimes called a *deadly embrace*) occurs when an *activity*
attempts to acquire a limited *resource* that has been exhausted and cannot be
replenished unless that activity makes progress.

When considering deadlocks involving only mutexes, each activity is
typically represented by a thread, and the resources are mutexes that
are exhausted when held, and replenished when released.

The simplest mutex-related deadlock is the *self-deadlock*:

```cpp
mu.Lock();
mu.Lock();      // BUG: deadlock: thread already holds mu
```

Deadlocks involving two resources, such as a mutex and a bounded-sized
thread pool, are easily generated too, but deadlocks involving three or
more resources are less common.  A two-mutex deadlock results when thread
T0 attempts to acquire M1 while holding M0 at the same time that thread
T1 attempts to acquire M0 while holding M1; each thread will wait
indefinitely for the other.

#### Deadlock Detection

Fortunately, deadlocks are among the easiest bugs to debug and avoid.
Debugging is typically easy because the address space stops exactly
where the bug occurs.  A stack trace of the threads is usually all that
is required to see what the threads are waiting for and what resources they
hold.

Additionally, the `absl::Mutex` API provides additional deadlock detection. Such
detection is enabled only when the application is compiled in debug mode and the
flag `-synch_deadlock_detection` is non-zero. When enabled, the API detects two
additional types of deadlock cases:

* Mutexes acquired in an inconsistent order. The deadlock detector maintains an
  *acquired-before* graph for mutexes in a process. An error is generated if
  potential deadlock (a cycle) is detected in that graph.
* Mutexes which are released by threads which do no hold them.

If `-synch_deadlock_detection=1`, a message is printed for each lock-order
error. If `-synch_deadlock_detection=2`, the first lock-order error causes the
process to abort.

The following calls are not recommended for production code, but are useful when
deadlock detection is enabled:

* `Mutex::AssertHeld()`: abort with high probability if `mu` is not held
  exclusively by the calling thread.
* `Mutex::AssertReaderHeld()`: abort with high probability if `mu` is not
  held in some mode by the calling thread.
* `Mutex::ForgetDeadlockInfo()`: forget ordering information gathered for
  this mutex. This routine should be used if the ordering of mutexes changes
  during execution (this is rare).

Note that deadlock detection introduces significant overhead; it should not be
enabled in production binaries.

## Other Synchronization Operations

Most concurrency issues that are not restricted to memory access issues fall
under the broad category of "synchronization" operations. Within a concurrent
system, a synchronization operation generally encompasses operations for
which a strict ordering must be ensured.

Abseil contains a number of synchronization abstractions:

* `call_once()`, which allows a function to be executed exactly once across all
  threads.
* A `Notification`, which allows threads to receive notification of a single
  occurrence of a single event.
* A `Barrier`, which blocks threads until a prespecified threshold of threads
  utilizes the barrier, at which point the barrier is unblocked.
* A `BlockingCounter`, which allows a thread to block for a pre-specified number
  of actions.


### `call_once()`

`absl::call_once()` is a fast implementation of the C++ standard library
`std::call_once()`, for invoking a given function at most once, across all
threads. You pass three arguments to `call_once()`: a `once_flag` to coordinate
and identify unique callers, a function to invoke, and the arguments to invoke
with the function.

The first call to `call_once()` with a particular `once_flag` argument (that
does not throw an exception) will run the passed function with the provided
arguments; other calls with the same `once_flag` argument will not run the
function, but will wait for the provided function to finish running (if it is
still running).

This mechanism provides a safe, simple, and fast mechanism for one-time
initialization in a multi-threaded process:

```cpp
class MyInitClass {
  public:
  ...
  absl::once_flag once_;

  MyInitClass* Init() {
    absl::call_once(once_, &MyInitClass::Init, this);
    return ptr_;
  }
}
```

### `Notification`

A `Notification` allows threads to receive notification of a single occurrence
of a single event. Threads sign up for notification using one of the
notification's `WaitForNotification*()` member functions.
`Notification::Notify()` is used to notify those waiting threads that the event
has occurred, and may be only called once for any given notification.

Example:

```cpp
// Create the notification
Notification notification_;

// Client waits for notification
void Foo() {
  notification_.WaitForNotification();
  // Do something based on that notification
}

//
void Bar() {
  // Do a bunch of stuff that needs to be done before notification
  notification_.Notify();
}

```

### Barrier

An `absl::Barrier` blocks threads until a prespecified threshold of threads
utilizes the barrier. A thread utilizes the `Barrier` by calling `Block()` on
the barrier, which will block that thread; no call to `Block()` will return
until the specified number of threads have called it.

Example:

```cpp
Barrier *barrier_ = new Barrier(num_active_threads);

void Foo() {
  if (barrier_->Block()) {
    delete barrier_;  // This thread is responsible for destroying barrier_;
  }
  // Do something now that the Barrier has been reached.
}
```


### BlockingCounter

An `absl::BlockingCounter` blocks all threads for a pre-specified number of
actions. Threads call `Wait()` on a blocking counter to block until the
specified number of events occur; worker threads then call `DecrementCount()` on
the counter upon completion of their work. Once the counter's internal "count"
reaches zero, the blocked thread unblocks.

Example:

```cpp
void Foo() {
  BlockingCounter things_to_process(things.size());
  Process(&things_to_process)
  things_to_process.Wait();
}

void Process(BlockingCounter* things) {
  // Do stuff
  things->DecrementCount();
  return;
}
```
