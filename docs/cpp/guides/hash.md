---
title: "`absl::Hash`"
layout: docs
sidenav: side-nav-cpp.html
type: markdown
---

# `absl::Hash`

The `absl::Hash` library consists of the following components:

*   `absl::Hash<T>`, a concrete hash functor object, which you can use out of
    the box
*   A generic hashing framework for specializing hashing behavior and making
    user-defined types hashable

This library is designed to be used as a replacement for
[`std::hash`](http://en.cppreference.com/w/cpp/utility/hash) and the various
other hash functors used in google3. It provides several advantages over them:

*   It can hash objects of almost any standard type, including `std::pair`,
    `std::tuple`, and most standard containers
*   It can be extended to support user-defined types. Our goal is that if it
    makes sense to hash an object of type `Foo`, then `absl::Hash<Foo>` will
    just work. These extensions are easy to write and efficient to execute.
*   The underlying hash algorithm can be changed without modifying user code,
    which allows us to improve it over time. For example, to improve performance
    and to defend against some hash-flooding attacks.

The `absl::Hash` framework is the default hash implementation for "Swiss tables"
`absl::{flat,node}_hash_{set,map}` and does not need to be explicitly specified
when working with that library.


## **TL;DR** How Do I Make My Type Hashable?

To make your type hashable, add a friend function like:

```c++
class Circle {
 public:
  ...

  template <typename H>
  friend H AbslHashValue(H h, const Circle& c) {
    return H::combine(std::move(h), c.center_, c.radius_);
  }

  ...

 private:
  std::pair<int, int> center_;
  int radius_;
};
```

where `H` refers to the existing `HashState`. If you need anything more complex
than this, please see
[Making Your User-Defined Types Hashable](#making-hashable-types) below.

To test your hash function, add a test like:

```c++
TEST(Circle, Hash) {
  EXPECT_TRUE(absl::VerifyTypeImplementsAbslHashCorrectly({
      Circle(),
      Circle(1, 2),
      Circle(2, 3),
      Circle(0, 0),
  }));
}
```

where the values passed should provide coverage for all interesting states of
the object.

For more complex cases, please see
[Testing Your Custom `AbslHashValue` Implementation](#testing-hashable-types)
below.

## Using `absl::Hash`

The `absl::Hash` framework is the default hash implementation for the "Swiss
table" hash tables. All types hashable by the `absl::Hash` framework will
automatically be hashable within Swiss tables.


For other hash table implementations, `absl::Hash` can be used just like any
other hash functor:

```c++
#include "third_party/absl/hash/hash.h"

std::unordered_map<MyKey, MyValue, absl::Hash<MyKey>> my_map;
```

Of course, this works only if `MyKey` is hashable by `absl::Hash`, i.e.
`absl::Hash` supports the `MyKey` type.

NOTE: the hash codes computed by `absl::Hash` are not guaranteed to be stable
across different runs of your program. In fact, in the usual case it randomly
seeds itself at program startup.

### Intrinsic Type Support

`absl::Hash` intrinsically supports the following types:

*   All integral types (including bool)
*   All enum types
*   All floating-point types (although hashing them is discouraged; we guarantee
    that `0.0` and `-0.0` produce the same hash)
*   All pointer types, including `nullptr_t`. Note that the pointer itself is
    hashed, not the value it points to.
*   `std::pair<T1, T2>`, if `T1` and `T2` are hashable
*   `std::tuple<Ts...>`, if all the `Ts...` are hashable
*   `std::unique_ptr` and `std::shared_ptr` (as with plain pointers, the pointer
    itself is hashed, not the value it points to)
*   All string-like types including:
    *   `absl::string_view`
    *   `std::string`
    *   `std::string_view` (as well as any instance of `std::basic_string` that
        uses `char` and `std::char_traits`)
*   All the standard sequence containers (provided the elements are hashable)
*   All the standard ordered associative containers (provided the elements are
    hashable)
*   absl types such as the following:
    *   `absl::InlinedVector`
    *   `absl::FixedArray`
    *   `absl::uint128`
    *   `absl::Time`, `absl::Duration`, and `absl::TimeZone`

NOTE: the list above is not meant to be exhaustive. Additional type support
may be added, in which case the above list will be updated.

Unlike `std::hash` and similar hashers, `absl::Hash` should **not** be
specialized. Instead, user-defined types can be made hashable by providing
an `AbslHashValue()` overload, as discussed [below](#making-hashable-types).


### `absl::Hash` Invocation Evaluation
When invoked, `absl::Hash<T>` searches for supplied hash functions in the
following order:

*   Natively supported types out of the box (see above)
*   Types for which an `AbslHashValue()` overload is provided (such as
    user-defined types). See
    [Making Your User-Defined Types Hashable](#making-hashable-types) below.
*   Types which define a `HASH_NAMESPACE::hash<T>` specialization (aka
    `__gnu_cxx::hash<T>` for gcc/Clang or `stdext::hash<T>` for MSVC)
*   Types which define a `std::hash<T>` specialization

The fallback to legacy hash functions exists mainly for backward compatibility.
If you have a choice, prefer defining an `AbslHashValue()` overload instead of
specializing any legacy hash functors. Legacy APIs can reduce the quality or
performance of the hash algorithm so their use is only recommended if
`AbslHashValue()` cannot be provided for a type.

## Making Your User-Defined Types Hashable {#making-hashable-types}

If you want your type to be hashable by `absl::Hash`, you need to define an
overload of `AbslHashValue()` for your type. The overload should combine
state with the existing hash state (denoted as `H` in the template below), and
your class must provide an equality operator.

### Example

```c++
class MyClass {
  // ...

  friend bool operator==(const MyClass& lhs, const MyClass& rhs);
  template <typename H>
  friend H AbslHashValue(H h, const MyClass& m);

 private:
  std::vector<int> v;
  std::string str;
  bool b;
};

bool operator==(const MyClass& lhs, const MyClass& rhs) {
  return lhs.v == rhs.v && lhs.str == rhs.str && lhs.b == rhs.b;
}

template <typename H>
H AbslHashValue(H h, const MyClass& m) {
  return H::combine(std::move(h), m.v, m.str, m.b);
}
```

Notice that `AbslHashValue()` is not a class member, but an ordinary function.
An `AbslHashValue()` overload for a type `Foo` should **only** be declared in
the header that defines `Foo`, and in the same namespace as `Foo`.


Also note that `MyClass` does not require adding an additional `#include` or any
`BUILD` dependency to provide its overload of `AbslHashValue()`.

### The `AbslHashValue()` Overload

An `AbslHashValue()` overload is a function template that takes two arguments:

1.  An object representing the current state of the hash algorithm, i.e. all of
    the input it has received so far, in some unspecified partially-hashed form
2.  The value to be hashed

It must return the resulting state object after combining its state to the
existing state, using the `Hash::combine()` or `Hash::combine_contiguous()`
functions. (See [Combining Hash States](#combining-states) below.)

NOTE: The hash state object type and value is unspecified except for the two
`combine*` functions. Users should not rely upon any other parts
of the state object.

If there is an `AbslHashValue()` overload that takes `Foo` as its second
argument, we say that `Foo` is "hashable".

`AbslHashValue()`'s job is to produce a new hash state by combining the input
hash state with a representation of the value, called the value's *hash
expansion*. The hash expansion is a sequence of simpler hashable values that
satisfies the following runtime requirements:

*   If two `Foo` objects are equal, then their hash expansions must be equal
*   Similarly, if two `Foo` objects are unequal, their hash expansions should be
    unequal[^unequal]
*   If two `Foo` objects are unequal, neither hash expansion should be a suffix
    of the other

[^unequal]: It can be OK for unequal values to have equal hash expansions, so
    long as that happens with very low probability. However, this is
    rarely necessary, and it degrades the quality of the final hash, so
    you should avoid it if possible.

These requirements are built on the concept of equality, so how you define
`AbslHashValue()` depends very much on how you define `operator==()`. In the
example above, two `MyClass` values are equal if and only if each of their
members are equal, so we can satisfy all the requirements for making `MyClass`
hashable by making the hash expansion consist simply of a list of those members.

More generally, if your `==` operator doesn't contain any loops or branches, but
just compares a fixed set of values, then your hash expansion should resolve to
that fixed set of values. Note that for this rule of thumb, only the code
directly in your `==` operator is of concern, not in the other `==` operators
that it calls; for example, `MyClass`'s hash expansion is just the values (`v`,
`str`, `b`), because its `==` operator doesn't contain any loops, even though it
calls `vector`'s `==` operator, which does.

### Combining Hash States {#combining-states}

Once you've figured out what your hash expansion is, you just need to combine it
with the hash state. The hash state object provides two static functions for
doing this:

*   `HashState::combine(H, const Args&...)`: Combines an arbitrary number of
    values into a hash state, returning the updated state. Each of the `Args`
    types must be hashable.

> NOTE:
>
> ```c++
>   state = H::combine(std::move(state), value1, value2, value3);
> ```
>
> is guaranteed to produce the same hash expansion as
>
> ```c++
>   state = H::combine(std::move(state), value1);
>   state = H::combine(std::move(state), value2);
>   state = H::combine(std::move(state), value3);
> ```

*   `HashState::combine_contiguous(H, const T*, size_t)`: Combines a contiguous
    array of `size` elements into a hash state, returning the updated state.

> NOTE:
>
> ```c++
>   state = H::combine_contiguous(std::move(state), data, size);
> ```
>
> is NOT guaranteed to produce the same hash expansion as a for loop but it may
> be faster. If you need this guarantee, write out the for loop instead.

Note that the state objects should always be passed by value. Furthermore, they
are move-only types (like `std::unique_ptr`), so you'll often have to use
`std::move` when passing them.

## Testing Your Custom `AbslHashValue` Implementation {#testing-hashable-types}

The Abseil hash library provides  `absl::VerifyTypeImplementsAbslHashCorrectly`
to verify that a type implements its overload correctly. This function has a few
requirements:

*   The type must implement the `==` operator correctly.
*   The caller must provide instances of the type that include any interesting
    representations for their type. (For example, a type with a small size
    optimization should include equivalent instances that use the small size
    optimization and that do not.)

```c++
TEST(MyClass, SupportsAbslHash) {
  EXPECT_TRUE(absl::VerifyTypeImplementsAbslHashCorrectly({
      MyClass(),
      MyClass(1, 2),
      MyClass(2, 3),
      MyClass(0, 0),
  }));
}
```

This call will verify that for any two elements `x` and `y` passed:

*   if `(x == y)`, then their hash expansions must be equal
*   if `!(x == y)` then their hash expansions must differ, and neither can be a
    suffix of the other.

In case of errors, `absl::VerifyTypeImplementsAbslHashCorrectly()` will print
diagnostics indicating which two elements violated these requirements.

`absl::VerifyTypeImplementsAbslHashCorrectly()` also supports testing
heterogenous lookup and custom equality operators. In this case, we would use a
tuple to pass mixed types.

```c++
// I have two types that share a `==` domain, and the hash function is
// supposed to be consistent between them.

TEST(Cord, HashMatchesString) {
  EXPECT_TRUE(absl::VerifyTypeImplementsAbslHashCorrectly(std::make_tuple(
    std::string(""), std::string("ABC"), std::string(1000,'a'),
    absl::Cord(""), absl::Cord("ABC"), absl::Cord(std::string(1000,'a'))
  )));
}

// Sometimes the types can't be directly compared, but you still want to ensure
// that equivalent values have the same hash value.
// This is rare, as it would require a custom Eq operator to match the default
// Hash.

TEST(MyClass, SupportsAbslHash) {
  EXPECT_TRUE(absl::VerifyTypeImplementsAbslHashCorrectly(std::make_tuple(
      // MyClass elements
      MyClass(),
      MyClass(1, 2),
      MyClass(2, 3),
      MyClass(0, 0),

      // MyOtherClass elements
      MyOtherClass(),
      MyOtherClass("A"),
      MyOtherClass("AB"),
      MyOtherClass("ABC"),
  ), CustomEqThatSupportsMyClassAndMyOtherClass()));
}

```

### Extending Types You Don't Own

As mentioned above, the only correct place to extend an API for a type is in the
same file that declares the type. This includes the `AbslHashValue()` extension
point.

If you want to hash objects of types you do not own, the solution depends on the
type in question, but the most common ones:

*   Use an explicit hash/equality function when declaring a hash table. Some
    types already provide these functions. For others you might need to write
    one yourself.
*   Add the extension point in the right place, or ask the owners of that code
    to do it for you.

For some known types that you may wish to hash, see the sections below for
advice.


#### Types in `std`

Most relevant types in the `std` namespace are directly supported by
`absl::Hash`. This includes all sequence and ordered associative containers.



<!--absl:google3=begin(third_party support)-->
#### Types in `//third_party` libraries and other types that we do not control

For types that we do not control the best approach is to write your own hash
function object and use it explicitly when required.
<!--absl:google3-end-->

### Making Your Types Hashable When You Cannot Use Templates

The `AbslHashValue` extension point is a function template that accepts
arbitrary hash state objects. This decouples the specific hash state from the
hash expansion code path. However, not all types can implement this function as
a template.

Two common cases where this technique fails are PImpl classes and interfaces
with virtual functions. For these cases the framework provides the class
`absl::HashState`, which is a type-erased version of the hash state object.

Usage example:

```c++
#include "third_party/absl/hash/hash.h"  // For definition of `absl::HashState`

// A class that uses the PImpl technique:

// in .h file
class MyClass {
 public:
  template <typename H>
  friend H AbslHashValue(H state, const MyClass& value) {
    value.HashValue(absl::HashState::Create(&state));
    return std::move(state);
  }

 private:
  void HashValue(absl::HashState state) const;

  class MyClassImpl;
  std::unique_ptr<MyClassImpl> impl_;
};

// in .cc file
...
void MyClass::HashValue(absl::HashState state) const {
  absl::HashState::combine(std::move(state), impl_->a, impl_->b, impl_->c);
}
```
