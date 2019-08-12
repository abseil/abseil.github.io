---
title: "B-tree Containers"
layout: about
sidenav: side-nav-design.html
type: markdown
---

# B-tree Containers

The Abseil `container` library includes b-tree containers that generally conform
to the STL sorted container (e.g. `std::map`) APIs, but are more efficient in
most cases. These containers are:

*   `absl::btree_set` (meant to replace usage of `std::set`)
*   `absl::btree_map` (meant to replace usage of `std::map`)
*   `absl::btree_multiset` (meant to replace usage of `std::multiset`)
*   `absl::btree_multimap` (meant to replace usage of `std::multimap`)

B-trees have a different implementation from STL `std::map` containers, which
require binary trees commonly implemented as [red-black trees][redblack_trees].
While a red-black tree is limited to single-element nodes, with precisely two
children, a B-tree may contain multiple values per node (M), with each node
having (M+1) children. Having more values and children per node is more cache
friendly because nodes are generally allocated separately so accessing
additional nodes often results in cache misses.

## Cache Friendliness

For search, insertion, and deletion, the number of nodes that need to be
accessed in a sorted tree is proportional to the height of the tree. Binary
trees have two children per node so the height for a balanced tree is
~log<sub>2</sub>(N), where N is the number of values in the tree. B-tree nodes
have more children (e.g., for `absl::btree_set<int32_t>`, nodes currently have
62 children) so the tree height for balanced B-trees is ~log<sub>M</sub>(N),
where M is the number of children. As a result, the height in a B-tree can be
lower than in a balanced binary tree of the same size by a factor of
~log<sub>2</sub>(M), which is ~6 for M=62.

For iteration, it is most cache efficient to store all values contiguously.
B-trees stores values contiguously in each node so it’s also generally more
efficient to iterate through a B-tree than a binary tree.

## Memory Overhead

B-trees also use significantly less memory per value in the tree because
overhead is per node, and there are fewer nodes per value in B-trees. There is
also an optimization in Abseil B-tree in which leaf nodes don’t store child
pointers. Since the vast majority of nodes are leaf nodes (due to the higher
branching factor due to more children per non-leaf node), this ends up saving a
significant amount of memory.

As an example, currently in 64-bit mode, the libstdc++ implementation of
`std::set<int32_t>` allocates 40 bytes per value inserted into the container.
`absl::btree_set<int32_t>` generally uses ~4.3 to ~5.1 bytes per value
(depending on usage).

## API Difference from STL Sorted Containers

When values are inserted or removed from a B-tree, nodes can be split or merged
and values can be moved within and between nodes (for the purpose of maintaining
tree balance). This means that when values are inserted or removed from a B-tree
container, pointers and iterators to other values in the B-tree can be
invalidated. Abseil B-trees therefore do not provide pointer stability or
iterator stability - this is in contrast to STL sorted containers that do
provide these guarantees.

## When to Use B-trees

B-trees are a good default choice for sorted containers, however, there are
cases in which the STL alternatives may be more appropriate.

* When `value_type` is large, fewer values can be stored per node so the
  benefits of B-tree are lessened.
* When `value_type` is expensive to move, B-tree may become more expensive than
  STL alternatives because B-tree needs to move values within and between nodes
  to maintain balance, whereas binary trees can just move pointers instead.
  `std::array<int32_t, 16>` is an example of a `value_type` for which STL sorted
  containers currently outperform B-trees.
* When pointer stability or iterator stability is required, B-trees aren’t a
  viable option (although usually code can be refactored to avoid these
  requirements).

[redblack_trees]: https://en.wikipedia.org/wiki/Red%E2%80%93black_tree
