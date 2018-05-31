---
title: "Revisiting Regular Types"
layout: blog
sidenav: side-nav-blog.html
published: true
permalink: blog/20180531-regular-types
type: markdown
category: blog
excerpt_separator: <!--break-->
---

_Good types are all alike; every poorly designed type is poorly defined in its
own way._ - Adapted with apologies to Leo Tolstoy

By [Titus Winters](mailto:titus@google.com)

### Abstract

With 20 years of experience, we know that Regular type design is a good
pattern - we should model user-defined types based on the syntax and semantics
of built-in types where possible. However, common formulations of Regular type
semantics only apply to values, and for performance reasons we commonly pass by
reference in C++. In order to use such a reference as if it were its underlying
Regular type we need some structural knowledge of the program to guarantee that
the type isn't being concurrently accessed. Using similar structural knowledge,
we can treat some non-Regular types as if they were Regular, including reference
types which don't own their data. Under such an analysis, `string_view` indeed
behaves as if it were Regular when applied to common usage (as a parameter).
However, `span` does not, and further it is (currently) impossible to have
shallow copy, deep compare, and Regular const semantics in the same type in C++.

This analysis provides us some basis to evaluate non-owning reference parameters
types (like `string_view` and `span`) in a practical fashion, without discarding
Regular design.

<!--break-->

## Introduction

What are Regular types? In the space of type design, "Regular" is a term
introduced by Alexander Stepanov. (The online/reduced form is [Fundamentals of
Generic Programming](http://stepanovpapers.com/DeSt98.pdf) which I will cite in
this essay. You're encouraged to read the full book "Elements of Programming"
for a more complete treatment.) By and large, the term Regular is meant to
describe the syntax and semantics of built-in types in a fashion that allows
user-defined types to behave sensibly.

"The C++ programming language allows the use of built-in type operator syntax
for user-defined types. This allows us, as programmers, to make our user-defined
types look like built-in types. Since we wish to extend semantics as well as
syntax from built-in types to user types, we introduce the idea of a Regular
type, which matches the built-in type semantics, thereby making our user-defined
types behave like built-in types as well."

A vastly-simplified summary, that has become popular in C++ design in later
years, is "do as the ints do." Generally speaking, for a snippet of generic code
operating on some type `T`, if it works properly on ints and also works properly
for your new type (similarly bug-free/comprehensible/etc.), you've designed a
reasonable type.

## Definitions of Regular

In fact, this evaluation of generic code is inherent in the (somewhat flexible)
definitions for Regular; Stepanov defines certain properties for Regular, but
different formulations may include a slightly different set of requirements. In
particular, proposal [P0898](http://wg21.link/p0898) aims to define Concepts for
use in the C++ standard library; the requirements for Regular as presented in
P0898 are somewhat reduced from Stepanov's definition (ordering is not
required). The crux of this difference seems to be that Stepanov's definition
stems from the requirements of a type with respect to the full set of C++98-era
standard algorithms, while P0898 focuses primarily on the requirements to be
used in a more modern library (specifically, the Ranges library as specified in
Range v3 and/or the Ranges TS).

<table>
<thead>
<tr>
<th><strong>Stepanov's Regular Requirements</strong></th>
<th><strong>P0898 Concept Requirements for Regular</strong></th>
</tr>
</thead>
<tbody>
<tr>
<td>Default constructor</td>
<td>DefaultConstructible</td>
</tr>
<tr>
<td>Copy constructor</td>
<td>CopyConstructible</td>
</tr>
<tr>
<td>Destructor</td>
<td>Destructible</td>
</tr>
<tr>
<td>Movable?</td>
<td>Movable</td>
</tr>
<tr>
<td></td>
<td>Swappable</td>
</tr>
<tr>
<td>Assignment</td>
<td>Assignable</td>
</tr>
<tr>
<td>Equality</td>
<td>EqualityComparable</td>
</tr>
<tr>
<td>Inequality</td>
<td>EqualityComparable</td>
</tr>
<tr>
<td>Total Ordering</td>
<td></td>
</tr>
</tbody>
</table>

Note: it’s generally assumed that Move construction would be included in
Stepanov’s formulation, although move semantics were not present in C++ of that
era. This is true even though `int` doesn’t have a move constructor: it is
still move constructible (can be constructed from a temporary), and this is
even the proper design for the type. Move+copy should be considered an overload
set for optimization purposes. For more information, see
[TotW 148](/tips/148))

In either case, it's important to bear a few (related) ideas in mind:

-   The various definitions of a Regular type are more alike than they are
    different.
-   After 20 years of experience, we're confident that the definition of a
    Regular type is a useful abstraction, and approximates the right "default
    semantics" for user defined types.
-   The definitions for a Regular type come from use in generic contexts. The
    essential aim is to define the syntax and semantics of a value type that
    mimics the behavior of a built-in type. The semantics of Regular allow us to
    reason about the use of the type within an algorithm, and hence define what
    the algorithm does.
-   The reasoning about code is much easier if the code consists of Regular
    types, instead of non-Regular ones, using the existing understanding of how
    built-in types work.

Both definitions focus heavily on **semantics** not just **syntax**. It is from
these basic semantic properties of types that we find design invariants like the
idea that copy, comparison, and const-ness are related. For instance, consider
four of the most basic semantic requirements on Regular types from Stepanov's
early paper:

```c++
// comparison follows from copy
T a = b; assert(a==b);

// copy and assignment are the same
T a1; a1 = b; T a2 = b; assert(a1 == a2);

// copy/assignment is by value, not reference
T a = c; T b = c; a = d; assert(b==c);

// zap always mutates, unmutated values are untouched
T a = c; T b = c; zap(a); assert(b==c && a!=b);
```

The above are enough to define copy and assignment semantics: `T` has
copy/assignment that operate by value, not by reference. However, all of this is
assuming we have an ability to define equality. Stepanov points out that
defining equality is a little squishy.

"Logicians might define equality via the following equivalence:

```
x == y ⇔ ∀ predicate P, P(x) == P(y)
```

That is, two values are equal if and only if no matter what predicate one
applies to them, one gets the same result. This appeals to our intuition, but it
turns out to have significant practical problems. One direction of the
equivalence:

```
x == y ⇒ ∀ predicate P, P(x) == P(y)
```

is useful, provided that we understand the predicates P for which it holds. We
shall return to this question later. The other direction, however:

```
∀ predicate P, P(x) == P(y) ⇒ x == y
```

is useless, even if P is restricted to well behaved predicates, for the simple
reason that there are far too many predicates P to make this a useful basis for
deciding equality."

Programming languages inherently contain predicates that don't exist in pure
math, because the execution on computing hardware is a somewhat leaky
abstraction. Consider: the question of "Are x and y aliases for the same memory
location?" This is an easy predicate to write in C++, but nonsense for a
traditional logician. In general, we focus on predicates that observe "the
value" rather than the identity of the instance.

Stepanov goes on to describe the built-in notion of equality for most types:
bitwise equality for ints and pointers. Floating point values are glossed over a
bit via "although there are sometimes minor deviations like distinct positive
and negative zero representations." From this as a basis, we can begin to build
up a definition of equality for aggregates, but immediately get into trouble
because of heap allocations. "... objects which are naturally variable sized
must be constructed in C++ out of multiple simple structs, connected by
pointers. In such cases, we say that the object has **remote** parts. For such
objects, the equality operator must compare the remote parts ..."

This reasoning continues, including some discussion about the physical state vs.
logical state of a type (for instance: the capacity of a vector does not figure
into its equality comparison, nor does the use of SSO affect equality comparison
for string).

Ultimately, Stepanov proposes the following definition, "although it still
leaves room for judgement":

**"Definition**: two objects are equal if their corresponding parts are equal
(applied recursively), including remote parts (but not comparing their
addresses), excluding inessential components, and excluding components which
identify related objects."

If we have a solid understanding of how to compare two instances of our type (by
value, focusing on the logical state, not comparing by identity/memory
location), and if our type implements all the syntactic/semantic requirements
for Regular then we have implemented a Regular type. That should always be our
starting point when designing a value type.

## Modern Regular Types and const

With an agreed-upon understanding of Regular, we can start to examine the ways
that Regular is used. We can reasonably assume that a Regular type can be fed
through standard algorithms, since that's a primary motivation for defining
Regularity (or, conversely, the implied requirement for the algorithms, although
the legacy algorithms are rarely specified in terms of semantic requirements).

So we can certainly express that this is safe and correct for Regular types,
yes?

```c++
void DoSomething(const T& t);  // May be any valid C++

const T a = SomeT();
const T b = SomeT();
if (a == b) {
  DoSomething(a);
  assert(a == b);  // Note: we're assuming the semantics of ==
}
```

This seems straightforward: we have two const values. If they are equal, it
doesn't matter what operation we perform on one of them, they will remain equal.
It also doesn't matter if we modify any other global state. It does imply one
additional requirement beyond being Regular: the normal semantics of `const` 
must be enforced - a const object must not change values. Consider the
following type and body for `DoSomething`:

```c++
class Rotten {
 public:
  Rotten();
  Rotten(const Rotten& rhs) : val_(rhs.val_) {}
  Rotten& operator=(const Rotten& rhs) { val_ = rhs.val_; return *this; }

  bool operator==(const Rotten& rhs) const { return val_ == rhs.val_; }
  void Increment() const { val_++; }

 private:
  mutable int val_ = 0;
};

void DoSomething(const Rotten& r) { r.Increment(); }
```

This `Rotten` type meets the syntactic requirements for P0898 Regular: it is
DefaultConstructible, CopyConstructible, Movable, Swappable, Assignable,
EqualityComparable, and it has the semantics for all of those operations. Where
it _fails_ is in the General front-matter for standard library concepts.
Consider, from P0898r2: "except where otherwise specified, an expression operand
that is a non-constant lvalue or rvalue may be modified. Operands that are
constant lvalues or rvalues must not be modified."

This restriction (while being a little squishy about "modified"), plus the basic
ideas of "equality" are enough to see that for at least the **logical** state of
a type, const must mean const. Since `Rotten` goes out of its way to break that,
the P0898 formulation of Regular rightly spots that bad type design and forbids
it.

Since the original Stepanov paper never discusses const, but const is tied
deeply to modern type design, I'll primarily focus the remainder of the
discussion on P0898 for simplicity and clarity.

## Data Races and Thread Safety Properties

Let us digress a little to discuss something that is unrelated on the surface,
but critical to the ensuing discussion: data races and the thread safety
properties of types.

Very significant essays and presentations can (and should) be produced on the
topics of data races in C++ and the thread safety properties of types. The
following is at most a surface treatment. If you are unfamiliar with this
domain, please find a good in-depth tutorial/refresher rather than relying on
only this brief summary.

More or less: a data race occurs when at least one memory location is written by
one thread and accessed (read or write) by another thread without
synchronization between those operations. Any number of threads may read
concurrently, but if any thread is writing, you must synchronize those
operations. That synchronization can take many forms, ranging from the use of
`std::atomic` up to a mutex or higher-level synchronization primitive. But no
matter what you think you know about how execution works on your processor, on
the C++ abstract machine there is no such thing as a safe data race. The C++
standard specifically calls this out: data races are undefined behavior. No
correct program has undefined behavior. There is no wiggle room.

At a slightly higher level: how do we tell the difference between a read
operation and a write operation for a type? For user-defined types we look at
the API documentation, where the `const` qualifier nicely summarizes the
read/write semantics of the API. For the vast majority of types (i.e. those that
have the same thread-safety behavior that `int` does), concurrent
(non-synchronized) calls to `const` methods are allowed, but if any concurrent
call is made to a non-`const` method, there is the chance for a data race.

For instance: if you have an `optional<int>` shared among many threads, those
threads may all ask `has_value()` or read from the contained `int`, so long as
none of them overwrites the `int`. Such a store would take place via `operator=`
(non-const) or assigning to the reference returned by the non-const overloads of
`value()`.

It has become common practice to classify types as either "thread-safe",
"thread-compatible", or "thread-unsafe", based on the conditions under which use
of its API may result in a data race.

-   **Thread-safe**: No concurrent call to any API of this type causes a data
    race. This is useful for things like a Mutex. Generally speaking,
    thread-safe types are easiest to work with, but you pay for some of that
    usability in performance or API restrictions or both.
-   **Thread-compatible**: No concurrent call to any `const` operation on this
    type causes a data race. Any call to a non-`const` API means that instance
    must be used with external synchronization. C++ guarantees that standard
    library types are at least thread-compatible. This follows from the general
    pattern of Regular design, and "do as the ints do" as `int` is
    thread-compatible. In most cases, this is in-line with the philosophy of
    C++ - you do not pay for what you do not use. If you operate on an
    `optional<int>`, you can be sure that it isn't grabbing a mutex. On the
    other hand, thread-compatible may have overhead in some cases:
    `shared_ptr<>` is unnecessarily expensive in cases where there is no sharing
    between threads, because of the use of atomics to synchronize the reference
    count.
-   **Thread-unsafe**: Even concurrent calls to `const` APIs on this type may
    cause data races - use of an instance of such a type requires external
    synchronization or knowledge of some form to be used safely. These are
    generally either used with a mutex or are used with knowledge like "I know
    that this instance is only accessed from this thread" or "I know that my
    whole program is only single threaded." Types like this may be because of
    `mutable` members, or because of non-thread-safe data that is shared between
    instances.

It is worth mentioning that "const means const" is _almost_ enough to ensure
that a type is thread-compatible. It is possible to have members in your type
that are not part of the logical state (for example: a reference count) but are
mutable (either via the mutable keyword or through something like a
const-pointer-to-non-const) and thus cause data races even when only const APIs
are invoked. There's a strong conceptual overlap between const-ness
(conceptually, including both syntax and semantics) and thread-compatibility,
and that overlap is actually equivalence in the case that there are no such
mutable members.

Now considering thread-safety and const-ness, we can consider whether either the
Stepanov or P0898 definitions of Regular say everything we want. If we're
following the model of `int` or the good standard library types, Regular types
have a powerful property: if you have a `const T`, and pass that instance as
`const T&` to some function that function can do nothing that can make your `T`
change value (that isn't inherently UB), become invalid, or otherwise become
harder to use. In order to hold that property, your Regular type needs to be
thread-compatible, or you need to constrain the function (promise to not share
this instance among threads, for instance). Both approaches are useful.

## Dependent Preconditions

One property of Regular that never seems entirely satisfying in less formal
design conversations is that both `int*` and `std::string` are equivalently
Regular, although any programmer will tell you that there is a lot more to worry
about when working with `int*`: there are preconditions when using an `int*`
that are harder to ensure than any precondition when using `std::string`.

For instance, `std::string::operator[]` has a precondition roughly of the form,
`index < size()`. In fact, the only APIs on `std::string` that have
preconditions of any form fall into two clear categories:

-   They are requirements that can be checked using other methods from the
    `string` API. For instance, the above precondition on `operator[]` can be
    checked by calling `size()`.
-   They are requirements entirely focused on the data being passed in, not on
    `string` itself. For instance, the `const char*` constructor (non-NULL,
    valid allocation, nul-terminated), or the iterator-range
    construction/assignment operations (valid range).

For comparison, `int*` has at least one precondition of a fundamentally
different flavor:

-   `operator*` - Requires that the pointer holds the address of a live `int`
    object.

This cannot be checked via any operation on `int*`, nor can it even be checked
portably in any fashion given an arbitrary `int*`. Invoking this operation
safely **requires** structural knowledge of the program. A type that has
**dependent preconditions** has one or more such APIs; these are often (but not
always) about properties of non-owned objects/external memory/etc.

APIs that have dependent preconditions are more complicated to use - they
fundamentally require knowledge about the rest of the program in order to use
safely. Types that have no such APIs are easier to use, and it is no surprise or
coincidence that the majority of types that we consider "good" avoid this
property. Or, put another way, types with dependent preconditions have a weaker
form of the property we want from Regular: when passing a `const T&` to a
function, that function may be able to invalidate the preconditions on some API
of `T` through mechanisms that are outside of `T`. It isn't enough to say that
`T` is thread-compatible - we must know that nothing in the program is going to
invalidate the dependent preconditions.

Let's consider `int*` in the context of our Regular-code usage snippet:

```c++
using T = int*;
void DoSomething(const T& t);

const T a = SomeT();
const T b = SomeT();
if (a == b) {
  DoSomething(a);
  assert(a == b);
}
```

Is it really the case that `DoSomething()` can do anything we want and leave
this snippet intact? For an `int*`, it definitely isn't - certainly not to the
same extent as it is for `int`. (There is perhaps some overlap between this and
Lisa Lippincott's recent work [What is The Basic
Interface](https://www.youtube.com/watch?v=s70b2P3A3lg).)

For instance, if we dereference the pointer, we may have introduced a data race:
`int*` is only thread-compatible if never dereferenced, but we do not have
knowledge that nothing else is modifying the underlying `int`. Or worse, if we
dereference and **write** to the pointer, we make it a race if any thread is
even reading the `int`.

```c++
void DoSomething(int* const t) { std::cout << *t << std::endl; }
```

P0898r2 gets at some of this in [concepts.lib.general.equality] p3: "Expressions
required by this specification to be equality preserving are further required to
be stable: two evaluations of such an expression with the same input objects
must have equal outputs absent any explicit intervening modification of those
input objects. [ Note: This requirement allows generic code to reason about the
current values of objects based on knowledge of the prior values as observed via
equality preserving expressions. **It effectively forbids spontaneous changes to
an object, changes to an object from another thread of execution, changes to an
object as side effects of non-modifying expressions, and changes to an object as
side effects of modifying a distinct object if those changes could be observable
to a library function via an equality preserving expression that is required to
be valid for that object**. — end note ]"

In order to reason about a type that has dependent preconditions (like `int*`),
to use it in standard algorithms, or to do much of anything with the type, we
must have additional knowledge: why do we know that a given instance is being
used in a race-free fashion?

The same is implicitly true for traditional Regular types. When handed a
newly-constructed `std::string`, you know everything you need to know in order
to operate on that object safely, even in the face of data races. If you don't
pass it to another thread, it isn't shared. You are data race free purely by
virtue of having the object and knowing there are no additional (mutable)
references to it anywhere. If we instead only hand you a `std::string&` (as is
the case for basically all usage of standard algorithms), we don't actually have
that knowledge. Without knowledge that it is unshared, you cannot compare it or
copy it in a race free fashion.

This requirement is unstated, and pervasive. Everything in the Stepanov-era
standard library implicitly assumes it. In the Ranges/Concepts era, we get text
like P0898, rightly forbidding spontaneous changes to an object. But in the
general case, the standard already says this, because of the language rules on
data races, and the library rules that require most library types
are effectively thread-compatible.

Put another way: what do you need to know when invoking a standard algorithm on
some user-defined type? You need to know the syntax and semantics of its basic
API - it needs to be Regular. But you also need to know that invocation of the
algorithm on that instance is race free. A few types give you that by being
thread-safe. The rest of the time, you have to know something about the
structure of your program and how your instance interacts with the program in
order to guarantee race-free.

Interestingly, it isn't only `operator*` on a pointer that has dependent
preconditions: it is implementation-defined behavior to invoke `operator==` on a
pointer after the underlying object has been deleted. According to Richard
Smith, it is "as-if we scribble over every pointer in the program that points to
the object at the time of deletion." So if we have

```c++
void DoSomething(int* const t) { delete t; }
```

we are already off in the realm of non-portable programs. And while
implementation-defined is less bad than undefined, this does further demonstrate
that even `operator==` for `int*` has preconditions that are impossible to
check - we have to rely on structural knowledge of the program to use pointers
correctly.

Which, luckily, clarifies most people's intuition: pointers are more complicated
than the other types we talk about as Regular. There's room for expansion in our
definition / usage / discussion of Regular. I believe that the missing piece for
Regular is "thread compatible" in the general case (although there are other
valid options), and existing design precedent in the library already follows
that direction. Builtins and our vocabulary types are both Regular and
thread-compatible.

## Flavors of Race-Free, plus Regular

While Regular+thread-compatible is the most common (and most like `int`)
combination that actually describes good/built-in-like types, other options may
work in some situations. These options correspond roughly to the answers for
"How do you know that operations on this instance do not cause data races?"

For any given instance of a type, you might know one of several possible things
that allow you to operate on it race-free.

-   **Thread-compatible** and not shared with other threads for writing. If
    you've been handed a (non-racing) `const T&` you can operate on this in
    const fashion. If necessary, you can copy it to ensure there are no lurking
    references and perform any computation / mutation safely (but
    inefficiently). With minor knowledge (the instance isn't shared), a `T&` can
    be used safely as if it were `T`.
-   It has **dependent-preconditions**, but for a particular instance + any
    dependent data, the program structure guarantees safe usage.
-   **Single-threaded usage** - There is only one thread in the program and thus
    all instances of the type are safe to use, or a given instance is known to
    not be shared among threads.

P0898r2's [concepts.lib.general.equality] p3, cited above, would fix the
standard library's stance on Regular to be entirely the first option ... at the
cost of pointers not being considered Regular because of semantic requirements
and implementation-defined behavior on comparison. (If deletion is "as-if all
other pointers to this object are scribbled over" that certainly violates the
restriction on the value of the object changing out from under us.)

All three of these options provide points in the type design space that are
useful in conjunction with the existing definitions for Regular.

-   **Thread-compatible** + Regular is what we really want for user-defined
    types that mimic built-ins. This lets us reason about an instance in the
    expected fashion and use it efficiently in conjunction with generic
    algorithms. Types that have mutable data may have some overhead to support
    this.
-   **Dependent-preconditions** with knowledge that an instance + its dependent
    data are safe to use. This is the common usage for `string_view` when we use
    it as a non-owning parameter type: the underlying buffer will outlive the
    function call and is immutable for the duration of the call. Given that
    external knowledge of that underlying buffer, `string_view` behaves as if it
    were Regular. This makes sense, given that `string_view` was designed to be
	a drop-in replacement for `const string&`, and although references are not
	Regular types, `std::string` types are.
-   **Single-threaded usage** - This is easy to misuse, but can be an important
    area for optimization. Consider the discussions to provide a `shared_ptr`
    analogue that does not synchronize its reference count - if we know
    something about program structure, or can guarantee particular usage for an
    instance, we can design a more efficient type in this fashion. Given that
    knowledge, such a `shared_ptr` can still behave as if it were Regular.

Given a type and one of the above options to explain why it is safe to use a
given instance, we can see that our nice property for Regular types still holds.
Given a `const T` (and some program knowledge), we can perform any operation
(that conforms to that program knowledge) on that `const T` without invalidating
it or any of its API preconditions. Regular+thread-compatible types allow us
this invariant with no constraints on the program or that operation. Lesser
invariants require more knowledge - in return we tend to get lower-overhead,
which is a very C++ style of tradeoff.

## Evaluating `string_view`

If we know that the underlying buffer exists and is not being mutated,
`string_view` behaves as if it were Regular: it is DefaultConstructible,
CopyConstructible, Movable, Swappable, Assignable, EqualityComparable. If the
underlying buffer is immutable for the life of our instance, the General Matter
rules in P0898 don't kick in: the value won't magically change out from under
us.

```c++
using T = string_view;
void DoSomething(const T& t);

const T a = SomeT();  // Assume SomeT() is providing a
                      // long-lived and stable buffer.
const T b = SomeT();

if (a == b) {
	
  // Won't modify the buffer, provided our assumption on SomeT() is correct.
  DoSomething(a);

  assert(a == b);
}
```

We can go back to Stepanov's axioms about assignment and comparison.

```c++
string_view a = b; assert(a==b);
string_view a1; a1 = b;  string_view a2 = b; assert(a1 == a2);
string_view a = c; string_view b = c; a = d; assert(b==c);
string_view a = c; string_view b = c; zap(a); assert(b==c && a!=b);
```

So long as the values we are assigning to represent buffers that outlive the
`string_view` and remain immutable, these axioms are held. (`zap()` has to
actually change its parameter so that pre/post calls to `zap` are not equal -
but remember that equality is about value not identity)

If we do **not** know that the underlying buffer exists and is not being
mutated, we cannot evaluate any of these snippets. Even executing `operator==`
runs the risk of undefined behavior either from use-after-free (if the buffer
has disappeared) or data race (if the buffer is mutated).

Remember that this is a lot to ask: this knowledge of the underlying buffer is a
lot more than the knowledge required when operating on something Regular like a
`string`. I've probably seen hundreds of bugs stemming from people getting the
object lifetimes wrong with `string_view` and its underlying buffer.

Without that external knowledge, it's easy to see how we fail with all of
Stepanov's axioms (assign these `string_view`s to temporaries). Similarly,
without that knowledge, we fail at P0898r2's [concepts.lib.general.equality]
p3 - the value can change out from under us. We get (countless) examples like
this:

```c++
string s1 = "hello";
string s2 = "hello";

string_view SomeT() {  // Give out references to different global strings
  static int count = 0;
  string_view ret = (count == 0 ? s1 : s2);
  count = (count + 1) % 2;
  return ret;
}

void DoSomething(const string_view sv) {  // modify an unrelated global
  s1[0] = 'a';
}

void f() {
  const string_view sv1 = SomeT();
  const string_view sv2 = SomeT();
  if (sv1 == sv2) {      // equal
    DoSomething(sv1);    // No program structure constraints, can modify a global.
    assert(sv1 == sv2);  // failure: "aello" != "hello"
  }
}
```

Side note: At some level I think this is a bogus example. Having participated
for many years in mailing list discussions about the Google-internal type that
inspired `string_view`, the way that people mishandle `string_view` has nothing
to do with mutability of the underlying data, and everything to do with the
underlying data being unowned and going out of scope. I estimate the prevalence
of lifetime-requirement failure vs. underyling-mutability failure to be at least
50:1 - the risks of a type like this are almost entirely based around lifetime,
not remote-mutation. It's also much easier to construct an example for this
snippet that fails because of insufficient buffer lifetime.

So no, `string_view` isn't quite Regular. Given particular very constrained
usage, it behaves as if it were Regular. That usage is very nearly **required**
by the rest of the standard - you can't even compare a `string_view` without
undefined behavior unless you have knowledge about the program structure to
guarantee that operation is safe. However, with that knowledge, `string_view`
still behaves as if it were Regular.

## Non-owning Reference Parameters

C++ is a language that is very concerned with 2 things: types, and efficiency.
The type system for C++ is more complex than most other languages by a
significant margin: this is the only mainstream language that I can imagine
where it's reasonable to envision a proposal for an infinite family of Null
types (P0196).

At the same time, C++ focuses a great deal of effort on "do not pay for what you
do not use". We have a preponderance of non-Regular types in the core language:
references are not Regular, but they are _efficient_. Passing by reference is
basic - when invoking a function we don't necessarily want to _copy_ anything,
we merely give a reference for the duration of the function call. An increasing
amount of modern design is about providing flexibility when it comes to the
specific types that are accepted - we overload on `const char*` and `const
string&`, or we just accept `string_view`. Other user-defined types that have a
contiguous buffer of characters can join in our overload set by providing a
conversion to `string_view`.

This is, in some respects, one of the big areas for design work in C++ these
days: building an increasing set of generic/type-erased types that accept a
broad selection of related types and provide a uniform interface. Consider
`function`, `function_ref`, `span`, and `string_view`, from recent standards
discussion. In Google's codebase I'm starting to see types like `AnySpan` which
behave like `span` but further abstract `T` away from the underlying type
(allowing non-null `unique_ptr` and `T*`, for instance).

From a usability perspective, we have to decide whether we are continuing down
the path of building types that represent our duck-typing overload sets, or
whether we are asking users to implement those overload sets inconsistently on
an ad-hoc basis. I'm fairly sure that most of us will conclude that there is
value in using these non-owning reference parameter types - if we can agree on
how to design them.

**When used as a parameter**, we always know that the underlying data continues
to exist and is as safe to access as making a copy of the data would have been.
(That is, if the underlying data is a reference itself, and we don't know if
anything is mutating it, we're already in trouble.)

Restated: the arguments against `string_view` and other reference types are that
they are not Regular. And that's true, they aren't when evaluated in a vacuum.
But if you have any structural knowledge about the program, they behave as if
they are Regular in their most common usage - as parameters.

So since we're probably going to keep building non-owning reference parameter
types, can we stop arguing about them being bad because they aren't Regular?
They may be Regular enough for the use case they are designed for, and if a C++
programmer chooses to use them for more, they'll still usually be Regular given
knowledge of the lifetime of their referent. (Or the lifetimes won't match up
and we'll be cursed for being a hard language, but that's unavoidable.)

Taking into account APIs with dependent preconditions and implementation-defined
behavior on deleted pointer comparison, `string_view` is no worse than `int*`,
after all.

## Evaluating `span`

When discussing reference types in the standard, the two common points of
reference are `string_view` (already voted in with C++17) and `span` (heading to
the working draft for C++20). Although there are numerous syntactic differences
in the APIs of these two, semantically the major difference is in the mutability
of the underlying data. A `string_view` is either a lightweight reference to a
string that it will not mutate, or a non-owning pointer+length to a buffer it
will not mutate (depending on whose conceptualization you follow), but in either
case it does not mutate the underlying buffer. A `const string_view` is only
interesting in that it cannot be trimmed nor reassigned.

On the other hand, `span<T>` allows non-const operations on the underlying `T`.
If `span` were a container like `vector` we would know that a `const span` would
imply only `const` access to the underlying `T`. In this sense, when comparing
to `string_view` we have no precedent to draw upon.

Let's apply the idea that we want `span` to be as close to Regular as possible.
What would it take for us to operate on an instance as if it were Regular? Keep
in mind that we are already assuming that the program structure forbids mutation
of the buffers except via the `span` directly and thus `DoSomething()` cannot
modify `a1` or `a2`.

```c++
std::array<int, 3> a1 = {1, 2, 3};
std::array<int, 3> a2 = {1, 2, 3};
const span<int> s1 = a1;
const span<int> s2 = a2;

if (s1 == s2) {
  DoSomething(s1);
  assert(s1 == s2);
}
```

We know that can only use `span` as if it were Regular if we know that the
underlying buffer isn't being mutated by anything else. But that isn't enough
here: it's easy to imagine a `DoSomething` that modifies a value through the
`const span` and then breaks our assertion.

```c++
void DoSomething(const span<int>& s) {
  s[0] = 42; // Having a const span<T> doesn't make the underlying T const
}
```

Perhaps what we want is for `span` to only provide const access to the buffer
when the span is const? We could make the const overload of `span::operator[]`
provide `const T&`. Unfortunately, this isn't enough for a copyable type.

```c++
void DoSomething(const span<int>& s) {
  span<int> copy = s; // Copying drops const but leaves the referent
  copy[0] = 42;  // Can modify through the copy
}
```

We have to treat the `span` and its dependent data as one, and that treatment
must include const propagation. Unfortunately, we cannot get shallow copy (copy
by pointer), const propagation (const reference implies const referent), and
deep equality (compare by pointee) in the same type. You can, however, get close
enough to const propagation by disallowing mutation of the underlying buffer.

For non-owning reference parameters like `string_view` and `span`, merely
knowing the underlying buffer isn't being mutated externally isn't enough for it
to be used as if it were Regular. We need to make one further choice:

-   The data cannot be mutated through the reference type, a la `string_view`
-   Equality is shallow: the logical state of the type is tied to the value of
    the pointer, rather than the value of what it points to
-   The reference type is designed in a clever fashion so that once you have a
    `const Reference<T>`, copies become at most `Reference<const T>`. (I suspect
    this is impossible in the language currently, and even if it isn't it is
    likely to be awkward to work with, but I'm intrigued at the possibility).

The stated aims of `span` (to replace easily-mishandled instances of `T*, len`)
cannot be met while having both Regular semantics and deep equality - the
logical state of the type must be only the pointer+length, not the underlying
unowned data. When given the choice, we should prefer to be more like Regular
and change to shallow equality. It's still arguable whether it will be Regular
(dependent preconditions on `operator[]`, and implementation-defined behavior
for comparison on a deleted pointer), but it will be much closer.

With such a change to its comparison, and knowledge that the underlying buffer
isn't being modified, `span` will behave as if it were Regular. Given a `const
span` and the required knowledge about its buffer, nothing we do to it can make
its value change or invalidate any of its API preconditions.

## Conclusion

If you have got the option, make your value types Regular and thread-compatible
with no mutable or shared state. Do not take any of the above as justification
to break that commandment lightly.

That said, Regular as everyone describes it does gloss over some things - we
operate on Regular types by reference in standard algorithms constantly, and
those operations aren't safe without some form of structural knowledge of the
program. Usually that knowledge is of the form "this instance isn't shared to
any other thread." The best Regular types, those that model built-ins most
closely, are thread-compatible and have no dependent preconditions. Types like
`int` and `string` are easier to work with than `int*` or `string_view`.

When it comes to non-owning reference types like `string_view` or `span`, the
required structural knowledge is more complex: it isn't only that the instance
isn't shared, it's that the instance plus its underlying data isn't shared in a
way that will cause data races. When operating on a type arbitrarily, that is
hard to prove. But in the very common (and very relevant to C++ design
priorities) case of building cheap non-owning reference parameters, we have that
knowledge because of how parameter passing and function invocation work.

If knowledge that the underlying data isn't shared is enough to make usage of an
instance passed as a parameter behave like Regular, that is good. These types
like `string_view` will have more sharp corners and take some getting used to,
but in practice most of the problems come from underlying buffers going out of
scope when used not as a parameter. Critically, such types must not allow
mutation of their unowned underlying data.

For types where we want reference semantics but must allow for mutation of the
underlying data, we must yield something. It is currently impossible to have a
type that has shallow-copy, deep-compare, and Regular behavior when propagating
const-ness: one or more of those properties must be given up. The expected usage
of every type is different, so it is hard to provide one-size-fits-all guidance,
but consider the following options:

-   **shallow compare** - Make the type compare based on what it points at by
    identity (pointer value) rather than dereferencing the underlying data.
-   **SemiRegular** - P0898 specifically defines the concept *SemiRegular* to
    denote types that are Regular except for a lack of `operator==`. These are
    still perfectly suitable for storing in many types of containers. Dropping
    `operator==` will leave no users confused at runtime when equality semantics
    do not match their expectation.

If equality isn't the culprit for your type being irregular (even given
knowledge of program structure), cut or rename the offending operations until it
is a strict subset of Regular - it is better for your type to not reuse common
syntax for operations that have non-Regular semantics.

As a satisfying side-note: classifying types based on the form of structural
knowledge they need in order to operate on them safely provides us a way to
separate types like `int` and `int*`. It has long been unsatisfying that
pointers and values were both considered Regular in exactly the same fashion.

Accounting for this variation in "how much information do we need when working
on an instance of this type safely", we can look at reference types when their
underlying data is extant and constant and determine whether the rest of their
usage still looks Regular. Pleasantly, `string_view` works fine. We do find some
weaknesses in the current `span` proposal, particularly when it comes to shallow
vs. deep const.
