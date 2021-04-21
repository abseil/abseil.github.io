---
title: "Abseil Containers"
layout: docs
sidenav: side-nav-cpp.html
type: markdown
---

# Abseil Containers

Abseil provides a number of containers as alternatives to STL containers. These
containers generally adhere to the properties of STL containers, though there
are often some associated API differences and/or implementation details which
differ from the standard library.

The Abseil containers are designed to be more efficient in the general case; in
some cases, however, the STL containers may be more efficient. Unlike some other
abstractions that Abseil provides, these containers should not be considered
drop-in replacements for their STL counterparts, as there are API and/or
contract differences between the two sets of containers. For example, the
Abseil containers often do not guarantee pointer stability after insertions or
deletions.

The Abseil `container` library defines the following sets of containers:

* B-tree ordered containers
* Swiss table unordered containers

See below for more information about each of these container types.

## B-tree Ordered Containers

The Abseil `container` library contains ordered containers generally
adhering to the STL container API contract, but implemented using (generally
more efficient) B-trees rather than binary trees (as used in `std::map` et al):

*   `absl::btree_map`
*   `absl::btree_set`
*   `absl::btree_multimap`
*   `absl::btree_multiset`

These ordered containers are designed to be more efficient replacements for
[`std::map`](https://en.cppreference.com/w/cpp/container/map)
and [`std::set`](https://en.cppreference.com/w/cpp/container/set) in most cases.
Specifically, they provide several advantages over the ordered `std::`
containers:

*   Provide lower memory overhead in most cases than their STL equivalents.
*   Are generally more cache friendly (and hence faster) than their STL
    equivalents.
*   Provide C++11 support for C++17 mechanisms such as `try_emplace()`.
*   Support heterogeneous lookup.

### Construction

The set of B-tree containers support the same overload set as
`std::map` for construction and assignment:

<!--{% raw %}-->
```c++
// Examples using btree_multimap and btree_multiset are equivalent

// Default constructor
// No allocation for the B-tree's elements is made.
absl::btree_set<std::string> set1;

absl::btree_map<int, std::string> map1;

// Initializer List constructor
absl::btree_set<std::string> set2 = {{"huey"}, {"dewey"}, {"louie"},};

absl::btree_map<int, std::string> map2 =
    {{1, "huey"}, {2, "dewey"}, {3, "louie"},};

// Copy constructor
absl::btree_set<std::string> set3(set2);

absl::btree_map<int, std::string> map3(map2);

// Copy assignment operator
// Hash functor and Comparator are copied as well
absl::btree_set<std::string> set4;
set4 = set3;

absl::btree_map<int, std::string> map4;
map4 = map3;

// Move constructor
// Move is guaranteed efficient
absl::btree_set<std::string> set5(std::move(set4));

absl::btree_map<int, std::string> map5(std::move(map4));

// Move assignment operator
// May be efficient if allocators are compatible
absl::btree_set<std::string> set6;
set6 = std::move(set5);

absl::btree_map<int, std::string> map6;
map6 = std::move(map5);

// Range constructor
std::vector<std::string> v = {"a", "b"};
absl::btree_set<std::string> set7(v.begin(), v.end());

std::vector<std::pair<int, std::string>> v = {{1, "a"}, {2, "b"}};
absl::btree_map<int, std::string> map7(v.begin(), v.end());
```
<!--{% endraw %}-->

## Hash Tables

The Abseil `container` library contains a number of useful hash tables generally
adhering to the STL container API contract:

*   `absl::flat_hash_map`
*   `absl::flat_hash_set`
*   `absl::node_hash_map`
*   `absl::node_hash_set`

Collectively, these hash tables are known as "Swiss tables" and are designed to
be replacements for
[`std::unordered_map`](https://en.cppreference.com/w/cpp/container/unordered_map)
and [`std::unordered_set`](https://en.cppreference.com/w/cpp/container/unordered_set)
They provide several advantages over the `std::unordered_*` containers:

*   Provides C++11 support for C++17 mechanisms such as `try_emplace()`.
*   Supports heterogeneous lookup.
*   Allows optimizations for `emplace({key, value})` to avoid allocating a pair
    in most common cases.
*   Supports a heterogeneous `std::initializer_list` to avoid extra copies for
    construction and insertion.
*   Guarantees an `O(1)` erase method by returning void instead of an iterator.

### Construction

The set of Swiss table containers support the same overload set as
`std::unordered_map` for construction and assignment:

<!--{% raw %}-->
```c++
// Examples using node_hash_set and node_hash_map are equivalent

// Default constructor
// No allocation for the table's elements is made.
absl::flat_hash_set<std::string> set1;

absl::flat_hash_map<int, std::string> map1;

// Initializer List constructor
absl::flat_hash_set<std::string> set2 = {{"huey"}, {"dewey"}, {"louie"},};

absl::flat_hash_map<int, std::string> map2 =
    {{1, "huey"}, {2, "dewey"}, {3, "louie"},};

// Copy constructor
absl::flat_hash_set<std::string> set3(set2);

absl::flat_hash_map<int, std::string> map3(map2);

// Copy assignment operator
// Hash functor and Comparator are copied as well
absl::flat_hash_set<std::string> set4;
set4 = set3;

absl::flat_hash_map<int, std::string> map4;
map4 = map3;

// Move constructor
// Move is guaranteed efficient
absl::flat_hash_set<std::string> set5(std::move(set4));

absl::flat_hash_map<int, std::string> map5(std::move(map4));

// Move assignment operator
// May be efficient if allocators are compatible
absl::flat_hash_set<std::string> set6;
set6 = std::move(set5);

absl::flat_hash_map<int, std::string> map6;
map6 = std::move(map5);

// Range constructor
std::vector<std::string> v = {"a", "b"};
absl::flat_hash_set<std::string> set7(v.begin(), v.end());

std::vector<std::pair<int, std::string>> v = {{1, "a"}, {2, "b"}};
absl::flat_hash_map<int, std::string> map7(v.begin(), v.end());
```
<!--{% endraw %}-->

### `absl::flat_hash_map` and `absl::flat_hash_set`

`absl::flat_hash_map` and `absl::flat_hash_set` are the recommended unordered
containers for general use. These are flat data structures, which store their
`value_type` directly in the slot array.

#### Guarantees

*   Keys and values are stored inline.
*   Iterators, references, and pointers to elements are invalidated on rehash.
*   Move operations do not invalidate iterators or pointers.

#### Memory Usage

<img src="images/flat-hash-map.svg" style="margin:5px;width:50%"
    alt="Flat Hash Map Memory Layout"/>

The container uses O(`(sizeof(std::pair<const K, V>) + 1) * bucket_count()`)
bytes. The *max load factor* is 87.5%, after which the table doubles in size
(making load factor go down by 2x). Thus `size()` is usually between
`0.4375*bucket_count()` and `0.875*bucket_count()`. For tables that have never
rehashed the load factor can be even lower, but these numbers are sufficient for
our estimates.

#### Recommendation

Use `absl::flat_hash_map` most of the time. If pointer stability of values (but
not keys) is needed, use `absl::flat_hash_map<Key, std::unique_ptr<Value>>`.

### `absl::node_hash_map` and `absl::node_hash_set`

These are near drop-in replacement for `std::unordered_map` and
`std::unordered_set`. They are useful:

*   When pointer stability[^pointer-stability] is required for both key and
    value.
*   For automatic migrations from `std::unordered_map`, `std::unordered_set`,
    `hash_map` or `hash_set` where it's difficult to figure out whether the code
    relies on pointer stability.

These are node-based data structures in the STL standard sense: each
`value_type` is allocated in a separate node and the main table contains
pointers to those nodes.

#### Guarantees

*   Nodes have stable addresses.
*   Iterators are invalidated on rehash.
*   Move operations do not invalidate iterators.

#### Memory Usage

<img src="images/node-hash-map.svg" style="margin:5px;width:50%"
    alt="Node Hash Map Memory Layout"/>

The slot array requires `(sizeof(void*) + 1) * bucket_count()` bytes and the
nodes themselves require `sizeof(value_type) * size()` bytes. Together, this is
O(`9*bucket_count + sizeof(std::pair<const K, V>)*size()`) on most platforms.

#### Recommendation

Prefer `absl::flat_hash_map` or `absl::flat_hash_set` in most new code (see
above).

Use `absl::node_hash_map` or `absl::node_hash_set` when pointer stability of
both keys and values is required (rare), or for code migrations from other
containers with this property. *Note:* Do not use popularity as a guide. You
will see the "node" containers used a lot, but only because it was safe to
migrate code to them from other containers.

### Construction and Usage

<!--{% raw %}-->
```cpp
absl::flat_hash_map<int, string> numbers =
    {{1, "one"}, {2, "two"}, {3, "three"}};
numbers.try_emplace(4, "four");

absl::flat_hash_map<string, std::unique_ptr<string>> strings;
strings.try_emplace("foo", absl::make_unique<string>("bar"));
```
<!--{% endraw %}-->

### Heterogeneous Lookup

Inserting into or looking up an element within an associative container requires
a key. In general, containers require the keys to be of a specific type, which
can lead to inefficiencies at call sites that need to convert between
near-equivalent types (such as `std::string` and `absl::string_view`).

<pre class="bad-code">
std::map&lt;std::string, int&gt; m = ...;
absl::string_view some_key = ...;
// Construct a temporary `std::string` to do the query.
// The allocation + copy + deallocation might dominate the find() call.
auto it = m.find(std::string(some_key));
</pre>

To avoid this unnecessary work, the Swiss tables provide heterogeneous lookup
for conversions to string types (allowing `absl::string_view` in the lookup, for
example), and for conversions to smart pointer types (`std::unique_ptr`,
`std::shared_ptr`), through the `absl::Hash` hashing framework. (The supporting
comparators are built into `absl::Hash`.)

```cpp
absl::flat_hash_map<std::string, int> m = ...;
absl::string_view some_key = ...;
// We can use string_view directly as the key search.
auto it = m.find(some_key);
```

### Iteration Order Instability

While `std::unordered_map` makes no guarantees about iteration order, many
implementations happen to have a deterministic order based on the keys and their
insert order. This is not true of `absl::flat_hash_map` and
`absl::node_hash_map`. Thus, converting from `std::unordered_map` to
`absl::flat_hash_map` can expose latent bugs where the code incorrectly depends
on iteration order.

A special case which can create a subtle bug is summing `float` values in an
unordered container. While mathematical sums do not depend on order, floating
point sums do, and it can be the case that a sum is deterministic with
`std::unordered_set` but non-deterministic with `absl::flat_hash_set`.

## Notes

[^pointer-stability]: "Pointer stability" means that a pointer to an element
    remains valid (is not invalidated) so long as the element
    is present, allowing code to cache pointers to elements
    even when the underlying container is mutated. Saying that
    a container has pointer stability is the same as saying
    that it doesn't move elements in memory; their addresses
    do not change. Pointer stability/invalidation is the same
    as reference stability/invalidation.
