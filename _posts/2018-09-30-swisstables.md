---
title: "Swiss Tables and <code>absl::Hash</code>"
layout: blog
sidenav: side-nav-blog.html
published: true
permalink: blog/20180930-swisstables
type: markdown
category: blog
excerpt_separator: <!--break-->
---

By [Matt Kulukundis](mailto:kfm@google.com) and
[Sam Benzaquen](mailto:sbenza@google.com))

We are extremely pleased to announce the availability of the new “Swiss Table” 
family of hashtables in Abseil and the `absl::Hash` hashing framework that 
allows easy extensibility for user defined types.

Last year at CppCon, We presented a [talk][cppcon-talk] on a new hashtable that
we were rolling out across Google’s codebase. When asked about its release 
date, we may have been a touch optimistic. But hopefully it will have been 
worth the wait. As an added bonus, this release also comes with an entirely new 
framework for hashing your types. As with all things of this size, this is the 
work of a great many people.

<!--break-->

Swiss Tables boast improvements to efficiency and provide C++11 codebases early
access to APIs from C++17 and C++20.

These hash tables live within the [Abseil `container` library][container-link].

### `absl::flat_hash_map` and `absl::flat_hash_set`

<img src="/img/flat_hash_map.svg" style="margin:5px;width:30%"
  alt="Flat Hash Map Memory Layout"/>

The "flat" Swiss tables should be your default choice. They store their 
`value_type` inside the container's main array to avoid memory indirections. 
Because they move data when they rehash, elements do not get pointer stability. 
If you require pointer stability or your values are large, consider using an
`absl::node_hash_map` or `absl::node_hash_set` (or an
`absl::flat_hash_map<Key, std::unique_ptr<Value>>`).

### `absl::node_hash_map` and `absl::node_hash_set`

<img src="/img/node_hash_map.svg" style="margin:5px;width:30%"
  alt="Node Hash Map Memory Layout"/>

The "node" Swiss tables allocate their `value_type` in nodes outside of the 
main array (like as in `std::unordered_map`). Because of the separate 
allocation, they provide pointer stability (the address of objects stored in 
the map does not change) for the stored data and empty slots only require 8 
bytes. Additionally, they can store things that are neither moveable nor 
copyable.

We generally recommend that you use
`absl::flat_hash_map<K, std::unique_ptr<V>>` instead of
`absl::node_hash_map<K, V>`.
	
## The `absl::Hash` hashing framework

The [`absl::Hash` library][hash-link] consists of two parts:

*   `absl::Hash<T>`, a concrete hash functor object, which you can use out of 
	the box
*   A generic hashing framework for specializing hashing behavior and making user-defined types hashable

This library is designed to be used as a replacement for 
[`std::hash`][std-hash] and the various other hash functors used in google3. It 
provides several advantages over them:

*   It can hash objects of almost any standard type, including `std::pair`, 
    `std::tuple`, and most standard containers
*   It can be extended to support user-defined types. Our goal is that if it 
    makes sense to hash an object of type `Foo`, then `absl::Hash<Foo>` will 
	just work. These extensions are easy to write and efficient to execute.

Importantly, the underlying hash algorithm can be changed without modifying
user code, which allows us to improve both it, and types which utilize 
`absl::Hash` over time. For example, we might wish to change the hashing 
algorithm within a container to improve performance and to defend against some
hash-flooding attacks.

The `absl::Hash` framework is the default hash implementation for the Swiss 
tables and does not need to be explicitly specified when working with that 
library.


[cppcon-talk]: https://www.youtube.com/watch?v=ncHmEUmJZf4&t=3s
[std-hash]: https://en.cppreference.com/w/cpp/utility/hash
[container-link]: https://github.com/abseil/abseil-cpp/tree/master/absl/container
[hash-link]: https://github.com/abseil/abseil-cpp/tree/master/absl/hash
