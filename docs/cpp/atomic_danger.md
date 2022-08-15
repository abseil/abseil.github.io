---
title: "The Danger of Atomic Operations"
layout: docs
sidenav: side-nav-cpp.html
type: markdown
---

# The Danger of Atomic Operations

Dmitry Vyukov, Sanjay Ghemawat, Mike Burrows, Jeffrey Yasskin, Kostya
Serebryany, Hans Boehm, Ashley Hedberg

First written Apr 22, 2014. Updated Jun 23, 2021.

-   [The danger of atomic operations](#the-danger-of-atomic-operations)
-   [Introduction](#introduction)
-   [Existing Components](#existing-components)
-   [Atomic Trickiness](#atomic-trickiness)
-   [Performance Considerations](#performance-considerations)
-   [Testing Considerations](#testing-considerations)
-   [Bug Examples](#bug-examples)

## Introduction

Most engineers reach for atomic operations in an attempt to produce some
lock-free mechanism. Furthermore, programmers enjoy the intellectual puzzle of
using atomic operations. Both of these lead to clever implementations which are
almost always ill-advised and often incorrect. Algorithms involving atomic
operations are extremely subtle. For example, discovering a general-purpose,
efficient, lock-free, singly-linked list algorithm took significant research and
required care to implement. Almost all programmers make mistakes when they
attempt direct use of atomic operations. Even when they don't make mistakes, the
resulting code is hard for others to maintain.

Atomic operations should be used only in a handful of low-level data structures
which are written by a few experts and then reviewed and tested thoroughly.
Unfortunately, many people attempt to write lock-free code, and this is almost
always a mistake. Please do not fall into this trap: do not use atomic
operations. If you do, you will make mistakes, and those will cost the owners of
that code time and money.

There are a number of existing higher-level components that are already
carefully crafted, reviewed, and tested. Use them if they do what you need.
Otherwise, use mutexes.

Note: the document is centered around C++, but similar arguments apply to other
languages as well. See [research!rsc](https://research.swtch.com/mm) for a more
detailed discussion of hardware, programming language, and Go memory models.

## Existing Components

Reach for commonly-available concurrency components before inventing your own
solution using atomics. The list below serves as a guide, but is not exhaustive.
Libraries such as the [C++ Standard Library](https://en.cppreference.com/w/cpp),
[Abseil](https://abseil.io/), and [Folly](https://github.com/facebook/folly) all
contain relevant components.

-   [std::shared_ptr](https://en.cppreference.com/w/cpp/memory/shared_ptr) and
    [folly's hazard pointer](https://github.com/facebook/folly/blob/master/folly/synchronization/Hazptr.h)
    for reference counting
-   [std::call_once](https://en.cppreference.com/w/cpp/thread/call_once) and
    [absl::call_once](https://github.com/abseil/abseil-cpp/blob/master/absl/base/call_once.h)
    for one-time initialization
-   [boost::asio::thread_pool](https://www.boost.org/doc/libs/1_76_0/doc/html/boost_asio/reference/thread_pool.html)
    for thread pooling
-   [absl::Notification](https://github.com/abseil/abseil-cpp/blob/master/absl/synchronization/notification.h)
    for one-time notifications
-   [std::latch](https://en.cppreference.com/w/cpp/thread/latch),
    [std::barrier](https://en.cppreference.com/w/cpp/thread/barrier),
    [absl::Barrier](https://github.com/abseil/abseil-cpp/blob/master/absl/synchronization/barrier.h),
    and
    [absl::BlockingCounter](https://github.com/abseil/abseil-cpp/blob/master/absl/synchronization/blocking_counter.h)
    for barrier synchronization
-   [std::future](https://en.cppreference.com/w/cpp/thread/future) for creating
    value promises
-   [Userspace RCU](https://github.com/urcu/userspace-rcu/blob/master/doc/cds-api.md)
    for read-copy-update algorithms and lock-free containers
-   [thread_local](https://en.cppreference.com/w/cpp/language/storage_duration)
    for better locality
-   [folly's concurrency library](https://github.com/facebook/folly/tree/master/folly/concurrency)
    for concurrent storage and queues
-   [folly::TokenBucket](https://github.com/facebook/folly/blob/master/folly/TokenBucket.h)
    for rate limiting

## Atomic Trickiness

Atomic operations introduce two separate kinds of hazards:

First, unless you exclusively use atomic operations that maintain ordering
semantics for all shared memory accesses (notably `memory_order_seq_cst`
operations), both compilers and processors can and will visibly reorder memory
accesses
[per the C++ standard](https://en.cppreference.com/w/cpp/atomic/memory_order).
Programming rules in these cases become far more complicated, and experts often
still have trouble pinning them down precisely. Many people find it particularly
surprising that such reordering doesn't always stop at traditional
synchronization operations, like a mutex acquisition.

If you do restrict yourself to sequentially-consistent operations, you avoid
this issue, but may well find that your code now runs slower on ARM and POWER
than if you had used mutexes. ARM and POWER are weakly-ordered systems, so
special CPU load instructions or memory fences are required to achieve
sequential consistency. This is not required on strongly-ordered platforms like
x86.

Second, it's extremely difficult to write code in a world in which a) only
individual memory accesses are atomic, and b) no way to achieve mutual exclusion
over larger code sections exists. Object lifetime management is difficult in a
concurrent setting. [CAS-based](http://en.wikipedia.org/wiki/Compare-and-swap)
algorithms are subject to the
[ABA problem](http://en.wikipedia.org/wiki/ABA_problem). Unexpected and
unreproducible thread interleavings occur. Sequences of atomic operations are
then not atomic as a whole. Before approaching atomic operations, you must be
ready for all of these problems and understand the language memory model with
respect to ordering, atomicity, visibility, and data races.

Don't assume x86 semantics. Hardware platform guarantees matter only if you are
programming in assembly. Higher-level language (C++/Java/Go) compilers can break
your code. Furthermore, ARM and POWER provide notably different and more complex
memory models; these can also break your code if you run on a variety of
hardware.

Let's consider two examples based on real code that demonstrate these two kinds
of subtleties related to atomic operations. First example:

```c++
std::atomic<bool> data_ready = false;
double data = 0.0;

void Thread1() {
  data = 1.23;
  data_ready.store(true, std::memory_order_relaxed);
}

void Thread2() {
  if (data_ready.load(std::memory_order_relaxed))
    CHECK(data == 1.23);
}
```

The code is seemingly correct: Thread1 initializes the data first and then sets
the flag, Thread2 ensures that the flag is set and only then reads the data.
What can possibly go wrong?

With optimizations enabled, gcc compiles this code to:

```
% g++ -O2 test.cc -S && cat test.s

Thread1:
  movabsq $4608218246714312622, %rax # 1. Load the constant into RAX
  movl    $1, data_ready(%rip)       # 2. Store 1 into data_ready
  movq    %rax, data(%rip)           # 3. Store RAX register into data
  ret
```

If Thread2 is executed between instructions 2 and 3 of Thread1, the `CHECK` in
Thread2 will fail. Note that the compiler does exactly what we asked it to do.
The operations on `data_ready` are indeed atomic; they are just reordered with
other memory accesses.

Another example, this time with implicit `memory_order_seq_cst`. Here, we have a
concurrent object pool based on a lock-free stack, whose algorithm tries to work
around the ABA problem in a non-traditional way:

```c++
template<typename T>
class ConcurrentPool {
 public:
  ConcurrentPool(size_t size)
      : head_(0),
       size_(size),
       array_(new Node[size]) {
    for (size_t i = 0; i < size; i++)
      array_[i].next.store(i + 1);
    array_[size - 1].next.store(kEnd);
  }

  T* Get() {
    while (size_.load() > 1) {
      size_t head1 = head_.load();
      size_t next1 = array_[head1].next.exchange(kEnd);
      if (next1 != kEnd) {
        if (head_.compare_exchange_strong(head1, next1)) {
          size_.fetch_sub(1);
          return &array_[head1].v;
        } else {
          array_[head1].next.exchange(next1);
        }
      }
    }
    return nullptr;
  }

  void Put(T* v) {
    Node *n = reinterpret_cast<Node*>(v);
    size_t i = n - &array_[0];
    size_t head1;
    do {
      head1 = head_.load();
      n->next.store(head1);
    } while (!head_.compare_exchange_strong(head1, i));
    size_.fetch_add(1);
  }

 private:
  struct Node {
    T v;
    atomic<size_t> next;
  };

  atomic<size_t> head_;
  atomic<size_t> size_;
  unique_ptr<Node[]> array_;

  static const size_t kEnd = -1;
};
```

Before reading further try to spot the bug in this code.

The bug is basically impossible to discover by testing and manual code
inspection. It was found by an automatic checker of synchronization algorithms.
The particular execution that leads to the bug:

1.  Thread 1 reads `head_ = 0` in `Get()`.
2.  Thread 0 reads `head_ = 0` in `Get()`.
3.  Thread 0 removes element 0 from the stack, `now head_ = 1`.
4.  Thread 0 starts putting the element 0.
5.  Thread 0 reads `head_ = 1`, and sets the next field of the element 0 to 1.
6.  Thread 1 executes `exchange` on the next field of the element 0. It reads 1
    and writes -1.
7.  Thread 2 gets the element 1 from the stack, now `head_ = 2`.
8.  Thread 0 fails with `compare_exchange` in `Put()`, re-reads `head_ = 2`, and
    writes 2 to the next field of the element 0.
9.  Thread 0 succeeds with `compare_exchange` in `Put()`. Now `head_ = 0`.
10. Thread 1 succeeds with `compare_exchange` in `Get()`. Now `head_ = 1`
    (however `head_` must be equal to 2!).
11. Thread 0 pops element 1 from the stack.

Now both threads 0 and 2 work with the element 1. Bang!

## Performance Considerations

Programmers assume that mutexes are expensive, and that using atomic operations
will be more efficient. But in reality, acquiring and releasing a mutex is
cheaper than a cache miss; attention to cache behavior is usually a more
fruitful way to improve performance. Furthermore, lock-free data structures are
often more expensive than using mutexes. A mutex allows arbitrary changes to be
made to a complex data structure; if the same changes must be made without a
mutex, the result is likely to take more atomic read-modify-write and memory
fence instructions, not fewer.

People wish to avoid mutex contention when concurrency is high. Reducing
concurrency is best solved by partitioning locked data structures to avoid mutex
contention. For example, it is easier, more efficient, and more useful to build
a high-concurrency hash table from many normal hash tables, each with its own
reader-writer mutex, than to build one lock-free hash table using atomic
operations.

[Thread-local](https://en.cppreference.com/w/cpp/language/storage_duration)
caching and batching of updates of centralized state is another technique that
usually vastly outperforms centralized lock-free algorithms. For example,
[tcmalloc](https://github.com/google/tcmalloc) uses it to achieve outstanding
scaling while relying only on mutexes for synchronization.

[Reference-counting](https://en.wikipedia.org/wiki/Reference_counting) can help
to significantly reduce the size of critical sections in some scenarios. Namely,
read-lock a container, find the necessary object, increment reference counter,
unlock, and return:

```c++
V *find(T key) {
  lock_guard l(mutex);
  V *v = container.find(key);
  if (v != nullptr)
    v->refcount.Acquire();
  return v;
  // Work with the object v happens outside of the mutex.
  // Caller calls v->refcount.Release() when done with the object.
}
```

The
[Read-Copy-Update/Multiversion-Concurrency-Control](http://en.wikipedia.org/wiki/Multiversion_concurrency_control)
technique allows one to achieve linear scaling for read-mostly data structures.

## Testing Considerations

Unit tests do not provide good enough coverage for lock-free algorithms; they
explore a negligible part of all possible thread interleavings. For a small
synchronization algorithm with N=10 atomic operations and T=4 threads, the total
number of possible thread interleavings is O(T^(T\*N)) ~= 10^24. Memory order
relaxations result in an even larger number of potential executions. Unit tests
will cover a thousand executions at best.

Moreover, x86 hardware can't yield all executions possible on POWER and ARM
platforms. Code compiled with a particular version of compiler and flags may not
be able to yield executions possible with a different compiler or flags. Future
compilers are likely to more aggressively reorder memory accesses than current
compilers.

The human brain is poor at reasoning about concurrent algorithms that are not
sequentially consistent. Any non-trivial lock-free algorithm requires careful
review by several experts, verification with formal checkers, and exhaustive
stress testing on different hardware at a minimum.

Note that even mutex-based algorithms can be complex (or a lock can be simply
forgotten). Use [ThreadSanitizer](https://github.com/google/sanitizers) to test
for data races and certain kinds of deadlocks.

## Bug Examples

Here are examples of several bugs in algorithms based on atomic operations. The
bugs are harmful, tricky, and were lurking in our codebases for years.

**Linux kernel lock-free fd lookup**

The bug was introduced on
[Sep 9, 2005](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=ab2af1f5005069321c5d130f09cce577b03f43ef)
as part of a migration from a spinlock to RCU refcounting. The change introduced
a bug in how the code needs to react on a narrow window of semi-inconsistent
state exposed by concurrent updates. It was fixed ten years later, on
[Jul 1, 2015](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=5ba97d2832f8).

**Data Plane Development Kit's RTE Ring**

The bug existed in the first public release of DPDK, which was on
[Mar 11, 2013](http://git.dpdk.org/dpdk/commit/?id=af75078fece3). There was a
bug with issuing a zero objects dequeue with multiple consumers. It was possible
to get more than one thread to succeed the compare-and-set operation and observe
starvation or even deadlock in the while loop that checks for preceding
dequeues. The same was possible on the enqueue path. The bug was fixed on
[Mar 22, 2016](http://git.dpdk.org/dpdk/commit/?id=d0979646166e740917baaabc4b78ded3482226b7).

**sync.WaitGroup**

The bug was introduced on
[Jul 18, 2011](https://github.com/golang/go/commit/ee6e1a3ff77) as part of a
WaitGroup rewrite that was intended to improve scalability. The change indeed
improved performance and scalability, but it also replaced a simple mutex-based
algorithm with a trickier one based on atomic operations. The bug occured in
very rare circumstances but led to arbitrary memory corruptions. It was
discovered and fixed only on
[Apr 10, 2014](https://github.com/golang/go/commit/e9347c781be). The bug was
caused by an unexpected thread interleaving.

**Parallel GC**

The bug was introduced on
[Sep 30, 2011](https://github.com/golang/go/commit/d324f2143b2) and fixed only
on [Jan 15, 2014](https://github.com/golang/go/commit/b3a3afc9b78). The bug led
to arbitrary memory corruptions on overloaded machines. The bug was due to
unexpected thread interleaving.

**org.jctools.maps.NonBlockingHashMap**

The bug was introduced sometime before
[Feb 2009](https://twitter.com/nitsanw/status/1406871256486580229). The bug
allowed the remove operation to return the same item more than once, ultimately
due to a flaw in the Java CAS spec. It was identified on
[Jan 15, 2018](https://github.com/JCTools/JCTools/issues/205#) and fixed on
[Jan 21, 2018](https://github.com/JCTools/JCTools/commit/69786bb178f194b7dad5e4dbf84bed41db5af94e)
after much discussion.
