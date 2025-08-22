---
title: "Performance Hints"
layout: fast
sidenav: side-nav-fast.html
type: markdown
---
<style>
  details {
    border: 1px solid #333;
    padding: .5rem;
    margin: .5rem;
  }
  summary {
    display: list-item;
  }
  .bad-code pre.prettyprint {
   background-color:#fbe9e7;
  }

  .new pre.prettyprint {
    background-color:#ebfaf8;
  }
</style>

[Jeff Dean](https://research.google/people/jeff/),
[Sanjay Ghemawat](https://research.google/people/sanjayghemawat/)

Original version: 2023/07/27, last updated: 2024/09/05

<style>
.g3doc-search {
  display: none;
}
.g3doc-page-links {
  display: none;
}
.toc > ul > li {
  font-size: 125%;
}
.toc > ul > li > ul > li {
  font-size: 80%;
}
.bad-code {
  background: #fbe9e7;
  position: relative;
}
.bad-code::before {
  content: "Old";
  position: absolute;
  right: 5px;
  top: 2px;
  alignment-baseline: top;
}
.new {
  background: #ebfaf8;
  position: relative;
}
.new::before {
  content: "New";
  position: absolute;
  right: 5px;
  top: 2px;
  alignment-baseline: top;
}

.bench {
  background: #efe;
  position: relative;
  margin-top: 1ex !important;
}
.bench::before {
  content: "Benchmark results";
  position: absolute;
  right: 5px;
  top: 2px;
  alignment-baseline: top;
}


/* Shrink space usage for diff regions */
details .g3doc-zippy-region .g3doc-clipboard-btn {
  display: none;
}
details .g3doc-zippy-region p {
  margin: 0;
  margin-top: 1ex;
}
details .g3doc-zippy-region pre {
  margin-top: 0;
  margin-bottom: 1ex;
  padding: 2px;
  font-size: 75%;
}

.example {
  margin: 0.5rem 0;
  padding: 0.5rem;
  padding-left: 1.125rem;
  border: 0.0625rem #dadce0 solid;
  border-radius: 0.25rem;
}
.example p {
  margin: 0;
}

/* Do not show edit buttons since this is generated code. */
.g3doc-edit-link { display: none; }
.g3doc-page-links-button { display: none; }
</style>

Over the years, we (Jeff & Sanjay) have done a fair bit of diving into
performance tuning of various pieces of code, and
improving the performance of our software has been important from the very earliest days of
Google, since it lets us do more for more users. We wrote this document as a way
of identifying some general principles and specific techniques that we use when
doing this sort of work, and tried to pick illustrative source code changes
(change lists, or CLs) that provide examples of the various approaches and
techniques. Most of the concrete suggestions below reference C++ types and CLs,
but the general principles apply to other languages. The document focuses on
general performance tuning in the context of a single binary, and does not cover
distributed systems or machine learning (ML) hardware performance tuning (huge
areas unto themselves). We hope others will find this useful.

*Many of the examples in the document have code fragments that demonstrate the
techniques (click the little triangles!).*
*Note that some of these code fragments mention various internal Google codebase abstractions. We have included these anyway if we felt like the examples were self-contained enough to be understandable to those unfamiliar with the details of those abstractions.*

## The importance of thinking about performance {#the-importance-of-thinking-about-performance}

Knuth is often quoted out of context as saying *premature optimization is the
root of all evil*. The
[full quote](https://dl.acm.org/doi/pdf/10.1145/356635.356640) reads: *"We
should forget about small efficiencies, say about 97% of the time: premature
optimization is the root of all evil. Yet we should not pass up our
opportunities in that critical 3%."* This document is about that critical
3%, and a more compelling quote, again
from Knuth, reads:

> The improvement in speed from Example 2 to Example 2a is only about 12%, and
> many people would pronounce that insignificant. The conventional wisdom shared
> by many of today's software engineers calls for ignoring efficiency in the
> small; but I believe this is simply an overreaction to the abuses they see
> being practiced by penny-wise-and-pound-foolish programmers, who can't debug
> or maintain their "optimized" programs. In established engineering disciplines
> a 12% improvement, easily obtained, is never considered marginal; and I
> believe the same viewpoint should prevail in software engineering. Of course I
> wouldn't bother making such optimizations on a one-shot job, but when it's a
> question of preparing quality programs, I don't want to restrict myself to
> tools that deny me such efficiencies.

Many people will say "let's write down the code in as simple a way as possible
and deal with performance later when we can profile". However, this approach is
often wrong:

1.  If you disregard all performance concerns when developing a large system,
    you will end up with a flat profile where there are no obvious hotspots
    because performance is lost all over the place. It will be difficult to
    figure out how to get started on performance improvements.
2.  If you are developing a library that will be used by other people, the
    people who will run into performance problems will be likely to be people
    who cannot easily make performance improvements (they will have to
    understand the details of code written by other people/teams, and have to
    negotiate with them about the importance of performance optimizations).
3.  It is harder to make significant changes to a system when it is in heavy
    use.
4.  It is also hard to tell if there are performance problems that can be solved
    easily and so we end up with potentially expensive solutions like
    over-replication or severe overprovisioning of a service to handle load
    problems.

Instead, we suggest that when writing code, try to choose the faster alternative
if it does not impact readability/complexity of the code significantly.

## Estimation

If you can develop an intuition for how much performance might matter in the
code you are writing, you can make a more informed decision (e.g., how much
extra complexity is warranted in the name of performance). Some tips on
estimating performance while you are writing code:

*   Is it test code? If so, you need to worry mostly about the asymptotic
    complexity of your algorithms and data structures. (Aside: development cycle
    time matters, so avoid writing tests that take a long time to run.)
*   Is it code specific to an application? If so, try to figure out how much
    performance matters for this piece of code. This is typically not very hard:
    just figuring out whether code is initialization/setup code vs. code that
    will end up on hot paths (e.g., processing every request in a service) is
    often sufficient
*   Is it library code that will be used by many applications? In this case it
    is hard to tell how sensitive it might become. This is where it becomes
    especially important to follow some of the simple techniques described in
    this document. For example, if you need to store a vector that usually has a
    small number of elements, use an absl::InlinedVector instead of std::vector.
    Such techniques are not very hard to follow and don't add any non-local
    complexity to the system. And if it turns out that the code you are writing
    does end up using significant resources, it will be higher performance from
    the start. And it will be easier to find the next thing to focus on when
    looking at a profile.

You can do a slightly deeper analysis when picking between options with
potentially different performance characteristics by relying on
[back of the envelope calculations](https://en.wikipedia.org/wiki/Back-of-the-envelope_calculation).
Such calculations can quickly give a very rough estimate of the performance of
different alternatives, and the results can be used to discard some of the
alternatives without having to implement them.

Here is how such an estimation might work:

1.  Estimate how many low-level operations of various kinds are required, e.g.,
    number of disk seeks, number of network round-trips, bytes transmitted etc.
2.  Multiply each kind of expensive operation with its rough cost, and add the
    results together.
3.  The preceding gives the *cost* of the system in terms of resource usage. If
    you are interested in latency, and if the system has any concurrency, some
    of the costs may overlap and you may have to do slightly more complicated
    analysis to estimate the latency.

The following table, which is an updated version of a table from a
[2007 talk at Stanford University](https://static.googleusercontent.com/media/research.google.com/en//people/jeff/stanford-295-talk.pdf)
(video of the 2007 talk no longer exists, but there is a
[video of a related 2011 Stanford talk that covers some of the same content](https://www.youtube.com/watch?v=modXC5IWTJI))
may be useful since it lists the types of operations to consider, and their
rough cost :

```
L1 cache reference                             0.5 ns
L2 cache reference                             3 ns
Branch mispredict                              5 ns
Mutex lock/unlock (uncontended)               15 ns
Main memory reference                         50 ns
Compress 1K bytes with Snappy              1,000 ns
Read 4KB from SSD                         20,000 ns
Round trip within same datacenter         50,000 ns
Read 1MB sequentially from memory         64,000 ns
Read 1MB over 100 Gbps network           100,000 ns
Read 1MB from SSD                      1,000,000 ns
Disk seek                              5,000,000 ns
Read 1 MB sequentially from disk      10,000,000 ns
Send packet CA->Netherlands->CA      150,000,000 ns
```

The preceding table contains rough costs for some basic low-level operations.
You may find it useful to also track estimated costs for higher-level operations
relevant to your system. E.g., you might want to know the rough cost of a point
read from your SQL database, the latency of interacting with a Cloud service, or
the time to render a simple HTML page. If you don’t know the relevant cost of
different operations, you can’t do decent back-of-the-envelope calculations!

### Example: Time to quicksort a billion 4 byte numbers

As a rough approximation, a good quicksort algorithm makes log(N) passes over an
array of size N. On each pass, the array contents will be streamed from memory
into the processor cache, and the partitition code will compare each element
once to a pivot element. Let's add up the dominant costs:

1.  Memory bandwidth: the array occupies 4 GB (4 bytes per number times a
    billion numbers). Let's assume ~16GB/s of memory bandwidth per core. That
    means each pass will take ~0.25s. N is ~2^30, so we will make ~30 passes, so
    the total cost of memory transfer will be ~7.5 seconds.
2.  Branch mispredictions: we will do a total of N*log(N) comparisons, i.e., ~30
    billion comparisons. Let's assume that half of them (i.e., 15 billion) are
    mispredicted. Multiplying by 5 ns per misprediction, we get a misprediction
    cost of 75 seconds. We assume for this analysis that correctly predicted
    branches are free.
3.  Adding up the previous numbers, we get an estimate of ~82.5 seconds.

If necessary, we could refine our analyis to account for processor caches. This
refinement is probably not needed since branch mispredictions are the dominant
cost according to the analysis above, but we include it here anyway as another
example. Let's assume we have a 32MB L3 cache, and that the cost of transferring
data from L3 cache to the processor is negligible. The L3 cache can hold 2^23
numbers, and therefore the last 22 passes can operate on the data resident in
the L3 cache (the 23rd last pass brings data into the L3 cache and the remaining
passes operate on that data.) That cuts down the memory transfer cost to 2.5
seconds (10 memory transfers of 4GB at 16GB/s) instead of 7.5 seconds (30 memory
transfers).

### Example: Time to generate a web page with 30 image thumbnails

Let's compare two potential designs where the original images are stored on
disk, and each image is approximately 1MB in size.

1.  Read the contents of the 30 images serially and generate a thumbnail for
    each one. Each read takes one seek + one transfer, which adds up to 5ms for
    the seek, and 10ms for the transfer, which adds up to 30 images times 15ms
    per image, i.e., 450ms.
2.  Read in parallel, assuming the images are spread evenly across K disks. The
    previous resource usage estimate still holds, but latency will drop by
    roughly a factor of K, ignoring variance (e.g, we will sometimes get unlucky
    and one disk will have more than 1/Kth of the images we are reading).
    Therefore if we are running on a distributed filesystem with hundreds of
    disks, the expected latency will drop to ~15ms.
3.  Let's consider a variant where all images are on a single SSD. This changes
    the sequential read performance to 20µs + 1ms per image, which adds up to
    ~30 ms overall.

## Measurement {#measurement}

The preceding section gives some tips about how to think about performance when
writing code without worrying too much about how to measure the performance
impact of your choices. However, before you actually start making improvements,
or run into a tradeoff involving various things like performance, simplicity,
etc. you will want to measure or estimate potential performance benefits. Being
able to measure things effectively is the number one tool you'll want to have in
your arsenal when doing performance-related work.

As an aside, it’s worth pointing out that profiling code that you’re unfamiliar
with can also be a good way of getting a general sense of the structure of the
codebase and how it operates. Examining the source code of heavily involved
routines in the dynamic call graph of a program can give you a high level sense
of “what happens” when running the code, which can then build your own
confidence in making performance-improving changes in slightly unfamiliar code.

### Profiling tools and tips {#profiling-tools-and-tips}

Many useful profiling tools are available. A useful tool to reach for first is
[pprof](https://github.com/google/pprof/blob/main/doc/README.md) since it gives
good high level performance information and is easy to use both locally and for
code running in production. Also try
[perf](https://perf.wiki.kernel.org/index.php/Main_Page) if you want more
detailed insight into performance.

Some tips for profiling:

*   Build production binaries with appropriate debugging information and
    optimization flags.
*   If you can, write a micro-benchmark that covers the code you are improving.
    Microbenchmarks improve turn-around time when making performance
    improvements, help verify the impact of performance improvements, and can
    help prevent future performance regressions. However microbenchmarks can
    have [pitfalls][fast39] that make them non-representative of full system
    performance. Useful libraries for writing micro-benchmarks:
    [C++][cpp benchmarks] [Go][go benchmarks] [Java][jmh].
*   Use a benchmark library to [emit performance counter readings][fast53] both
    for better precision, and to get more insight into program behavior.
*   Lock contention can often artificially lower CPU usage. Some mutex
    implementations provide support for profiling lock contention.
*   Use [ML profilers][xprof] for machine learning performance
    work.

### What to do when profiles are flat {#what-to-do-when-profiles-are-flat}

You will often run into situations where your CPU profile is flat (there is no
obvious big contributor to slowness). This can often happen when all low-hanging
fruit has been picked. Here are some tips to consider if you find yourself in
this situation:

*   Don't discount the value of many small optimizations! Making twenty separate
    1% improvements in some subsystem is often eminently possible and
    collectively mean a pretty sizable improvement (work of this flavor often
    relies on having stable and high quality microbenchmarks). Some examples of
    these sorts of changes are in the
    [changes that demonstrate multiple techniques](#cls-that-demonstrate-multiple-techniques)
    section.
*   Find loops closer to the top of call stacks (flame graph view of a CPU
    profile can be helpful here). Potentially, the loop or the code it calls
    could be restructured to be more efficient. Some code that initially built a
    complicated graph structure incrementally by looping over nodes and edges of
    the input was changed to build the graph structure in one shot by passing it
    the entire input. This removed a bunch of internal checks that were
    happening per edge in the initial code.
*   Take a step back and look for structural changes higher up in the call
    stacks instead of concentrating on micro-optimizations. The techniques
    listed under [algorithmic improvements](#algorithmic-improvements) can be
    useful when doing this.
*   Look for overly general code. Replace it with a customized or lower-level
    implementation. E.g., if an application is repeatedly using a regular
    expression match where a simple prefix match would suffice, consider
    dropping the use of the regular expression.
*   Attempt to reduce the number of allocations:
    [get an allocation profile][profile sources], and pick away at the highest
    contributor to the number of allocations. This will have two effects: (1) It
    will provide a direct reduction of the amount of time spent in the allocator
    (and garbage collector for GC-ed languages) (2) There will often be a
    reduction in cache misses since in a long running program using tcmalloc,
    every allocation tends to go to a different cache line.
*   Gather other types of profiles, specially ones based on hardware performance
    counters. Such profiles may point out functions that are encountering a high
    cache miss rate. Techniques described in the
    [profiling tools and tips](#profiling-tools-and-tips) section can be
    helpful.

## API considerations {#api-considerations}

Some of the techniques suggested below require changing data structures and
function signatures, which may be disruptive to callers. Try to organize code so
that the suggested performance improvements can be made inside an encapsulation
boundary without affecting public interfaces. This will be easier if your
[modules are deep](https://web.stanford.edu/~ouster/cgi-bin/book.php)
(significant functionality accessed via a narrow interface).

Widely used APIs come under heavy pressure to add
features.
Be careful when adding new features since these will constrain future
implementations and increase cost unnecessarily for users who don't need the new
features. E.g., many C++ standard library containers promise iterator stability,
which in typical implementations increases the number of allocations
significantly, even though many users do not need pointer stability.

Some specific techniques are listed below. Consider carefully the performance
benefits vs. any API usability issues introduced by such changes.

### Bulk APIs

Provide bulk ops to reduce expensive API boundary crossings or to take advantage
of algorithmic improvements.

<details markdown="1">
<summary>
Added bulk MemoryManager::LookupMany interface.
</summary>

In addition to adding a bulk interface, this also simplified the signature for
the new bulk variant: it turns out clients only needed to know if all the keys
were found, so we can return a bool rather than a Status object.

memory_manager.h

{: .bad-code}
```c++
class MemoryManager {
 public:
  ...
  util::StatusOr<LiveTensor> Lookup(const TensorIdProto& id);
```

{: .new}
```c++
class MemoryManager {
 public:
  ...
  util::StatusOr<LiveTensor> Lookup(const TensorIdProto& id);

  // Lookup the identified tensors
  struct LookupKey {
    ClientHandle client;
    uint64 local_id;
  };
  bool LookupMany(absl::Span<const LookupKey> keys,
                  absl::Span<tensorflow::Tensor> tensors);
```

</details>

<details markdown="1">
<summary>
Added bulk ObjectStore::DeleteRefs API to amortize
locking overhead.
</summary>

object_store.h

{: .bad-code}
```c++
template <typename T>
class ObjectStore {
 public:
  ...
  absl::Status DeleteRef(Ref);
```

{: .new}
```c++
template <typename T>
class ObjectStore {
 public:
  ...
  absl::Status DeleteRef(Ref);

  // Delete many references.  For each ref, if no other Refs point to the same
  // object, the object will be deleted.  Returns non-OK on any error.
  absl::Status DeleteRefs(absl::Span<const Ref> refs);
  ...
template <typename T>
absl::Status ObjectStore<T>::DeleteRefs(absl::Span<const Ref> refs) {
  util::Status result;
  absl::MutexLock l(&mu_);
  for (auto ref : refs) {
    result.Update(DeleteRefLocked(ref));
  }
  return result;
}
```

memory_tracking.cc

{: .bad-code}
```c++
void HandleBatch(int, const plaque::Batch& input) override {
  for (const auto& t : input) {
    auto in = In(t);
    PLAQUE_OP_ASSIGN_OR_RETURN(const auto& handles, in.handles());
    for (const auto handle : handles.value->handles()) {
      PLAQUE_OP_RETURN_IF_ERROR(in_buffer_store_
                                    ? bstore_->DeleteRef(handle)
                                    : tstore_->DeleteRef(handle));
    }
  }
}
```

{: .new}
```c++
void HandleBatch(int, const plaque::Batch& input) override {
  for (const auto& t : input) {
    auto in = In(t);
    PLAQUE_OP_ASSIGN_OR_RETURN(const auto& handles, in.handles());
    if (in_buffer_store_) {
      PLAQUE_OP_RETURN_IF_ERROR(
          bstore_->DeleteRefs(handles.value->handles()));
    } else {
      PLAQUE_OP_RETURN_IF_ERROR(
          tstore_->DeleteRefs(handles.value->handles()));
    }
  }
}
```

</details>

<details markdown="1">
<summary>
<a href="https://en.wikipedia.org/wiki/Heapsort#Variations">Floyd's
heap construction</a>.
</summary>

Bulk initialization of a heap can be done in O(N) time, whereas adding one
element at a time and updating the heap property after each addition requires
O(N lg(N)) time.

</details>

Sometimes it is hard to change callers to use a new bulk API directly. In that
case it might be beneficial to use a bulk API internally and cache the results
for use in future non-bulk API calls:

<details markdown="1">
<summary>
Cache block decode results for use in future calls.
</summary>

Each lookup needs to decode a whole block of K entries. Store the decoded
entries in a cache and consult the cache on future lookups.

lexicon.cc

{: .bad-code}
```c++
void GetTokenString(int pos, std::string* out) const {
  ...
  absl::FixedArray<LexiconEntry, 32> entries(pos + 1);

  // Decode all lexicon entries up to and including pos.
  for (int i = 0; i <= pos; ++i) {
    p = util::coding::TwoValuesVarint::Decode32(p, &entries[i].remaining,
                                                &entries[i].shared);
    entries[i].remaining_str = p;
    p += entries[i].remaining;  // remaining bytes trail each entry.
  }
```

{: .new}
```c++
mutable std::vector<absl::InlinedVector<std::string, 16>> cache_;
...
void GetTokenString(int pos, std::string* out) const {
  ...
  DCHECK_LT(skentry, cache_.size());
  if (!cache_[skentry].empty()) {
    *out = cache_[skentry][pos];
    return;
  }
  ...
  // Init cache.
  ...
  const char* prev = p;
  for (int i = 0; i < block_sz; ++i) {
    uint32 shared, remaining;
    p = TwoValuesVarint::Decode32(p, &remaining, &shared);
    auto& cur = cache_[skentry].emplace_back();
    gtl::STLStringResizeUninitialized(&cur, remaining + shared);

    std::memcpy(cur.data(), prev, shared);
    std::memcpy(cur.data() + shared, p, remaining);
    prev = cur.data();
    p += remaining;
  }
  *out = cache_[skentry][pos];
```

</details>

### View types

Prefer view types (e.g., `std::string_view`, `std::Span<T>`,
`absl::FunctionRef<R(Args...)>`) for function arguments (unless ownership of the
data is being transferred). These types reduce copying, and allow callers to
pick their own container types (e.g., one caller might use `std::vector` whereas
another one uses `absl::InlinedVector`).

### Pre-allocated/pre-computed arguments

For frequently called routines, sometimes it is useful to allow higher-level
callers to pass in a data structure that they own or information that the called
routine needs that the client already has. This can avoid the low-level routine
being forced to allocate its own temporary data structure or recompute
already-available information.

<details markdown="1">
<summary>
Added RPC_Stats::RecordRPC variant allowing client to pass
in already available WallTime value.
</summary>

rpc-stats.h

{: .bad-code}
```c++
static void RecordRPC(const Name &name, const RPC_Stats_Measurement& m);
```

{: .new}
```c++
static void RecordRPC(const Name &name, const RPC_Stats_Measurement& m,
                      WallTime now);
```

clientchannel.cc

{: .bad-code}
```c++
const WallTime now = WallTime_Now();
...
RPC_Stats::RecordRPC(stats_name, m);
```

{: .new}
```c++
const WallTime now = WallTime_Now();
...
RPC_Stats::RecordRPC(stats_name, m, now);
```

</details>

### Thread-compatible vs. Thread-safe types {#thread-compatible-vs-thread-safe-types}

A type may be either thread-compatible (synchronized externally) or thread-safe
(synchronized internally). Most generally used types should be
thread-compatible. This way callers who do not need thread-safety don't pay for
it.

<details markdown="1">
<summary>
Make a class thread-compatible since callers are already
synchronized.
</summary>

hitless-transfer-phase.cc

{: .bad-code}
```c++
TransferPhase HitlessTransferPhase::get() const {
  static CallsiteMetrics cm("HitlessTransferPhase::get");
  MonitoredMutexLock l(&cm, &mutex_);
  return phase_;
}
```

{: .new}
```c++
TransferPhase HitlessTransferPhase::get() const { return phase_; }
```

hitless-transfer-phase.cc

{: .bad-code}
```c++
bool HitlessTransferPhase::AllowAllocate() const {
  static CallsiteMetrics cm("HitlessTransferPhase::AllowAllocate");
  MonitoredMutexLock l(&cm, &mutex_);
  return phase_ == TransferPhase::kNormal || phase_ == TransferPhase::kBrownout;
}
```

{: .new}
```c++
bool HitlessTransferPhase::AllowAllocate() const {
  return phase_ == TransferPhase::kNormal || phase_ == TransferPhase::kBrownout;
}
```

</details>

However if the typical use of a type needs synchronization, prefer to move the
synchronization inside the type. This allows the synchronization mechanism to be
tweaked as necessary to improve performance (e.g., sharding to reduce
contention) without affecting callers.

## Algorithmic improvements {#algorithmic-improvements}

The most critical opportunities for performance improvements come from
algorithmic improvements, e.g., turning an O(N²) algorithm to O(N lg(N)) or
O(N), avoiding potentially exponential behavior, etc. These opportunities are
rare in stable code, but are worth paying attention to when writing new code. A
few examples that show such improvements to pre-existing code:

<details markdown="1">
<summary>
Add nodes to cycle detection structure in reverse
post-order.
</summary>

We were previously adding graph nodes and edges one at a time to a
cycle-detection data structure, which required expensive work per edge. We now
add the entire graph in reverse post-order, which makes cycle-detection trivial.

graphcycles.h

{: .bad-code}
```c++
class GraphCycles : public util_graph::Graph {
 public:
  GraphCycles();
  ~GraphCycles() override;

  using Node = util_graph::Node;
```

{: .new}
```c++
class GraphCycles : public util_graph::Graph {
 public:
  GraphCycles();
  ~GraphCycles() override;

  using Node = util_graph::Node;

  // InitFrom adds all the nodes and edges from src, returning true if
  // successful, false if a cycle is encountered.
  // REQUIRES: no nodes and edges have been added to GraphCycles yet.
  bool InitFrom(const util_graph::Graph& src);
```

graphcycles.cc

{: .new}
```c++
bool GraphCycles::InitFrom(const util_graph::Graph& src) {
  ...
  // Assign ranks in topological order so we don't need any reordering during
  // initialization. For an acyclic graph, DFS leaves nodes in reverse
  // topological order, so we assign decreasing ranks to nodes as we leave them.
  Rank last_rank = n;
  auto leave = [&](util_graph::Node node) {
    DCHECK(r->rank[node] == kMissingNodeRank);
    NodeInfo* nn = &r->nodes[node];
    nn->in = kNil;
    nn->out = kNil;
    r->rank[node] = --last_rank;
  };
  util_graph::DFSAll(src, std::nullopt, leave);

  // Add all the edges (detect cycles as we go).
  bool have_cycle = false;
  util_graph::PerEdge(src, [&](util_graph::Edge e) {
    DCHECK_NE(r->rank[e.src], kMissingNodeRank);
    DCHECK_NE(r->rank[e.dst], kMissingNodeRank);
    if (r->rank[e.src] >= r->rank[e.dst]) {
      have_cycle = true;
    } else if (!HasEdge(e.src, e.dst)) {
      EdgeListAddNode(r, &r->nodes[e.src].out, e.dst);
      EdgeListAddNode(r, &r->nodes[e.dst].in, e.src);
    }
  });
  if (have_cycle) {
    return false;
  } else {
    DCHECK(CheckInvariants());
    return true;
  }
}
```

graph_partitioner.cc

{: .bad-code}
```c++
absl::Status MergeGraph::Init() {
  const Graph& graph = *compiler_->graph();
  clusters_.resize(graph.NodeLimit());
  graph.PerNode([&](Node node) {
    graph_->AddNode(node);
    NodeList* n = new NodeList;
    n->push_back(node);
    clusters_[node] = n;
  });
  absl::Status s;
  PerEdge(graph, [&](Edge e) {
    if (!s.ok()) return;
    if (graph_->HasEdge(e.src, e.dst)) return;  // already added
    if (!graph_->InsertEdge(e.src, e.dst)) {
      s = absl::InvalidArgumentError("cycle in the original graph");
    }
  });
  return s;
}
```

{: .new}
```c++
absl::Status MergeGraph::Init() {
  const Graph& graph = *compiler_->graph();
  if (!graph_->InitFrom(graph)) {
    return absl::InvalidArgumentError("cycle in the original graph");
  }
  clusters_.resize(graph.NodeLimit());
  graph.PerNode([&](Node node) {
    NodeList* n = new NodeList;
    n->push_back(node);
    clusters_[node] = n;
  });
  return absl::OkStatus();
}
```

</details>

<details markdown="1">
<summary>
Replace the deadlock detection system built into a mutex
implementation with a better algorithm.
</summary>

Replaced deadlock detection algorithm by one that is ~50x as fast and scales to
millions of mutexes without problem (the old algorithm relied on a 2K limit to
avoid a performance cliff). The new code is based on the following paper: A
dynamic topological sort algorithm for directed acyclic graphs David J. Pearce,
Paul H. J. Kelly Journal of Experimental Algorithmics (JEA) JEA Homepage archive
Volume 11, 2006, Article No. 1.7

The new algorithm takes O(|V|+|E|) space (instead of the O(|V|^2) bits needed by
the older algorithm). Lock-acquisition order graphs are very sparse, so this is
much less space. The algorithm is also quite simple: the core of it is ~100
lines of C++. Since the code now scales to much larger number of Mutexes, we
were able to relax an artificial 2K limit, which uncovered a number of latent
deadlocks in real programs.

Benchmark results: these were run in DEBUG mode since deadlock detection is
mainly enabled in debug mode. The benchmark argument (/2k etc.) is the number of
tracked nodes. At the default 2k limit of the old algorithm, the new algorithm
takes only 0.5 microseconds per InsertEdge compared to 22 microseconds for the
old algorithm. The new algorithm also easily scales to much larger graphs
without problems whereas the old algorithm keels over quickly.

{: .bad-code}
```
DEBUG: Benchmark            Time(ns)    CPU(ns) Iterations
----------------------------------------------------------
DEBUG: BM_StressTest/2k        23553      23566      29086
DEBUG: BM_StressTest/4k        45879      45909      15287
DEBUG: BM_StressTest/16k      776938     777472        817
```

{: .new}
```
DEBUG: BM_StressTest/2k          392        393   10485760
DEBUG: BM_StressTest/4k          392        393   10485760
DEBUG: BM_StressTest/32k         407        407   10485760
DEBUG: BM_StressTest/256k        456        456   10485760
DEBUG: BM_StressTest/1M          534        534   10485760
```

</details>

<details markdown="1">
<summary>
Replace an IntervalMap (with O(lg N) lookups) with a hash
table (O(1) lookups).
</summary>

The initial code was using IntervalMap because it seemed like the right data
structure to support coalescing of adjacent blocks, but a hash table suffices
since the adjacent block can be found by a hash table lookup. This (plus other
changes in the CL) improve the performance of tpu::BestFitAllocator by ~4X.

best_fit_allocator.h

{: .bad-code}
```c++
using Block = gtl::IntervalMap<int64, BlockState>::Entry;
...
// Map of pairs (address range, BlockState) with one entry for each allocation
// covering the range [0, allocatable_range_end_).  Adjacent kFree and
// kReserved blocks are coalesced. Adjacent kAllocated blocks are not
// coalesced.
gtl::IntervalMap<int64, BlockState> block_list_;

// Set of all free blocks sorted according to the allocation policy. Adjacent
// free blocks are coalesced.
std::set<Block, BlockSelector> free_list_;
```

{: .new}
```c++
// A faster hash function for offsets in the BlockTable
struct OffsetHash {
  ABSL_ATTRIBUTE_ALWAYS_INLINE size_t operator()(int64 value) const {
    uint64 m = value;
    m *= uint64_t{0x9ddfea08eb382d69};
    return static_cast<uint64_t>(m ^ (m >> 32));
  }
};

// Hash table maps from block start address to block info.
// We include the length of the previous block in this info so we
// can find the preceding block to coalesce with.
struct HashTableEntry {
  BlockState state;
  int64 my_length;
  int64 prev_length;  // Zero if there is no previous block.
};
using BlockTable = absl::flat_hash_map<int64, HashTableEntry, OffsetHash>;
```

</details>

<details markdown="1">
<summary>
Replace sorted-list intersection (O(N log N)) with hash
table lookups (O(N)).
</summary>

Old code to detect whether or not two nodes share a common source would get the
sources for each node in sorted order and then do a sorted intersection. The new
code places the sources for one node in a hash-table and then iterates over the
other node's sources checking the hash-table.

{: .bench}
```
name             old time/op  new time/op  delta
BM_CompileLarge   28.5s ± 2%   22.4s ± 2%  -21.61%  (p=0.008 n=5+5)
```

</details>

<details markdown="1">
<summary>
Implement good hash function so that things are O(1)
instead of O(N).
</summary>

location.h

{: .bad-code}
```c++
// Hasher for Location objects.
struct LocationHash {
  size_t operator()(const Location* key) const {
    return key != nullptr ? util_hash::Hash(key->address()) : 0;
  }
};
```

{: .new}
```c++
size_t HashLocation(const Location& loc);
...
struct LocationHash {
  size_t operator()(const Location* key) const {
    return key != nullptr ? HashLocation(*key) : 0;
  }
};
```

location.cc

{: .new}
```c++
size_t HashLocation(const Location& loc) {
  util_hash::MurmurCat m;

  // Encode some simpler features into a single value.
  m.AppendAligned((loc.dynamic() ? 1 : 0)                    //
                  | (loc.append_shard_to_address() ? 2 : 0)  //
                  | (loc.is_any() ? 4 : 0)                   //
                  | (!loc.any_of().empty() ? 8 : 0)          //
                  | (loc.has_shardmap() ? 16 : 0)            //
                  | (loc.has_sharding() ? 32 : 0));

  if (loc.has_shardmap()) {
    m.AppendAligned(loc.shardmap().output() |
                    static_cast<uint64_t>(loc.shardmap().stmt()) << 20);
  }
  if (loc.has_sharding()) {
    uint64_t num = 0;
    switch (loc.sharding().type_case()) {
      case Sharding::kModShard:
        num = loc.sharding().mod_shard();
        break;
      case Sharding::kRangeSplit:
        num = loc.sharding().range_split();
        break;
      case Sharding::kNumShards:
        num = loc.sharding().num_shards();
        break;
      default:
        num = 0;
        break;
    }
    m.AppendAligned(static_cast<uint64_t>(loc.sharding().type_case()) |
                    (num << 3));
  }

  auto add_string = [&m](absl::string_view s) {
    if (!s.empty()) {
      m.Append(s.data(), s.size());
    }
  };

  add_string(loc.address());
  add_string(loc.lb_policy());

  // We do not include any_of since it is complicated to compute a hash
  // value that is not sensitive to order and duplication.
  return m.GetHash();
}
```

</details>

## Better memory representation {#better-memory-representation}

Careful consideration of memory footprint and cache footprint of important data
structures can often yield big savings. The data structures below focus on
supporting common operations by touching fewer cache lines. Care taken here can
(a) avoid expensive cache misses (b) reduce memory bus traffic, which speeds up
both the program in question and anything else running on the same machine. They
rely on some common techniques you may find useful when designing your own data
structures.

### Compact data structures

Use compact representations for data that will be accessed often or that
comprises a large portion of the application's memory usage. A compact
representation can significantly reduce memory usage and improve performance by
touching fewer cache lines and reducing memory bus bandwidth usage. However,
watch out for [cache-line contention](#reduce-false-sharing).

### Memory layout {#memory-layout}

Carefully consider the memory layout of types that have a large memory or cache
footprint.

*   Reorder fields to reduce padding between fields with different alignment
    requirements
    (see [class layout discussion](https://stackoverflow.com/questions/9989164/optimizing-memory-layout-of-class-instances-in-c)).
*   Use smaller numeric types where the stored data will fit in the smaller
    type.
*   Enum values sometimes take up a whole word unless you're careful. Consider
    using a smaller representation (e.g., use `enum class OpType : uint8_t { ...
    }` instead of `enum class OpType { ... }`).
*   Order fields so that fields that are frequently accessed together are closer
    to each other – this will reduce the number of cache lines touched on common
    operations.
*   Place hot read-only fields away from hot mutable fields so that writes to
    the mutable fields do not cause the read-only fields to be evicted from
    nearby caches.
*   Move cold data so it does not live next to hot data, either by placing the
    cold data at the end of the struct, or behind a level of indirection, or in
    a separate array.
*   Consider packing things into fewer bytes by using bit and byte-level
    encoding. This can be complicated, so only do this when the data under
    question is encapsulated inside a well-tested module, and the overall
    reduction of memory usage is significant. Furthermore, watch out for side
    effects like under-alignment of frequently used data, or more expensive code
    for accessing packed representations. Validate such changes using
    benchmarks.

### Indices instead of pointers {#indices-instead-of-pointers}

On modern 64-bit machines, pointers take up 64 bits. If you have a pointer-rich
data structure, you can easily chew up lots of memory with indirections of T\*.
Instead, consider using integer indices into an array T[] or other data
structure. Not only will the references be smaller (if the number of indices is
small enough to fit in 32 or fewer bits), but the storage for all the T[]
elements will be contiguous, often leading to better cache locality.

### Batched storage

Avoid data structures that allocate a separate object per stored element (e.g.,
`std::map`, `std::unordered_map` in C++). Instead, consider types that use
chunked or flat representations to store multiple elements in close proximity in
memory (e.g., `std::vector`, `absl::flat_hash_{map,set}` in C++). Such types
tend to have much better cache behavior. Furthermore, they encounter less
allocator overhead.

One useful technique is to partition elements into chunks where each chunk can
hold a fixed number of elements. This technique can reduce the cache footprint
of a data structure significantly while preserving good asymptotic behavior.

For some data structures, a single chunk suffices to hold all elements (e.g.,
strings and vectors). Other types (e.g., `absl::flat_hash_map`) also use this
technique.

### Inlined storage {#inlined-storage}

Some container types are optimized for storing a small number of elements. These
types provide space for a small number of elements at the top level and
completely avoid allocations when the number of elements is small. This can be
very helpful when instances of such types are constructed often (e.g., as stack
variables in frequently executed code), or if many instances are live at the
same time. If a container will typically contain a small number of elements
consider using one of the inlined storage types, e.g., InlinedVector.

Caveat: if `sizeof(T)` is large, inlined storage containers may not be the best
choice since the inlined backing store will be large.

### Unnecessarily nested maps

Sometimes a nested map data structure can be replaced with a single-level map
with a compound key. This can reduce the cost of lookups and insertions
significantly.

<details markdown="1">
<summary>
Reduce allocations and improve cache footprint by
converting btree&lt;a,btree&lt;b,c>> to btree&lt;pair&lt;a,b>,c>.
</summary>

graph_splitter.cc

{: .bad-code}
```c++
absl::btree_map<std::string, absl::btree_map<std::string, OpDef>> ops;
```

{: .new}
```c++
// The btree maps from {package_name, op_name} to its const Opdef*.
absl::btree_map<std::pair<absl::string_view, absl::string_view>,
                const OpDef*>
    ops;
```

</details>

Caveat: if the first map key is big, it might be better to stick with nested
maps:

<details markdown="1">
<summary>
Switch to a nested map leads to 76% performance
improvement in microbenchmark.
</summary>

We previously had a single-level hash table where the key consisted of a
(string) path and some other numeric sub-keys. Each path occurred in
approximately 1000 keys on average. We split the hash table into two levels
where the first level was keyed by the path and each second level hash table
kept just the sub-key to data mapping for a particular path. This reduced the
memory usage for storing paths by a factor of 1000, and also sped up accesses
</details>

### Arenas {#arenas}

Arenas can help reduce memory allocation cost, but they also have the benefit of
packing together independently allocated items next to each other, typically in
fewer cache lines, and eliminating most destruction costs. They are likely most
effective for complex data structures with many sub-objects. Consider providing
an appropriate initial size for the arena since that can help reduce
allocations.

Caveat: it is easy to misuse arenas by putting too many short-lived objects in a
long-lived arena, which can unnecessarily bloat memory footprint.

### Arrays instead of maps

If the domain of a map can be represented by a small integer or is an enum, or
if the map will have very few elements, the map can sometimes be replaced by an
array or a vector of some form.

<details markdown="1">
<summary>
Use an array instead of flat_map.
</summary>

rtp_controller.h

{: .bad-code}
```c++
const gtl::flat_map<int, int> payload_type_to_clock_frequency_;
```

{: .new}
```c++
// A map (implemented as a simple array) indexed by payload_type to clock freq
// for that paylaod type (or 0)
struct PayloadTypeToClockRateMap {
  int map[128];
};
...
const PayloadTypeToClockRateMap payload_type_to_clock_frequency_;
```

</details>

### Bit vectors instead of sets

If the domain of a set can be represented by a small integer, the set can be
replaced with a bit vector (InlinedBitVector is often a good choice). Set
operations can also be nicely efficient on these representations using bitwise
boolean operations (OR for union, AND for intersection, etc.).

<details markdown="1">
<summary>
Spanner placement system. Replace
dense_hash_set&lt;ZoneId> with a bit-vector with one bit per zone.
</summary>

zone_set.h

{: .bad-code}
```c++
class ZoneSet: public dense_hash_set<ZoneId> {
 public:
  ...
  bool Contains(ZoneId zone) const {
    return count(zone) > 0;
  }
```

{: .new}
```c++
class ZoneSet {
  ...
  // Returns true iff "zone" is contained in the set
  bool ContainsZone(ZoneId zone) const {
    return zone < b_.size() && b_.get_bit(zone);
  }
  ...
 private:
  int size_;          // Number of zones inserted
  util::bitmap::InlinedBitVector<256> b_;
```

Benchmark results:

{: .bench}
```
CPU: AMD Opteron (4 cores) dL1:64KB dL2:1024KB
Benchmark                          Base (ns)  New (ns) Improvement
------------------------------------------------------------------
BM_Evaluate/1                            960       676    +29.6%
BM_Evaluate/2                           1661      1138    +31.5%
BM_Evaluate/3                           2305      1640    +28.9%
BM_Evaluate/4                           3053      2135    +30.1%
BM_Evaluate/5                           3780      2665    +29.5%
BM_Evaluate/10                          7819      5739    +26.6%
BM_Evaluate/20                         17922     12338    +31.2%
BM_Evaluate/40                         36836     26430    +28.2%
```

</details>

<details markdown="1">
<summary>
Use bit matrix to keep track of reachability properties
between operands instead of hash table.
</summary>

hlo_computation.h

{: .bad-code}
```c++
using TransitiveOperandMap =
    std::unordered_map<const HloInstruction*,
                       std::unordered_set<const HloInstruction*>>;
```

{: .new}
```c++
class HloComputation::ReachabilityMap {
  ...
  // dense id assignment from HloInstruction* to number
  tensorflow::gtl::FlatMap<const HloInstruction*, int> ids_;
  // matrix_(a,b) is true iff b is reachable from a
  tensorflow::core::Bitmap matrix_;
};
```

</details>

## Reduce allocations {#reduce-allocations}

Memory allocation adds costs:

1.  It increases the time spent in the allocator.
2.  Newly-allocated objects may require expensive initialization and sometimes
    corresponding expensive destruction when no longer needed.
3.  Every allocation tends to be on a new cache line and therefore data spread
    across many independent allocations will have a larger cache footprint than
    data spread across fewer allocations.

Garbage-collection runtimes sometimes obviate issue #3 by placing consecutive
allocations sequentially in memory.

### Avoid unnecessary allocations {#avoid-unnecessary-allocations}

<details markdown="1">
<summary>
Reducing allocations increases benchmark throughput by
21%.
</summary>

memory_manager.cc

{: .bad-code}
```c++
LiveTensor::LiveTensor(tf::Tensor t, std::shared_ptr<const DeviceInfo> dinfo,
                       bool is_batched)
    : tensor(std::move(t)),
      device_info(dinfo ? std::move(dinfo) : std::make_shared<DeviceInfo>()),
      is_batched(is_batched) {
```

{: .new}
```c++
static const std::shared_ptr<DeviceInfo>& empty_device_info() {
  static std::shared_ptr<DeviceInfo>* result =
      new std::shared_ptr<DeviceInfo>(new DeviceInfo);
  return *result;
}

LiveTensor::LiveTensor(tf::Tensor t, std::shared_ptr<const DeviceInfo> dinfo,
                       bool is_batched)
    : tensor(std::move(t)), is_batched(is_batched) {
  if (dinfo) {
    device_info = std::move(dinfo);
  } else {
    device_info = empty_device_info();
  }
```

</details>

<details markdown="1">
<summary>
Use statically-allocated zero vector when possible rather
than allocating a vector and filling it with zeroes.
</summary>

embedding_executor_8bit.cc

{: .bad-code}
```c++
// The actual implementation of the EmbeddingLookUpT using template parameters
// instead of object members to improve the performance.
template <bool Mean, bool SymmetricInputRange>
static tensorflow::Status EmbeddingLookUpT(...) {
    ...
  std::unique_ptr<tensorflow::quint8[]> zero_data(
      new tensorflow::quint8[max_embedding_width]);
  memset(zero_data.get(), 0, sizeof(tensorflow::quint8) * max_embedding_width);
```

{: .new}
```c++
// A size large enough to handle most embedding widths
static const int kTypicalMaxEmbedding = 256;
static tensorflow::quint8 static_zero_data[kTypicalMaxEmbedding];  // All zeroes
...
// The actual implementation of the EmbeddingLookUpT using template parameters
// instead of object members to improve the performance.
template <bool Mean, bool SymmetricInputRange>
static tensorflow::Status EmbeddingLookUpT(...) {
    ...
  std::unique_ptr<tensorflow::quint8[]> zero_data_backing(nullptr);

  // Get a pointer to a memory area with at least
  // "max_embedding_width" quint8 zero values.
  tensorflow::quint8* zero_data;
  if (max_embedding_width <= ARRAYSIZE(static_zero_data)) {
    // static_zero_data is big enough so we don't need to allocate zero data
    zero_data = &static_zero_data[0];
  } else {
    // static_zero_data is not big enough: we need to allocate zero data
    zero_data_backing =
        absl::make_unique<tensorflow::quint8[]>(max_embedding_width);
    memset(zero_data_backing.get(), 0,
           sizeof(tensorflow::quint8) * max_embedding_width);
    zero_data = zero_data_backing.get();
  }
```

</details>

Also, prefer stack allocation over heap allocation when object lifetime is
bounded by the scope (although be careful with stack frame sizes for large
objects).

### Resize or reserve containers {#resize-or-reserve-containers}

When the maximum or expected maximum size of a vector (or some other container
types) is known in advance, pre-size the container's backing store (e.g., using
`resize` or `reserve` in C++).

<details markdown="1">
<summary>
Pre-size a vector and fill it in, rather than N push_back
operations.
</summary>

indexblockdecoder.cc

{: .bad-code}
```c++
for (int i = 0; i < ndocs-1; i++) {
  uint32 delta;
  ERRORCHECK(b->GetRice(rice_base, &delta));
  docs_.push_back(DocId(my_shard_ + (base + delta) * num_shards_));
  base = base + delta + 1;
}
docs_.push_back(last_docid_);
```

{: .new}
```c++
docs_.resize(ndocs);
DocId* docptr = &docs_[0];
for (int i = 0; i < ndocs-1; i++) {
  uint32 delta;
  ERRORCHECK(b.GetRice(rice_base, &delta));
  *docptr = DocId(my_shard_ + (base + delta) * num_shards_);
  docptr++;
  base = base + delta + 1;
}
*docptr = last_docid_;
```

</details>

Caveat: Do not use `resize` or `reserve` to grow one element at a time since
that may lead to quadratic behavior. Also, if element construction is expensive,
prefer an initial `reserve` call followed by several `push_back` or
`emplace_back` calls instead of an initial `resize` since that will double the
number of constructor calls.

### Avoid copying when possible {#avoid-copying-when-possible}

*   Prefer moving to copying data structures when possible.
*   If lifetime is not an issue, store pointers or indices instead of copies of
    objects in transient data structures. E.g., if a local map is used to select
    a set of protos from an incoming list of protos, we can make the map store
    just pointers to the incoming protos instead of copying potentially deeply
    nested data. Another common example is sorting a vector of indices rather
    than sorting a vector of large objects directly since the latter would incur
    significant copying/moving costs.

<details markdown="1">
<summary>
Avoid an extra copy when receiving a tensor via gRPC.
</summary>

A benchmark that sends around 400KB tensors speeds up by ~10-15%:

{: .bad-code}
```
Benchmark              Time(ns)    CPU(ns) Iterations
-----------------------------------------------------
BM_RPC/30/98k_mean    148764691 1369998944       1000
```

{: .new}
```
Benchmark              Time(ns)    CPU(ns) Iterations
-----------------------------------------------------
BM_RPC/30/98k_mean    131595940 1216998084       1000
```

</details>

<details markdown="1">
<summary>
Move large options structure rather than copying it.
</summary>

index.cc

{: .bad-code}
```c++
return search_iterators::DocPLIteratorFactory::Create(opts);
```

{: .new}
```c++
return search_iterators::DocPLIteratorFactory::Create(std::move(opts));
```

</details>

<details markdown="1">
<summary>
Use std::sort instead of std::stable_sort, which avoids
an internal copy inside the stable sort implementation.
</summary>

encoded-vector-hits.h

{: .bad-code}
```c++
std::stable_sort(hits_.begin(), hits_.end(),
                 gtl::OrderByField(&HitWithPayloadOffset::docid));
```

{: .new}
```c++
struct HitWithPayloadOffset {
  search_iterators::LocalDocId64 docid;
  int first_payload_offset;  // offset into the payload vector.
  int num_payloads;

  bool operator<(const HitWithPayloadOffset& other) const {
    return (docid < other.docid) ||
           (docid == other.docid &&
            first_payload_offset < other.first_payload_offset);
  }
};
    ...
    std::sort(hits_.begin(), hits_.end());
```

</details>

### Reuse temporary objects

A container or an object declared inside a loop will be recreated on every loop
iteration. This can lead to expensive construction, destruction, and resizing.
Hoisting the declaration outside the loop enables reuse and can provide a
significant performance boost. (Compilers are often unable to do such hoisting
on their own due to language semantics or their inability to ensure program
equivalence.)

<details markdown="1">
<summary>
Hoist variable definition outside of loop iteration.
</summary>

autofdo_profile_utils.h

{: .bad-code}
```c++
auto iterator = absl::WrapUnique(sstable->GetIterator());
while (!iterator->done()) {
  T profile;
  if (!profile.ParseFromString(iterator->value_view())) {
    return absl::InternalError(
        "Failed to parse mem_block to specified profile type.");
  }
  ...
  iterator->Next();
}
```

{: .new}
```c++
auto iterator = absl::WrapUnique(sstable->GetIterator());
T profile;
while (!iterator->done()) {
  if (!profile.ParseFromString(iterator->value_view())) {
    return absl::InternalError(
        "Failed to parse mem_block to specified profile type.");
  }
  ...
  iterator->Next();
}
```

</details>

<details markdown="1">
<summary>
Define a protobuf variable outside a loop so that its
allocated storage can be reused across loop iterations.
</summary>

stats-router.cc

{: .bad-code}
```c++
for (auto& r : routers_to_update) {
  ...
  ResourceRecord record;
  {
    MutexLock agg_lock(r.agg->mutex());
    r.agg->AddResourceRecordUsages(measure_indices, &record);
  }
  ...
}
```

{: .new}
```c++
ResourceRecord record;
for (auto& r : routers_to_update) {
  ...
  record.Clear();
  {
    MutexLock agg_lock(r.agg->mutex());
    r.agg->AddResourceRecordUsages(measure_indices, &record);
  }
  ...
}
```

</details>

<details markdown="1">
<summary>
Serialize to same std::string repeatedly.
</summary>

program_rep.cc

{: .bad-code}
```c++
std::string DeterministicSerialization(const proto2::Message& m) {
  std::string result;
  proto2::io::StringOutputStream sink(&result);
  proto2::io::CodedOutputStream out(&sink);
  out.SetSerializationDeterministic(true);
  m.SerializePartialToCodedStream(&out);
  return result;
}
```

{: .new}
```c++
absl::string_view DeterministicSerializationTo(const proto2::Message& m,
                                               std::string* scratch) {
  scratch->clear();
  proto2::io::StringOutputStream sink(scratch);
  proto2::io::CodedOutputStream out(&sink);
  out.SetSerializationDeterministic(true);
  m.SerializePartialToCodedStream(&out);
  return absl::string_view(*scratch);
}
```

</details>

Caveat: protobuf, string, vector, containers etc. tend to grow to the size of
the largest value ever stored in them. Therefore reconstructing them
periodically (e.g., after every N uses) can help reduce memory requirements and
reinitialization costs.

## Avoid unnecessary work {#avoid-unnecessary-work}

Perhaps one of the most effective categories of improving performance is
avoiding work you don't have to do. This can take many forms, including creating
specialized paths through code for common cases that avoid more general
expensive computation, precomputation, deferring work until it is really needed,
hoisting work into less-frequently executed pieces of code, and other similar
approaches. Below are many examples of this general approach, categorized into a
few representative categories.

### Fast paths for common cases

Often, code is written to cover all cases, but some subset of the cases are much
simpler and more common than others. E.g., `vector::push_back` usually has
enough space for the new element, but contains code to resize the underlying
storage when it does not. Some attention paid to the structure of code can help
make the common simple case faster without hurting uncommon case performance
significantly.

<details markdown="1">
<summary>
Make fast path cover more common cases.
</summary>

Add handling of trailing single ASCII bytes, rather than only handling multiples
of four bytes with this routine. This avoids calling the slower generic routine
for all-ASCII strings that are, for example, 5 bytes.

utf8statetable.cc

{: .bad-code}
```c++
// Scan a UTF-8 stringpiece based on state table.
// Always scan complete UTF-8 characters
// Set number of bytes scanned. Return reason for exiting
// OPTIMIZED for case of 7-bit ASCII 0000..007f all valid
int UTF8GenericScanFastAscii(const UTF8ScanObj* st, absl::string_view str,
                             int* bytes_consumed) {
                             ...
  int exit_reason;
  do {
    //  Skip 8 bytes of ASCII at a whack; no endianness issue
    while ((src_limit - src >= 8) &&
           (((UNALIGNED_LOAD32(src + 0) | UNALIGNED_LOAD32(src + 4)) &
             0x80808080) == 0)) {
      src += 8;
    }
    //  Run state table on the rest
    int rest_consumed;
    exit_reason = UTF8GenericScan(
        st, absl::ClippedSubstr(str, src - initial_src), &rest_consumed);
    src += rest_consumed;
  } while (exit_reason == kExitDoAgain);

  *bytes_consumed = src - initial_src;
  return exit_reason;
}
```

{: .new}
```c++
// Scan a UTF-8 stringpiece based on state table.
// Always scan complete UTF-8 characters
// Set number of bytes scanned. Return reason for exiting
// OPTIMIZED for case of 7-bit ASCII 0000..007f all valid
int UTF8GenericScanFastAscii(const UTF8ScanObj* st, absl::string_view str,
                             int* bytes_consumed) {
                             ...
  int exit_reason = kExitOK;
  do {
    //  Skip 8 bytes of ASCII at a whack; no endianness issue
    while ((src_limit - src >= 8) &&
           (((UNALIGNED_LOAD32(src + 0) | UNALIGNED_LOAD32(src + 4)) &
             0x80808080) == 0)) {
      src += 8;
    }
    while (src < src_limit && Is7BitAscii(*src)) { // Skip ASCII bytes
      src++;
    }
    if (src < src_limit) {
      //  Run state table on the rest
      int rest_consumed;
      exit_reason = UTF8GenericScan(
          st, absl::ClippedSubstr(str, src - initial_src), &rest_consumed);
      src += rest_consumed;
    }
  } while (exit_reason == kExitDoAgain);

  *bytes_consumed = src - initial_src;
  return exit_reason;
}
```

</details>

<details markdown="1">
<summary>
Simpler fast paths for InlinedVector.
</summary>

inlined_vector.h

{: .bad-code}
```c++
auto Storage<T, N, A>::Resize(ValueAdapter values, size_type new_size) -> void {
  StorageView storage_view = MakeStorageView();

  IteratorValueAdapter<MoveIterator> move_values(
      MoveIterator(storage_view.data));

  AllocationTransaction allocation_tx(GetAllocPtr());
  ConstructionTransaction construction_tx(GetAllocPtr());

  absl::Span<value_type> construct_loop;
  absl::Span<value_type> move_construct_loop;
  absl::Span<value_type> destroy_loop;

  if (new_size > storage_view.capacity) {
  ...
  } else if (new_size > storage_view.size) {
    construct_loop = {storage_view.data + storage_view.size,
                      new_size - storage_view.size};
  } else {
    destroy_loop = {storage_view.data + new_size, storage_view.size - new_size};
  }
```

{: .new}
```c++
auto Storage<T, N, A>::Resize(ValueAdapter values, size_type new_size) -> void {
  StorageView storage_view = MakeStorageView();
  auto* const base = storage_view.data;
  const size_type size = storage_view.size;
  auto* alloc = GetAllocPtr();
  if (new_size <= size) {
    // Destroy extra old elements.
    inlined_vector_internal::DestroyElements(alloc, base + new_size,
                                             size - new_size);
  } else if (new_size <= storage_view.capacity) {
    // Construct new elements in place.
    inlined_vector_internal::ConstructElements(alloc, base + size, &values,
                                               new_size - size);
  } else {
  ...
  }
```

</details>

<details markdown="1">
<summary>
Fast path for common cases of initializing 1-D to 4-D
tensors.
</summary>

tensor_shape.cc

{: .bad-code}
```c++
template <class Shape>
TensorShapeBase<Shape>::TensorShapeBase(gtl::ArraySlice<int64> dim_sizes) {
  set_tag(REP16);
  set_data_type(DT_INVALID);
  set_ndims_byte(0);
  set_num_elements(1);
  for (int64 s : dim_sizes) {
    AddDim(internal::SubtleMustCopy(s));
  }
}
```

{: .new}
```c++
template <class Shape>
void TensorShapeBase<Shape>::InitDims(gtl::ArraySlice<int64> dim_sizes) {
  DCHECK_EQ(tag(), REP16);

  // Allow sizes that are under kint64max^0.25 so that 4-way multiplication
  // below cannot overflow.
  static const uint64 kMaxSmall = 0xd744;
  static_assert(kMaxSmall * kMaxSmall * kMaxSmall * kMaxSmall <= kint64max,
                "bad overflow check");
  bool large_size = false;
  for (auto s : dim_sizes) {
    if (s > kMaxSmall) {
      large_size = true;
      break;
    }
  }

  if (!large_size) {
    // Every size fits in 16 bits; use fast-paths for dims in {1,2,3,4}.
    uint16* dst = as16()->dims_;
    switch (dim_sizes.size()) {
      case 1: {
        set_ndims_byte(1);
        const int64 size = dim_sizes[0];
        const bool neg = Set16(kIsPartial, dst, 0, size);
        set_num_elements(neg ? -1 : size);
        return;
      }
      case 2: {
        set_ndims_byte(2);
        const int64 size0 = dim_sizes[0];
        const int64 size1 = dim_sizes[1];
        bool neg = Set16(kIsPartial, dst, 0, size0);
        neg |= Set16(kIsPartial, dst, 1, size1);
        set_num_elements(neg ? -1 : (size0 * size1));
        return;
      }
      case 3: {
      ...
      }
      case 4: {
      ...
      }
    }
  }

  set_ndims_byte(0);
  set_num_elements(1);
  for (int64 s : dim_sizes) {
    AddDim(internal::SubtleMustCopy(s));
  }
}
```

</details>

<details markdown="1">
<summary>
Make varint parser fast path cover just the 1-byte case,
instead of covering 1-byte and 2-byte cases.
</summary>

Reducing the size of the (inlined) fast path reduces code size and icache
pressure, which leads to improved performance.

parse_context.h

{: .bad-code}
```c++
template <typename T>
PROTOBUF_NODISCARD const char* VarintParse(const char* p, T* out) {
  auto ptr = reinterpret_cast<const uint8_t*>(p);
  uint32_t res = ptr[0];
  if (!(res & 0x80)) {
    *out = res;
    return p + 1;
  }
  uint32_t byte = ptr[1];
  res += (byte - 1) << 7;
  if (!(byte & 0x80)) {
    *out = res;
    return p + 2;
  }
  return VarintParseSlow(p, res, out);
}
```

{: .new}
```c++
template <typename T>
PROTOBUF_NODISCARD const char* VarintParse(const char* p, T* out) {
  auto ptr = reinterpret_cast<const uint8_t*>(p);
  uint32_t res = ptr[0];
  if (!(res & 0x80)) {
    *out = res;
    return p + 1;
  }
  return VarintParseSlow(p, res, out);
}
```

parse_context.cc

{: .bad-code}
```c++
std::pair<const char*, uint32_t> VarintParseSlow32(const char* p,
                                                   uint32_t res) {
  for (std::uint32_t i = 2; i < 5; i++) {
  ...
}
...
std::pair<const char*, uint64_t> VarintParseSlow64(const char* p,
                                                   uint32_t res32) {
  uint64_t res = res32;
  for (std::uint32_t i = 2; i < 10; i++) {
  ...
}
```

{: .new}
```c++
std::pair<const char*, uint32_t> VarintParseSlow32(const char* p,
                                                   uint32_t res) {
  for (std::uint32_t i = 1; i < 5; i++) {
  ...
}
...
std::pair<const char*, uint64_t> VarintParseSlow64(const char* p,
                                                   uint32_t res32) {
  uint64_t res = res32;
  for (std::uint32_t i = 1; i < 10; i++) {
  ...
}
```

</details>

<details markdown="1">
<summary>
Skip significant work in RPC_Stats_Measurement addition if
no errors have occurred.
</summary>

rpc-stats.h

{: .bad-code}
```c++
struct RPC_Stats_Measurement {
  ...
  double errors[RPC::NUM_ERRORS];
```

{: .new}
```c++
struct RPC_Stats_Measurement {
  ...
  double get_errors(int index) const { return errors[index]; }
  void set_errors(int index, double value) {
    errors[index] = value;
    any_errors_set = true;
  }
 private:
  ...
  // We make this private so that we can keep track of whether any of
  // these values have been set to non-zero values.
  double errors[RPC::NUM_ERRORS];
  bool any_errors_set;  // True iff any of the errors[i] values are non-zero
```

rpc-stats.cc

{: .bad-code}
```c++
void RPC_Stats_Measurement::operator+=(const RPC_Stats_Measurement& x) {
  ...
  for (int i = 0; i < RPC::NUM_ERRORS; ++i) {
    errors[i] += x.errors[i];
  }
}
```

{: .new}
```c++
void RPC_Stats_Measurement::operator+=(const RPC_Stats_Measurement& x) {
  ...
  if (x.any_errors_set) {
    for (int i = 0; i < RPC::NUM_ERRORS; ++i) {
      errors[i] += x.errors[i];
    }
    any_errors_set = true;
  }
}
```

</details>

<details markdown="1">
<summary>
Do array lookup on first byte of string to often avoid
fingerprinting full string.
</summary>

soft-tokens-helper.cc

{: .bad-code}
```c++
bool SoftTokensHelper::IsSoftToken(const StringPiece& token) const {
  return soft_tokens_.find(Fingerprint(token.data(), token.size())) !=
      soft_tokens_.end();
}
```

soft-tokens-helper.h

{: .new}
```c++
class SoftTokensHelper {
 ...
 private:
  ...
  // Since soft tokens are mostly punctuation-related, for performance
  // purposes, we keep an array filter_.  filter_[i] is true iff any
  // of the soft tokens start with the byte value 'i'.  This avoids
  // fingerprinting a term in the common case, since we can just do an array
  // lookup based on the first byte, and if filter_[b] is false, then
  // we can return false immediately.
  bool          filter_[256];
  ...
};

inline bool SoftTokensHelper::IsSoftToken(const StringPiece& token) const {
  if (token.size() >= 1) {
    char first_char = token.data()[0];
    if (!filter_[first_char]) {
      return false;
    }
  }
  return IsSoftTokenFallback(token);
}
```

soft-tokens-helper.cc

{: .new}
```c++
bool SoftTokensHelper::IsSoftTokenFallback(const StringPiece& token) const {
  return soft_tokens_.find(Fingerprint(token.data(), token.size())) !=
      soft_tokens_.end();
}
```

</details>

### Precompute expensive information once

<details markdown="1">
<summary>
Precompute a TensorFlow graph execution node property
that allows us to quickly rule out certain unusual cases.
</summary>

executor.cc

{: .bad-code}
```c++
struct NodeItem {
  ...
  bool kernel_is_expensive = false;  // True iff kernel->IsExpensive()
  bool kernel_is_async = false;      // True iff kernel->AsAsync() != nullptr
  bool is_merge = false;             // True iff IsMerge(node)
  ...
  if (IsEnter(node)) {
  ...
  } else if (IsExit(node)) {
  ...
  } else if (IsNextIteration(node)) {
  ...
  } else {
    // Normal path for most nodes
    ...
  }
```

{: .new}
```c++
struct NodeItem {
  ...
  bool kernel_is_expensive : 1;  // True iff kernel->IsExpensive()
  bool kernel_is_async : 1;      // True iff kernel->AsAsync() != nullptr
  bool is_merge : 1;             // True iff IsMerge(node)
  bool is_enter : 1;             // True iff IsEnter(node)
  bool is_exit : 1;              // True iff IsExit(node)
  bool is_control_trigger : 1;   // True iff IsControlTrigger(node)
  bool is_sink : 1;              // True iff IsSink(node)
  // True iff IsEnter(node) || IsExit(node) || IsNextIteration(node)
  bool is_enter_exit_or_next_iter : 1;
  ...
  if (!item->is_enter_exit_or_next_iter) {
    // Fast path for nodes types that don't need special handling
    DCHECK_EQ(input_frame, output_frame);
    ...
  } else if (item->is_enter) {
  ...
  } else if (item->is_exit) {
  ...
  } else {
    DCHECK(IsNextIteration(node));
    ...
  }
```

</details>

<details markdown="1">
<summary>
Precompute 256 element array and use during trigram
initialization.
</summary>

byte_trigram_classifier.cc

{: .bad-code}
```c++
void ByteTrigramClassifier::VerifyModel(void) const {
  ProbT class_sums[num_classes_];
  for (int cls = 0; cls < num_classes_; cls++) {
    class_sums[cls] = 0;
  }
  for (ByteNgramId id = 0; id < trigrams_.num_trigrams(); id++) {
    for (int cls = 0; cls < num_classes_; ++cls) {
      class_sums[cls] += Prob(trigram_probs_[id].log_probs[cls]);
    }
  }
  ...
}
```

{: .new}
```c++
void ByteTrigramClassifier::VerifyModel(void) const {
  CHECK_EQ(sizeof(ByteLogProbT), 1);
  ProbT fast_prob[256];
  for (int b = 0; b < 256; b++) {
    fast_prob[b] = Prob(static_cast<ByteLogProbT>(b));
  }

  ProbT class_sums[num_classes_];
  for (int cls = 0; cls < num_classes_; cls++) {
    class_sums[cls] = 0;
  }
  for (ByteNgramId id = 0; id < trigrams_.num_trigrams(); id++) {
    for (int cls = 0; cls < num_classes_; ++cls) {
      class_sums[cls] += fast_prob[trigram_probs_[id].log_probs[cls]];
    }
  }
  ...
}
```

</details>

General advice: check for malformed inputs at module boundaries instead of
repeating checks internally.

### Move expensive computations outside loops

<details markdown="1">
<summary>
Move bounds computation outside loop.
</summary>

literal_linearizer.cc

{: .bad-code}
```c++
for (int64 i = 0; i < src_shape.dimensions(dimension_numbers.front());
     ++i) {
```

{: .new}
```c++
int64 dim_front = src_shape.dimensions(dimension_numbers.front());
const uint8* src_buffer_data = src_buffer.data();
uint8* dst_buffer_data = dst_buffer.data();
for (int64 i = 0; i < dim_front; ++i) {
```

</details>

### Defer expensive computation {#defer-expensive-computation}

<details markdown="1">
<summary>
Defer GetSubSharding call until needed, which reduces 43
seconds of CPU time to 2 seconds.
</summary>

sharding_propagation.cc

{: .bad-code}
```c++
HloSharding alternative_sub_sharding =
    user.sharding().GetSubSharding(user.shape(), {i});
if (user.operand(i) == &instruction &&
    hlo_sharding_util::IsShardingMoreSpecific(alternative_sub_sharding,
                                              sub_sharding)) {
  sub_sharding = alternative_sub_sharding;
}
```

{: .new}
```c++
if (user.operand(i) == &instruction) {
  // Only evaluate GetSubSharding if this operand is of interest,
  // as it is relatively expensive.
  HloSharding alternative_sub_sharding =
      user.sharding().GetSubSharding(user.shape(), {i});
  if (hlo_sharding_util::IsShardingMoreSpecific(
          alternative_sub_sharding, sub_sharding)) {
    sub_sharding = alternative_sub_sharding;
  }
}
```

</details>

<details markdown="1">
<summary>
Don't update stats eagerly; compute them on demand.
</summary>

Do not update stats on the very frequent allocation/deallocation calls. Instead,
compute stats on demand when the much less frequently called Stats() method is
invoked.

</details>

<details markdown="1">
<summary>
Preallocate 10 nodes not 200 for query handling in Google's
web server.
</summary>

A simple change that reduced web server's CPU usage by 7.5%.

querytree.h

{: .bad-code}
```c++
static const int kInitParseTreeSize = 200;   // initial size of querynode pool
```

{: .new}
```c++
static const int kInitParseTreeSize = 10;   // initial size of querynode pool
```

</details>

<details markdown="1">
<summary>
Change search order for 19% throughput improvement.
</summary>

An old search system (circa 2000) had two tiers: one contained a full-text
index, and the other tier contained just the index for the title and anchor
terms. We used to search the smaller title/anchor tier first.
Counter-intuitively, we found that it is cheaper to search the larger full-text
index tier first since if we reach the end of the full-text tier, we can
entirely skip searching the title/anchor tier (a subset of the full-text tier).
This happened reasonably often and allowed us to reduce the average number of
disk seeks to process a query.

See discussion of title and anchor text handling in
[The Anatomy of a Large-Scale Hypertextual Web Search Engine](https://research.google/pubs/the-anatomy-of-a-large-scale-hypertextual-web-search-engine/)
</details>

### Specialize code

A particular performance-sensitive call-site may not need the full generality
provided by a general-purpose library. Consider writing specialized code in such
cases instead of calling the general-purpose code if it provides a performance
improvement.

<details markdown="1">
<summary>
Custom printing code for Histogram class is 4x as fast as
sprintf.
</summary>

This code is performance sensitive because it is invoked when monitoring systems
gather statistics from various servers.

histogram_export.cc

{: .bad-code}
```c++
void Histogram::PopulateBuckets(const string &prefix,
                                expvar::MapProto *const var) const {
                                ...
  for (int i = min_bucket; i <= max_bucket; ++i) {
    const double count = BucketCount(i);
    if (!export_empty_buckets && count == 0.0) continue;
    acc += count;
    // The label format of exported buckets for discrete histograms
    // specifies an inclusive upper bound, which is the same as in
    // the original Histogram implementation.  This format is not
    // applicable to non-discrete histograms, so a half-open interval
    // is used for them, with "_" instead of "-" as a separator to
    // make possible to distinguish the formats.
    string key =
        options_.export_cumulative_counts() ?
            StringPrintf("%.12g", boundaries_->BucketLimit(i)) :
        options_.discrete() ?
            StringPrintf("%.0f-%.0f",
                         ceil(boundaries_->BucketStart(i)),
                         ceil(boundaries_->BucketLimit(i)) - 1.0) :
            StringPrintf("%.12g_%.12g",
                         boundaries_->BucketStart(i),
                         boundaries_->BucketLimit(i));
    EscapeMapKey(&key);
    const double value = options_.export_cumulative_counts() ? acc : count;
    expvar::AddMapFloat(StrCat(prefix,
                               options_.export_bucket_key_prefix(),
                               key),
                        value * count_mult,
                        var);
  }
```

{: .new}
```c++
// Format "val" according to format.  If "need_escape" is true, then the
// format can produce output with a '.' in it, and the result will be escaped.
// If "need_escape" is false, then the caller guarantees that format is
// such that the resulting number will not have any '.' characters and
// therefore we can avoid calling EscapeKey.
// The function is free to use "*scratch" for scratch space if necessary,
// and the resulting StringPiece may point into "*scratch".
static StringPiece FormatNumber(const char* format,
                                bool need_escape,
                                double val, string* scratch) {
  // This routine is specialized to work with only a limited number of formats
  DCHECK(StringPiece(format) == "%.0f" || StringPiece(format) == "%.12g");

  scratch->clear();
  if (val == trunc(val) && val >= kint32min && val <= kint32max) {
    // An integer for which we can just use StrAppend
    StrAppend(scratch, static_cast<int32>(val));
    return StringPiece(*scratch);
  } else if (isinf(val)) {
    // Infinity, represent as just 'inf'.
    return StringPiece("inf", 3);
  } else {
    // Format according to "format", and possibly escape.
    StringAppendF(scratch, format, val);
    if (need_escape) {
      EscapeMapKey(scratch);
    } else {
      DCHECK(!StringPiece(*scratch).contains("."));
    }
    return StringPiece(*scratch);
  }
}
...
void Histogram::PopulateBuckets(const string &prefix,
                                expvar::MapProto *const var) const {
                                ...
  const string full_key_prefix = StrCat(prefix,
                                        options_.export_bucket_key_prefix());
  string key = full_key_prefix;  // Keys will start with "full_key_prefix".
  string start_scratch;
  string limit_scratch;
  const bool cumul_counts = options_.export_cumulative_counts();
  const bool discrete = options_.discrete();
  for (int i = min_bucket; i <= max_bucket; ++i) {
    const double count = BucketCount(i);
    if (!export_empty_buckets && count == 0.0) continue;
    acc += count;
    // The label format of exported buckets for discrete histograms
    // specifies an inclusive upper bound, which is the same as in
    // the original Histogram implementation.  This format is not
    // applicable to non-discrete histograms, so a half-open interval
    // is used for them, with "_" instead of "-" as a separator to
    // make possible to distinguish the formats.
    key.resize(full_key_prefix.size());  // Start with full_key_prefix.
    DCHECK_EQ(key, full_key_prefix);

    const double limit = boundaries_->BucketLimit(i);
    if (cumul_counts) {
      StrAppend(&key, FormatNumber("%.12g", true, limit, &limit_scratch));
    } else {
      const double start = boundaries_->BucketStart(i);
      if (discrete) {
        StrAppend(&key,
                  FormatNumber("%.0f", false, ceil(start), &start_scratch),
                  "-",
                  FormatNumber("%.0f", false, ceil(limit) - 1.0,
                               &limit_scratch));
      } else {
        StrAppend(&key,
                  FormatNumber("%.12g", true, start, &start_scratch),
                  "_",
                  FormatNumber("%.12g", true, limit, &limit_scratch));
      }
    }
    const double value = cumul_counts ? acc : count;

    // Add to map var
    expvar::AddMapFloat(key, value * count_mult, var);
  }
}
```

</details>

<details markdown="1">
<summary>
Add specializations for VLOG(1), VLOG(2), … for speed and
smaller code size.
</summary>

`VLOG` is a heavily used macro throughout the code base. This change avoids
passing an extra integer constant at nearly every call site (if the log level is
constant at the call site, as it almost always is, as in `VLOG(1) << ...`),
which saves code space.

vlog_is_on.h

{: .bad-code}
```c++
class VLogSite final {
 public:
  ...
  bool IsEnabled(int level) {
    int stale_v = v_.load(std::memory_order_relaxed);
    if (ABSL_PREDICT_TRUE(level > stale_v)) {
      return false;
    }

    // We put everything other than the fast path, i.e. vlogging is initialized
    // but not on, behind an out-of-line function to reduce code size.
    return SlowIsEnabled(stale_v, level);
  }
  ...
 private:
  ...
  ABSL_ATTRIBUTE_NOINLINE
  bool SlowIsEnabled(int stale_v, int level);
  ...
};
```

{: .new}
```c++
class VLogSite final {
 public:
  ...
  bool IsEnabled(int level) {
    int stale_v = v_.load(std::memory_order_relaxed);
    if (ABSL_PREDICT_TRUE(level > stale_v)) {
      return false;
    }

    // We put everything other than the fast path, i.e. vlogging is initialized
    // but not on, behind an out-of-line function to reduce code size.
    // "level" is almost always a call-site constant, so we can save a bit
    // of code space by special-casing for levels 1, 2, and 3.
#if defined(__has_builtin) && __has_builtin(__builtin_constant_p)
    if (__builtin_constant_p(level)) {
      if (level == 0) return SlowIsEnabled0(stale_v);
      if (level == 1) return SlowIsEnabled1(stale_v);
      if (level == 2) return SlowIsEnabled2(stale_v);
      if (level == 3) return SlowIsEnabled3(stale_v);
      if (level == 4) return SlowIsEnabled4(stale_v);
      if (level == 5) return SlowIsEnabled5(stale_v);
    }
#endif
    return SlowIsEnabled(stale_v, level);
    ...
 private:
  ...
  ABSL_ATTRIBUTE_NOINLINE
  bool SlowIsEnabled(int stale_v, int level);
  ABSL_ATTRIBUTE_NOINLINE bool SlowIsEnabled0(int stale_v);
  ABSL_ATTRIBUTE_NOINLINE bool SlowIsEnabled1(int stale_v);
  ABSL_ATTRIBUTE_NOINLINE bool SlowIsEnabled2(int stale_v);
  ABSL_ATTRIBUTE_NOINLINE bool SlowIsEnabled3(int stale_v);
  ABSL_ATTRIBUTE_NOINLINE bool SlowIsEnabled4(int stale_v);
  ABSL_ATTRIBUTE_NOINLINE bool SlowIsEnabled5(int stale_v);
  ...
};
```

vlog_is_on.cc

{: .new}
```c++
bool VLogSite::SlowIsEnabled0(int stale_v) { return SlowIsEnabled(stale_v, 0); }
bool VLogSite::SlowIsEnabled1(int stale_v) { return SlowIsEnabled(stale_v, 1); }
bool VLogSite::SlowIsEnabled2(int stale_v) { return SlowIsEnabled(stale_v, 2); }
bool VLogSite::SlowIsEnabled3(int stale_v) { return SlowIsEnabled(stale_v, 3); }
bool VLogSite::SlowIsEnabled4(int stale_v) { return SlowIsEnabled(stale_v, 4); }
bool VLogSite::SlowIsEnabled5(int stale_v) { return SlowIsEnabled(stale_v, 5); }
```

</details>

<details markdown="1">
<summary>
Replace RE2 call with a simple prefix match when possible.
</summary>

read_matcher.cc

{: .bad-code}
```c++
enum MatchItemType {
  MATCH_TYPE_INVALID,
  MATCH_TYPE_RANGE,
  MATCH_TYPE_EXACT,
  MATCH_TYPE_REGEXP,
};
```

{: .new}
```c++
enum MatchItemType {
  MATCH_TYPE_INVALID,
  MATCH_TYPE_RANGE,
  MATCH_TYPE_EXACT,
  MATCH_TYPE_REGEXP,
  MATCH_TYPE_PREFIX,   // Special type for regexp ".*"
};
```

read_matcher.cc

{: .bad-code}
```c++
p->type = MATCH_TYPE_REGEXP;
```

{: .new}
```c++
term.NonMetaPrefix().CopyToString(&p->prefix);
if (term.RegexpSuffix() == ".*") {
  // Special case for a regexp that matches anything, so we can
  // bypass RE2::FullMatch
  p->type = MATCH_TYPE_PREFIX;
} else {
  p->type = MATCH_TYPE_REGEXP;
```

</details>

<details markdown="1">
<summary>
Use StrCat rather than StringPrintf to format IP
addresses.
</summary>

ipaddress.cc

{: .bad-code}
```c++
string IPAddress::ToString() const {
  char buf[INET6_ADDRSTRLEN];

  switch (address_family_) {
    case AF_INET:
      CHECK(inet_ntop(AF_INET, &addr_.addr4, buf, INET6_ADDRSTRLEN) != NULL);
      return buf;
    case AF_INET6:
      CHECK(inet_ntop(AF_INET6, &addr_.addr6, buf, INET6_ADDRSTRLEN) != NULL);
      return buf;
    case AF_UNSPEC:
      LOG(DFATAL) << "Calling ToString() on an empty IPAddress";
      return "";
    default:
      LOG(FATAL) << "Unknown address family " << address_family_;
  }
}
...
string IPAddressToURIString(const IPAddress& ip) {
  switch (ip.address_family()) {
    case AF_INET6:
      return StringPrintf("[%s]", ip.ToString().c_str());
    default:
      return ip.ToString();
  }
}
...
string SocketAddress::ToString() const {
  return IPAddressToURIString(host_) + StringPrintf(":%u", port_);
}
```

{: .new}
```c++
string IPAddress::ToString() const {
  char buf[INET6_ADDRSTRLEN];

  switch (address_family_) {
    case AF_INET: {
      uint32 addr = gntohl(addr_.addr4.s_addr);
      int a1 = static_cast<int>((addr >> 24) & 0xff);
      int a2 = static_cast<int>((addr >> 16) & 0xff);
      int a3 = static_cast<int>((addr >> 8) & 0xff);
      int a4 = static_cast<int>(addr & 0xff);
      return StrCat(a1, ".", a2, ".", a3, ".", a4);
    }
    case AF_INET6:
      CHECK(inet_ntop(AF_INET6, &addr_.addr6, buf, INET6_ADDRSTRLEN) != NULL);
      return buf;
    case AF_UNSPEC:
      LOG(DFATAL) << "Calling ToString() on an empty IPAddress";
      return "";
    default:
      LOG(FATAL) << "Unknown address family " << address_family_;
  }
}
...
string IPAddressToURIString(const IPAddress& ip) {
  switch (ip.address_family()) {
    case AF_INET6:
      return StrCat("[", ip.ToString(), "]");
    default:
      return ip.ToString();
  }
}
...
string SocketAddress::ToString() const {
  return StrCat(IPAddressToURIString(host_), ":", port_);
}
```

</details>

### Use caching to avoid repeated work {#use-caching-to-avoid-repeated-work}

<details markdown="1">
<summary>
Cache based on precomputed fingerprint of large
serialized proto.
</summary>

dp_ops.cc

{: .bad-code}
```c++
InputOutputMappingProto mapping_proto;
PLAQUE_OP_REQUIRES(
    mapping_proto.ParseFromStringPiece(GetAttrMappingProto(state)),
    absl::InternalError("Failed to parse InputOutputMappingProto"));
ParseMapping(mapping_proto);
```

{: .new}
```c++
uint64 mapping_proto_fp = GetAttrMappingProtoFp(state);
{
  absl::MutexLock l(&fp_to_iometa_mu);
  if (fp_to_iometa == nullptr) {
    fp_to_iometa =
        new absl::flat_hash_map<uint64, std::unique_ptr<ProgramIOMetadata>>;
  }
  auto it = fp_to_iometa->find(mapping_proto_fp);
  if (it != fp_to_iometa->end()) {
    io_metadata_ = it->second.get();
  } else {
    auto serial_proto = GetAttrMappingProto(state);
    DCHECK_EQ(mapping_proto_fp, Fingerprint(serial_proto));
    InputOutputMappingProto mapping_proto;
    PLAQUE_OP_REQUIRES(
        mapping_proto.ParseFromStringPiece(GetAttrMappingProto(state)),
        absl::InternalError("Failed to parse InputOutputMappingProto"));
    auto io_meta = ParseMapping(mapping_proto);
    io_metadata_ = io_meta.get();
    (*fp_to_iometa)[mapping_proto_fp] = std::move(io_meta);
  }
}
```

</details>

### Make the compiler's job easier

The compiler may have trouble optimizing through layers of abstractions because
it must make conservative assumptions about the overall behavior of the code, or
may not make the right speed vs. size tradeoffs. The application programmer will
often know more about the behavior of the system and can aid the compiler by
rewriting the code to operate at a lower level. However, only do this when
profiles show an issue since compilers will often get things right on their own.
Looking at the generated assembly code for performance critical routines can
help you understand if the compiler is "getting it right". Pprof provides a very
helpful [display of source code interleaved with disassembly][annotated source]
and annotated with performance data.

Some techniques that may be useful:

1.  Avoid functions calls in hot functions (allows the compiler to avoid frame
    setup costs).
2.  Move slow-path code into a separate tail-called function.
3.  Copy small amounts of data into local variables before heavy use. This can
    let the compiler assume there is no aliasing with other data, which may
    improve auto-vectorization and register allocation.
4.  Hand-unroll very hot loops.

<details markdown="1">
<summary>
Speed up ShapeUtil::ForEachState by replacing absl::Span
with raw pointers to the underlying arrays.
</summary>

shape_util.h

{: .bad-code}
```c++
struct ForEachState {
  ForEachState(const Shape& s, absl::Span<const int64_t> b,
               absl::Span<const int64_t> c, absl::Span<const int64_t> i);
  ~ForEachState();

  const Shape& shape;
  const absl::Span<const int64_t> base;
  const absl::Span<const int64_t> count;
  const absl::Span<const int64_t> incr;
```

{: .new}
```c++
struct ForEachState {
  ForEachState(const Shape& s, absl::Span<const int64_t> b,
               absl::Span<const int64_t> c, absl::Span<const int64_t> i);
  inline ~ForEachState() = default;

  const Shape& shape;
  // Pointers to arrays of the passed-in spans
  const int64_t* const base;
  const int64_t* const count;
  const int64_t* const incr;
```

</details>

<details markdown="1">
<summary>
Hand unroll
<a href="https://en.wikipedia.org/wiki/Cyclic_redundancy_check">cyclic
redundancy check</a> (CRC) computation loop.
</summary>

crc.cc

{: .bad-code}
```c++
void CRC32::Extend(uint64 *lo, uint64 *hi, const void *bytes, size_t length)
                      const {
                      ...
  // Process bytes 4 at a time
  while ((p + 4) <= e) {
    uint32 c = l ^ WORD(p);
    p += 4;
    l = this->table3_[c & 0xff] ^
        this->table2_[(c >> 8) & 0xff] ^
        this->table1_[(c >> 16) & 0xff] ^
        this->table0_[c >> 24];
  }

  // Process the last few bytes
  while (p != e) {
    int c = (l & 0xff) ^ *p++;
    l = this->table0_[c] ^ (l >> 8);
  }
  *lo = l;
}
```

{: .new}
```c++
void CRC32::Extend(uint64 *lo, uint64 *hi, const void *bytes, size_t length)
                      const {
                      ...
#define STEP {                                  \
    uint32 c = l ^ WORD(p);                     \
    p += 4;                                     \
    l = this->table3_[c & 0xff] ^               \
        this->table2_[(c >> 8) & 0xff] ^        \
        this->table1_[(c >> 16) & 0xff] ^       \
        this->table0_[c >> 24];                 \
}

  // Process bytes 16 at a time
  while ((e-p) >= 16) {
    STEP;
    STEP;
    STEP;
    STEP;
  }

  // Process bytes 4 at a time
  while ((p + 4) <= e) {
    STEP;
  }
#undef STEP

  // Process the last few bytes
  while (p != e) {
    int c = (l & 0xff) ^ *p++;
    l = this->table0_[c] ^ (l >> 8);
  }
  *lo = l;
}

```

</details>

<details markdown="1">
<summary>
Handle four characters at a time when parsing Spanner
keys.
</summary>

1.  Hand unroll loop to deal with four characters at a time rather than using
    memchr

2.  Manually unroll loop for finding separated sections of name

3.  Go backwards to find separated portions of a name with '#' separators
    (rather than forwards) since the first part is likely the longest in the
    name.

key.cc

{: .bad-code}
```c++
void Key::InitSeps(const char* start) {
  const char* base = &rep_[0];
  const char* limit = base + rep_.size();
  const char* s = start;

  DCHECK_GE(s, base);
  DCHECK_LT(s, limit);

  for (int i = 0; i < 3; i++) {
    s = (const char*)memchr(s, '#', limit - s);
    DCHECK(s != NULL);
    seps_[i] = s - base;
    s++;
  }
}
```

{: .new}
```c++
inline const char* ScanBackwardsForSep(const char* base, const char* p) {
  while (p >= base + 4) {
    if (p[0] == '#') return p;
    if (p[-1] == '#') return p-1;
    if (p[-2] == '#') return p-2;
    if (p[-3] == '#') return p-3;
    p -= 4;
  }
  while (p >= base && *p != '#') p--;
  return p;
}

void Key::InitSeps(const char* start) {
  const char* base = &rep_[0];
  const char* limit = base + rep_.size();
  const char* s = start;

  DCHECK_GE(s, base);
  DCHECK_LT(s, limit);

  // We go backwards from the end of the string, rather than forwards,
  // since the directory name might be long and definitely doesn't contain
  // any '#' characters.
  const char* p = ScanBackwardsForSep(s, limit - 1);
  DCHECK(*p == '#');
  seps_[2] = p - base;
  p--;

  p = ScanBackwardsForSep(s, p);
  DCHECK(*p == '#');
  seps_[1] = p - base;
  p--;

  p = ScanBackwardsForSep(s, p);
  DCHECK(*p == '#');
  seps_[0] = p - base;
}
```

</details>

<details markdown="1">
<summary>
Avoid frame setup costs by converting ABSL_LOG(FATAL) to
ABSL_DCHECK(false).
</summary>

arena_cleanup.h

{: .bad-code}
```c++
inline ABSL_ATTRIBUTE_ALWAYS_INLINE size_t Size(Tag tag) {
  if (!EnableSpecializedTags()) return sizeof(DynamicNode);

  switch (tag) {
    case Tag::kDynamic:
      return sizeof(DynamicNode);
    case Tag::kString:
      return sizeof(TaggedNode);
    case Tag::kCord:
      return sizeof(TaggedNode);
    default:
      ABSL_LOG(FATAL) << "Corrupted cleanup tag: " << static_cast<int>(tag);
      return sizeof(DynamicNode);
  }
}
```

{: .new}
```c++
inline ABSL_ATTRIBUTE_ALWAYS_INLINE size_t Size(Tag tag) {
  if (!EnableSpecializedTags()) return sizeof(DynamicNode);

  switch (tag) {
    case Tag::kDynamic:
      return sizeof(DynamicNode);
    case Tag::kString:
      return sizeof(TaggedNode);
    case Tag::kCord:
      return sizeof(TaggedNode);
    default:
      ABSL_DCHECK(false) << "Corrupted cleanup tag: " << static_cast<int>(tag);
      return sizeof(DynamicNode);
  }
}
```

</details>

### Reduce stats collection costs

Balance the utility of stats and other behavioral information about a system
against the cost of maintaining that information. The extra information can
often help people to understand and improve high-level behavior, but can also be
costly to maintain.

Stats that are not useful can be dropped altogether.

<details markdown="1">
<summary>
Stop maintaining expensive stats about number of alarms and
closures in SelectServer.
</summary>

Part of changes that reduce time for setting an alarm from 771 ns to 271 ns.

selectserver.h

{: .bad-code}
```c++
class SelectServer {
 public:
 ...
 protected:
  ...
  scoped_ptr<MinuteTenMinuteHourStat> num_alarms_stat_;
  ...
  scoped_ptr<MinuteTenMinuteHourStat> num_closures_stat_;
  ...
};
```

{: .new}
```c++
// Selectserver class
class SelectServer {
 ...
 protected:
 ...
};
```

/selectserver.cc

{: .bad-code}
```c++
void SelectServer::AddAlarmInternal(Alarmer* alarmer,
                                    int offset_in_ms,
                                    int id,
                                    bool is_periodic) {
                                    ...
  alarms_->insert(alarm);
  num_alarms_stat_->IncBy(1);
  ...
}
```

{: .new}
```c++
void SelectServer::AddAlarmInternal(Alarmer* alarmer,
                                    int offset_in_ms,
                                    int id,
                                    bool is_periodic) {
                                    ...
  alarms_->Add(alarm);
  ...
}
```

/selectserver.cc

{: .bad-code}
```c++
void SelectServer::RemoveAlarm(Alarmer* alarmer, int id) {
      ...
      alarms_->erase(alarm);
      num_alarms_stat_->IncBy(-1);
      ...
}
```

{: .new}
```c++
void SelectServer::RemoveAlarm(Alarmer* alarmer, int id) {
      ...
      alarms_->Remove(alarm);
      ...
}
```

</details>

Often, stats or other properties can be maintained for a sample of the elements
handled by the system (e.g., RPC requests, input records, users). Many
subsystems use this approach (tcmalloc allocation tracking, /requestz status
pages, Dapper samples).

When sampling, consider reducing the sampling rate when appropriate.

<details markdown="1">
<summary>
Maintain stats for just a sample of doc info requests.
</summary>

Sampling allows us to avoid touching 39 histograms and MinuteTenMinuteHour stats
for most requests.

generic-leaf-stats.cc

{: .bad-code}
```c++
... code that touches 39 histograms to update various stats on every request ...
```

{: .new}
```c++
// Add to the histograms periodically
if (TryLockToUpdateHistogramsDocInfo(docinfo_stats, bucket)) {
  // Returns true and grabs bucket->lock only if we should sample this
  // request for maintaining stats
  ... code that touches 39 histograms to update various stats ...
  bucket->lock.Unlock();
}
```

</details>

<details markdown="1">
<summary>
Reduce sampling rate and make faster sampling decisions.
</summary>

This change reduces the sampling rate from 1 in 10 to 1 in 32. Furthermore, we
now keep execution time stats just for the sampled events and speed up sampling
decisions by using a power of two modulus. This code is called on every packet
in the Google Meet video conferencing system and needed performance work to keep
up with capacity demands during the first part of the COVID outbreak as users
rapidly migrated to doing more online meetings.

packet_executor.cc

{: .bad-code}
```c++
class ScopedPerformanceMeasurement {
 public:
  explicit ScopedPerformanceMeasurement(PacketExecutor* packet_executor)
      : packet_executor_(packet_executor),
        tracer_(packet_executor->packet_executor_trace_threshold_,
                kClosureTraceName) {
    // ThreadCPUUsage is an expensive call. At the time of writing,
    // it takes over 400ns, or roughly 30 times slower than absl::Now,
    // so we sample only 10% of closures to keep the cost down.
    if (packet_executor->closures_executed_ % 10 == 0) {
      thread_cpu_usage_start_ = base::ThreadCPUUsage();
    }

    // Sample start time after potentially making the above expensive call,
    // so as not to pollute wall time measurements.
    run_start_time_ = absl::Now();
  }

  ~ScopedPerformanceMeasurement() {
```

{: .new}
```c++
ScopedPerformanceMeasurement::ScopedPerformanceMeasurement(
    PacketExecutor* packet_executor)
    : packet_executor_(packet_executor),
      tracer_(packet_executor->packet_executor_trace_threshold_,
              kClosureTraceName) {
  // ThreadCPUUsage is an expensive call. At the time of writing,
  // it takes over 400ns, or roughly 30 times slower than absl::Now,
  // so we sample only 1 in 32 closures to keep the cost down.
  if (packet_executor->closures_executed_ % 32 == 0) {
    thread_cpu_usage_start_ = base::ThreadCPUUsage();
  }

  // Sample start time after potentially making the above expensive call,
  // so as not to pollute wall time measurements.
  run_start_time_ = absl::Now();
}
```

packet_executor.cc

{: .bad-code}
```c++
~ScopedPerformanceMeasurement() {
  auto run_end_time = absl::Now();
  auto run_duration = run_end_time - run_start_time_;

  if (thread_cpu_usage_start_.has_value()) {
  ...
  }

  closure_execution_time->Record(absl::ToInt64Microseconds(run_duration));
```

{: .new}
```c++
ScopedPerformanceMeasurement::~ScopedPerformanceMeasurement() {
  auto run_end_time = absl::Now();
  auto run_duration = run_end_time - run_start_time_;

  if (thread_cpu_usage_start_.has_value()) {
    ...
    closure_execution_time->Record(absl::ToInt64Microseconds(run_duration));
  }
```

Benchmark results:

{: .bench}
```
Run on (40 X 2793 MHz CPUs); 2020-03-24T20:08:19.991412535-07:00
CPU: Intel Ivybridge with HyperThreading (20 cores) dL1:32KB dL2:256KB dL3:25MB
Benchmark                                      Base (ns)    New (ns) Improvement
----------------------------------------------------------------------------
BM_PacketOverhead_mean                               224          85    +62.0%
```

</details>

### Avoid logging on hot code paths

Logging statements can be costly, even if the logging-level for the statement
doesn't actually log anything. E.g., `ABSL_VLOG`'s implementation requires at
least a load and a comparison, which may be a problem in hot code paths. In
addition, the presence of the logging code may inhibit compiler optimizations.
Consider dropping logging entirely from hot code paths.

<details markdown="1">
<summary>
Remove logging from guts of memory allocator.
</summary>

This was a small part of a larger change.

gpu_bfc_allocator.cc

{: .bad-code}
```c++
void GPUBFCAllocator::SplitChunk(...) {
  ...
  VLOG(6) << "Adding to chunk map: " << new_chunk->ptr;
  ...
}
...
void GPUBFCAllocator::DeallocateRawInternal(void* ptr) {
  ...
  VLOG(6) << "Chunk at " << c->ptr << " no longer in use";
  ...
}
```

{: .new}
```c++
void GPUBFCAllocator::SplitChunk(...) {
...
}
...
void GPUBFCAllocator::DeallocateRawInternal(void* ptr) {
...
}
```

</details>

<details markdown="1">
<summary>
Precompute whether or not logging is enabled outside a
nested loop.
</summary>

image_similarity.cc

{: .bad-code}
```c++
for (int j = 0; j < output_subimage_size_y; j++) {
  int j1 = j - rad + output_to_integral_subimage_y;
  int j2 = j1 + 2 * rad + 1;
  // Create a pointer for this row's output, taking into account the offset
  // to the full image.
  double *image_diff_ptr = &(*image_diff)(j + min_j, min_i);

  for (int i = 0; i < output_subimage_size_x; i++) {
    ...
    if (VLOG_IS_ON(3)) {
    ...
    }
    ...
  }
}
```

{: .new}
```c++
const bool vlog_3 = DEBUG_MODE ? VLOG_IS_ON(3) : false;

for (int j = 0; j < output_subimage_size_y; j++) {
  int j1 = j - rad + output_to_integral_subimage_y;
  int j2 = j1 + 2 * rad + 1;
  // Create a pointer for this row's output, taking into account the offset
  // to the full image.
  double *image_diff_ptr = &(*image_diff)(j + min_j, min_i);

  for (int i = 0; i < output_subimage_size_x; i++) {
    ...
    if (vlog_3) {
    ...
    }
  }
}
```

{: .bench}
```
Run on (40 X 2801 MHz CPUs); 2016-05-16T15:55:32.250633072-07:00
CPU: Intel Ivybridge with HyperThreading (20 cores) dL1:32KB dL2:256KB dL3:25MB
Benchmark                          Base (ns)  New (ns) Improvement
------------------------------------------------------------------
BM_NCCPerformance/16                   29104     26372     +9.4%
BM_NCCPerformance/64                  473235    425281    +10.1%
BM_NCCPerformance/512               30246238  27622009     +8.7%
BM_NCCPerformance/1k              125651445  113361991     +9.8%
BM_NCCLimitedBoundsPerformance/16       8314      7498     +9.8%
BM_NCCLimitedBoundsPerformance/64     143508    132202     +7.9%
BM_NCCLimitedBoundsPerformance/512   9335684   8477567     +9.2%
BM_NCCLimitedBoundsPerformance/1k   37223897  34201739     +8.1%
```

</details>

<details markdown="1">
<summary>
Precompute whether logging is enabled and use the result
in helper routines.
</summary>

periodic_call.cc

{: .bad-code}
```c++
  VLOG(1) << Logid()
          << "MaybeScheduleAlarmAtNextTick. Time until next real time: "
          << time_until_next_real_time;
          ...
  uint64 next_virtual_time_ms =
      next_virtual_time_ms_ - num_ticks * kResolutionMs;
  CHECK_GE(next_virtual_time_ms, 0);
  ScheduleAlarm(now, delay, next_virtual_time_ms);
}

void ScheduleNextAlarm(uint64 current_virtual_time_ms)
    ABSL_EXCLUSIVE_LOCKS_REQUIRED(mutex_) {
  if (calls_.empty()) {
    VLOG(1) << Logid() << "No calls left, entering idle mode";
    next_real_time_ = absl::InfiniteFuture();
    return;
  }
  uint64 next_virtual_time_ms = FindNextVirtualTime(current_virtual_time_ms);
  auto delay =
      absl::Milliseconds(next_virtual_time_ms - current_virtual_time_ms);
  ScheduleAlarm(GetClock().TimeNow(), delay, next_virtual_time_ms);
}

// An alarm scheduled by this function supersedes all previously scheduled
// alarms. This is ensured through `scheduling_sequence_number_`.
void ScheduleAlarm(absl::Time now, absl::Duration delay,
                   uint64 virtual_time_ms)
    ABSL_EXCLUSIVE_LOCKS_REQUIRED(mutex_) {
  next_real_time_ = now + delay;
  next_virtual_time_ms_ = virtual_time_ms;
  ++ref_count_;  // The Alarm holds a reference.
  ++scheduling_sequence_number_;
  VLOG(1) << Logid() << "ScheduleAlarm. Time : "
          << absl::FormatTime("%M:%S.%E3f", now, absl::UTCTimeZone())
          << ", delay: " << delay << ", virtual time: " << virtual_time_ms
          << ", refs: " << ref_count_
          << ", seq: " << scheduling_sequence_number_
          << ", executor: " << executor_;

  executor_->AddAfter(
      delay, new Alarm(this, virtual_time_ms, scheduling_sequence_number_));
}
```

{: .new}
```c++
  const bool vlog_1 = VLOG_IS_ON(1);

  if (vlog_1) {
    VLOG(1) << Logid()
            << "MaybeScheduleAlarmAtNextTick. Time until next real time: "
            << time_until_next_real_time;
  }
  ...
  uint64 next_virtual_time_ms =
      next_virtual_time_ms_ - num_ticks * kResolutionMs;
  CHECK_GE(next_virtual_time_ms, 0);
  ScheduleAlarm(now, delay, next_virtual_time_ms, vlog_1);
}

void ScheduleNextAlarm(uint64 current_virtual_time_ms, bool vlog_1)
    ABSL_EXCLUSIVE_LOCKS_REQUIRED(mutex_) {
  if (calls_.empty()) {
    if (vlog_1) {
      VLOG(1) << Logid() << "No calls left, entering idle mode";
    }
    next_real_time_ = absl::InfiniteFuture();
    return;
  }
  uint64 next_virtual_time_ms = FindNextVirtualTime(current_virtual_time_ms);
  auto delay =
      absl::Milliseconds(next_virtual_time_ms - current_virtual_time_ms);
  ScheduleAlarm(GetClock().TimeNow(), delay, next_virtual_time_ms, vlog_1);
}

// An alarm scheduled by this function supersedes all previously scheduled
// alarms. This is ensured through `scheduling_sequence_number_`.
void ScheduleAlarm(absl::Time now, absl::Duration delay,
                   uint64 virtual_time_ms,
                   bool vlog_1)
    ABSL_EXCLUSIVE_LOCKS_REQUIRED(mutex_) {
  next_real_time_ = now + delay;
  next_virtual_time_ms_ = virtual_time_ms;
  ++ref_count_;  // The Alarm holds a reference.
  ++scheduling_sequence_number_;
  if (vlog_1) {
    VLOG(1) << Logid() << "ScheduleAlarm. Time : "
            << absl::FormatTime("%M:%S.%E3f", now, absl::UTCTimeZone())
            << ", delay: " << delay << ", virtual time: " << virtual_time_ms
            << ", refs: " << ref_count_
            << ", seq: " << scheduling_sequence_number_
            << ", executor: " << executor_;
  }

  executor_->AddAfter(
      delay, new Alarm(this, virtual_time_ms, scheduling_sequence_number_));
}
```

</details>

## Code size considerations {#code-size-considerations}

Performance encompasses more than just runtime speed. Sometimes it is worth
considering the effects of software choices on the size of generated code. Large
code size means longer compile and link times, bloated binaries, more memory
usage, more icache pressure, and other sometimes negative effects on
microarchitectural structures like branch predictors, etc.
Thinking about these issues is especially important when writing low-level
library code that will be used in many places, or when writing templated code
that you expect will be instantiated for many different types.

The techniques that are useful for reducing code size vary significantly across
programming languages. Here are some techniques that we have found useful for
C++ code (which can suffer from an over-use of templates and inlining).

### Trim commonly inlined code

Widely called functions combined with inlining can have a dramatic effect on
code size.

<details markdown="1">
<summary>
Speed up TF_CHECK_OK.
</summary>

Avoid creating Ok object, and save code space by doing complex formatting of
fatal error message out of line instead of at every call site.

status.h

{: .bad-code}
```c++
#define TF_CHECK_OK(val) CHECK_EQ(::tensorflow::Status::OK(), (val))
#define TF_QCHECK_OK(val) QCHECK_EQ(::tensorflow::Status::OK(), (val))
```

{: .new}
```c++
extern tensorflow::string* TfCheckOpHelperOutOfLine(
    const ::tensorflow::Status& v, const char* msg);
inline tensorflow::string* TfCheckOpHelper(::tensorflow::Status v,
                                           const char* msg) {
  if (v.ok()) return nullptr;
  return TfCheckOpHelperOutOfLine(v, msg);
}
#define TF_CHECK_OK(val)                                           \
  while (tensorflow::string* _result = TfCheckOpHelper(val, #val)) \
  LOG(FATAL) << *(_result)
#define TF_QCHECK_OK(val)                                          \
  while (tensorflow::string* _result = TfCheckOpHelper(val, #val)) \
  LOG(QFATAL) << *(_result)
```

status.cc

{: .new}
```c++
string* TfCheckOpHelperOutOfLine(const ::tensorflow::Status& v,
                                 const char* msg) {
  string r("Non-OK-status: ");
  r += msg;
  r += " status: ";
  r += v.ToString();
  // Leaks string but this is only to be used in a fatal error message
  return new string(r);
}
```

</details>

<details markdown="1">
<summary>
Shrink each RETURN_IF_ERROR call site by 79 bytes of
code.
</summary>

1.  Added special adaptor class for use by just RETURN_IF_ERROR.
2.  Do not construct/destruct StatusBuilder on fast path of RETURN_IF_ERROR.
3.  Do not inline some StatusBuilder methods since they are now no longer needed
    on the fast path.
4.  Avoid unnecessary ~Status call.

</details>

<details markdown="1">
<summary>
Improve performance of CHECK_GE by 4.5X and shrink code
size from 125 bytes to 77 bytes.
</summary>

logging.h

{: .bad-code}
```c++
struct CheckOpString {
  CheckOpString(string* str) : str_(str) { }
  ~CheckOpString() { delete str_; }
  operator bool() const { return str_ == NULL; }
  string* str_;
};
...
#define DEFINE_CHECK_OP_IMPL(name, op) \
  template <class t1, class t2> \
  inline string* Check##name##Impl(const t1& v1, const t2& v2, \
                                   const char* names) { \
    if (v1 op v2) return NULL; \
    else return MakeCheckOpString(v1, v2, names); \
  } \
  string* Check##name##Impl(int v1, int v2, const char* names);
DEFINE_CHECK_OP_IMPL(EQ, ==)
DEFINE_CHECK_OP_IMPL(NE, !=)
DEFINE_CHECK_OP_IMPL(LE, <=)
DEFINE_CHECK_OP_IMPL(LT, < )
DEFINE_CHECK_OP_IMPL(GE, >=)
DEFINE_CHECK_OP_IMPL(GT, > )
#undef DEFINE_CHECK_OP_IMPL
```

{: .new}
```c++
struct CheckOpString {
  CheckOpString(string* str) : str_(str) { }
  // No destructor: if str_ is non-NULL, we're about to LOG(FATAL),
  // so there's no point in cleaning up str_.
  operator bool() const { return str_ == NULL; }
  string* str_;
};
...
extern string* MakeCheckOpStringIntInt(int v1, int v2, const char* names);

template<int, int>
string* MakeCheckOpString(const int& v1, const int& v2, const char* names) {
  return MakeCheckOpStringIntInt(v1, v2, names);
}
...
#define DEFINE_CHECK_OP_IMPL(name, op) \
  template <class t1, class t2> \
  inline string* Check##name##Impl(const t1& v1, const t2& v2, \
                                   const char* names) { \
    if (v1 op v2) return NULL; \
    else return MakeCheckOpString(v1, v2, names); \
  } \
  inline string* Check##name##Impl(int v1, int v2, const char* names) { \
    if (v1 op v2) return NULL; \
    else return MakeCheckOpString(v1, v2, names); \
  }
DEFINE_CHECK_OP_IMPL(EQ, ==)
DEFINE_CHECK_OP_IMPL(NE, !=)
DEFINE_CHECK_OP_IMPL(LE, <=)
DEFINE_CHECK_OP_IMPL(LT, < )
DEFINE_CHECK_OP_IMPL(GE, >=)
DEFINE_CHECK_OP_IMPL(GT, > )
#undef DEFINE_CHECK_OP_IMPL
```

logging.cc

{: .new}
```c++
string* MakeCheckOpStringIntInt(int v1, int v2, const char* names) {
  strstream ss;
  ss << names << " (" << v1 << " vs. " << v2 << ")";
  return new string(ss.str(), ss.pcount());
}
```

</details>

### Inline with care

Inlining can often improve performance, but sometimes it can increase code size
without a corresponding performance payoff (and in some case even a performance
loss due to increased instruction cache pressure).

<details markdown="1">
<summary>
Reduce inlining in TensorFlow.
</summary>

The change stops inlining many non-performance-sensitive functions (e.g., error
paths and op registration code). Furthermore, slow paths of some
performance-sensitive functions are moved into non-inlined functions.

These changes reduces the size of tensorflow symbols in a typical binary by
</details>

<details markdown="1">
<summary>
Protocol buffer library change. Avoid expensive inlined
code space for encoding message length for messages &ge; 128 bytes and instead
do a procedure call to a shared out-of-line routine.
</summary>

Not only makes important large binaries smaller but also faster.

Bytes of generated code per line of a heavily inlined routine in one large
binary. First number represents the total bytes generated for a particular
source line including all locations where that code has been inlined.

Before:

{: .bad-code}
```c++
.           0   1825 template <typename MessageType>
.           0   1826 inline uint8* WireFormatLite::InternalWriteMessage(
.           0   1827     int field_number, const MessageType& value, uint8* target,
.           0   1828     io::EpsCopyOutputStream* stream) {
>>>    389246   1829   target = WriteTagToArray(field_number, WIRETYPE_LENGTH_DELIMITED, target);
>>>   5454640   1830   target = io::CodedOutputStream::WriteVarint32ToArray(
>>>    337837   1831       static_cast<uint32>(value.GetCachedSize()), target);
>>>   1285539   1832   return value._InternalSerialize(target, stream);
.           0   1833 }
```

The new codesize output with this change looks like:

{: .new}
```c++
.           0   1825 template <typename MessageType>
.           0   1826 inline uint8* WireFormatLite::InternalWriteMessage(
.           0   1827     int field_number, const MessageType& value, uint8* target,
.           0   1828     io::EpsCopyOutputStream* stream) {
>>>    450612   1829   target = WriteTagToArray(field_number, WIRETYPE_LENGTH_DELIMITED, target);
>>       9609   1830   target = io::CodedOutputStream::WriteVarint32ToArrayOutOfLine(
>>>    434668   1831       static_cast<uint32>(value.GetCachedSize()), target);
>>>   1597394   1832   return value._InternalSerialize(target, stream);
.           0   1833 }
```

coded_stream.h

{: .new}
```c++
class PROTOBUF_EXPORT CodedOutputStream {
  ...
  // Like WriteVarint32()  but writing directly to the target array, and with the
  // less common-case paths being out of line rather than inlined.
  static uint8* WriteVarint32ToArrayOutOfLine(uint32 value, uint8* target);
  ...
};
...
inline uint8* CodedOutputStream::WriteVarint32ToArrayOutOfLine(uint32 value,
                                                               uint8* target) {
  target[0] = static_cast<uint8>(value);
  if (value < 0x80) {
    return target + 1;
  } else {
    return WriteVarint32ToArrayOutOfLineHelper(value, target);
  }
}
```

coded_stream.cc

{: .new}
```c++
uint8* CodedOutputStream::WriteVarint32ToArrayOutOfLineHelper(uint32 value,
                                                              uint8* target) {
  DCHECK_GE(value, 0x80);
  target[0] |= static_cast<uint8>(0x80);
  value >>= 7;
  target[1] = static_cast<uint8>(value);
  if (value < 0x80) {
    return target + 2;
  }
  target += 2;
  do {
    // Turn on continuation bit in the byte we just wrote.
    target[-1] |= static_cast<uint8>(0x80);
    value >>= 7;
    *target = static_cast<uint8>(value);
    ++target;
  } while (value >= 0x80);
  return target;
}
```

</details>

<details markdown="1">
<summary>
Reduce absl::flat_hash_set and absl::flat_hash_map code
size.
</summary>

1.  Extract code that does not depend on the specific hash table type into
    common (non-inlined) functions.
2.  Place ABSL_ATTRIBUTE_NOINLINE directives judiciously.
3.  Out-of-line some slow paths.

</details>

<details markdown="1">
<summary>
Do not inline string allocation and deallocation when not
using protobuf arenas.
</summary>

public/arenastring.h

{: .bad-code}
```c++
  if (IsDefault(default_value)) {
    std::string* new_string = new std::string();
    tagged_ptr_.Set(new_string);
    return new_string;
  } else {
    return UnsafeMutablePointer();
  }
}
```

{: .new}
```c++
  if (IsDefault(default_value)) {
    return SetAndReturnNewString();
  } else {
    return UnsafeMutablePointer();
  }
}
```

internal/arenastring.cc

{: .new}
```c++
std::string* ArenaStringPtr::SetAndReturnNewString() {
  std::string* new_string = new std::string();
  tagged_ptr_.Set(new_string);
  return new_string;
}
```

</details>

<details markdown="1">
<summary>
Avoid inlining some routines. Create variants of routines
that take 'const char\*' rather than 'const std::string&' to avoid std::string
construction code at every call site.
</summary>

op.h

{: .bad-code}
```c++
class OpDefBuilderWrapper {
 public:
  explicit OpDefBuilderWrapper(const char name[]) : builder_(name) {}
  OpDefBuilderWrapper& Attr(std::string spec) {
    builder_.Attr(std::move(spec));
    return *this;
  }
  OpDefBuilderWrapper& Input(std::string spec) {
    builder_.Input(std::move(spec));
    return *this;
  }
  OpDefBuilderWrapper& Output(std::string spec) {
    builder_.Output(std::move(spec));
    return *this;
  }
```

{: .new}
```c++
class OpDefBuilderWrapper {
 public:
  explicit OpDefBuilderWrapper(const char name[]) : builder_(name) {}
  OpDefBuilderWrapper& Attr(std::string spec) {
    builder_.Attr(std::move(spec));
    return *this;
  }
  OpDefBuilderWrapper& Attr(const char* spec) TF_ATTRIBUTE_NOINLINE {
    return Attr(std::string(spec));
  }
  OpDefBuilderWrapper& Input(std::string spec) {
    builder_.Input(std::move(spec));
    return *this;
  }
  OpDefBuilderWrapper& Input(const char* spec) TF_ATTRIBUTE_NOINLINE {
    return Input(std::string(spec));
  }
  OpDefBuilderWrapper& Output(std::string spec) {
    builder_.Output(std::move(spec));
    return *this;
  }
  OpDefBuilderWrapper& Output(const char* spec) TF_ATTRIBUTE_NOINLINE {
    return Output(std::string(spec));
  }
```

</details>

### Reduce template instantiations

Templated code can be duplicated for every possible combination of template
arguments which which it is instantiated.

<details markdown="1">
<summary>
Replace template argument with a regular argument.
</summary>

Changed a large routine templated on a bool to instead take the bool as an extra
argument. (The bool was only being used once to select one of two string
constants, so a run-time check was just fine.) This reduced the # of
instantiations of the large routine from 287 to 143.

sharding_util_ops.cc

{: .bad-code}
```c++
template <bool Split>
Status GetAndValidateAttributes(OpKernelConstruction* ctx,
                                std::vector<int32>& num_partitions,
                                int& num_slices, std::vector<int32>& paddings,
                                bool& has_paddings) {
  absl::string_view num_partitions_attr_name =
      Split ? kNumSplitsAttrName : kNumConcatsAttrName;
      ...
  return OkStatus();
}
```

{: .new}
```c++
Status GetAndValidateAttributes(bool split, OpKernelConstruction* ctx,
                                std::vector<int32>& num_partitions,
                                int& num_slices, std::vector<int32>& paddings,
                                bool& has_paddings) {
  absl::string_view num_partitions_attr_name =
      split ? kNumSplitsAttrName : kNumConcatsAttrName;
      ...
  return OkStatus();
}
```

</details>

<details markdown="1">
<summary>
Move bulky code from templated constructor to a
non-templated shared base class constructor.
</summary>

Also reduce number of template instantiations from one for every combination of
`<T, Device, Rank>` to one for every `<T>` and every `<Rank>`.

sharding_util_ops.cc

{: .bad-code}
```c++
template <typename Device, typename T>
class XlaSplitNDBaseOp : public OpKernel {
 public:
  explicit XlaSplitNDBaseOp(OpKernelConstruction* ctx) : OpKernel(ctx) {
    OP_REQUIRES_OK(
        ctx, GetAndValidateAttributes(/*split=*/true, ctx, num_splits_,
                                      num_slices_, paddings_, has_paddings_));
  }
```

{: .new}
```c++
// Shared base class to save code space
class XlaSplitNDShared : public OpKernel {
 public:
  explicit XlaSplitNDShared(OpKernelConstruction* ctx) TF_ATTRIBUTE_NOINLINE
      : OpKernel(ctx),
        num_slices_(1),
        has_paddings_(false) {
    GetAndValidateAttributes(/*split=*/true, ctx, num_splits_, num_slices_,
                             paddings_, has_paddings_);
  }
```

</details>

<details markdown="1">
<summary>
Reduce generated code size for absl::flat_hash_set and
absl::flat_hash_map.
</summary>

*   Extract code that does not depend on the specific hash table type into
    common (non-inlined) functions.
*   Place ABSL_ATTRIBUTE_NOINLINE directives judiciously.
*   Move some slow paths out of line.

</details>

### Reduce container operations

Consider the impact of map and other container operations since each call to
such and operation can produce large amounts of generated code.

<details markdown="1">
<summary>
Turn many map insertion calls in a row to initialize a
hash table of emoji characters into a single bulk insert operation (188KB of
text down to 360 bytes in library linked into many binaries). 😊
</summary>

textfallback_init.h

{: .bad-code}
```c++
inline void AddEmojiFallbacks(TextFallbackMap *map) {
  (*map)[0xFE000] = &kFE000;
  (*map)[0xFE001] = &kFE001;
  (*map)[0xFE002] = &kFE002;
  (*map)[0xFE003] = &kFE003;
  (*map)[0xFE004] = &kFE004;
  (*map)[0xFE005] = &kFE005;
  ...
  (*map)[0xFEE7D] = &kFEE7D;
  (*map)[0xFEEA0] = &kFEEA0;
  (*map)[0xFE331] = &kFE331;
};
```

{: .new}
```c++
inline void AddEmojiFallbacks(TextFallbackMap *map) {
#define PAIR(x) {0x##x, &k##x}
  // clang-format off
  map->insert({
    PAIR(FE000),
    PAIR(FE001),
    PAIR(FE002),
    PAIR(FE003),
    PAIR(FE004),
    PAIR(FE005),
    ...
    PAIR(FEE7D),
    PAIR(FEEA0),
    PAIR(FE331)});
  // clang-format on
#undef PAIR
};
```

</details>

<details markdown="1">
<summary>
Stop inlining a heavy user of InlinedVector operations.
</summary>

Moved very long routine that was being inlined from .h file to .cc (no real
performance benefit from inlining this).

reduction_ops_common.h

{: .bad-code}
```c++
Status Simplify(const Tensor& data, const Tensor& axis,
                const bool keep_dims) {
  ... Eighty line routine body ...
}
```

{: .new}
```c++
Status Simplify(const Tensor& data, const Tensor& axis, const bool keep_dims);
```

</details>

## Parallelization and synchronization {#parallelization-and-synchronization}

### Exploit Parallelism {#exploit-parallelism}

Modern machines have many cores, and they are often underutilized. Expensive
work may therefore be completed faster by parallelizing it. The most common
approach is to process different items in parallel and combine the results when
done. Typically, the items are first partitioned into batches to avoid paying
the cost of running something in parallel per item.

<details markdown="1">
<summary>
Improves the rate of encoding tokens by ~3.6x with four-way
parallelization.
</summary>

blocked-token-coder.cc

{: .new}
```c++
MutexLock l(&encoder_threads_lock);
if (encoder_threads == NULL) {
  encoder_threads = new ThreadPool(NumCPUs());
  encoder_threads->SetStackSize(262144);
  encoder_threads->StartWorkers();
}
encoder_threads->Add
    (NewCallback(this,
                 &BlockedTokenEncoder::EncodeRegionInThread,
                 region_tokens, N, region,
                 stats,
                 controller_->GetClosureWithCost
                 (NewCallback(&DummyCallback), N)));
```

</details>

<details markdown="1">
<summary>
Parallelization improves decoding performance by 5x.
</summary>

coding.cc

{: .bad-code}
```c++
for (int c = 0; c < clusters->size(); c++) {
  RET_CHECK_OK(DecodeBulkForCluster(...);
}
```

{: .new}
```c++
struct SubTask {
  absl::Status result;
  absl::Notification done;
};

std::vector<SubTask> tasks(clusters->size());
for (int c = 0; c < clusters->size(); c++) {
  options_.executor->Schedule([&, c] {
    tasks[c].result = DecodeBulkForCluster(...);
    tasks[c].done.Notify();
  });
}
for (int c = 0; c < clusters->size(); c++) {
  tasks[c].done.WaitForNotification();
}
for (int c = 0; c < clusters->size(); c++) {
  RETURN_IF_ERROR(tasks[c].result);
}
```

</details>

The effect on system performance should be measured carefully – if spare CPU is
not available, or if memory bandwidth is saturated, parallelization may not
help, or may even hurt.

### Amortize Lock Acquisition {#amortize-lock-acquisition}

Avoid fine-grained locking to reduce the cost of Mutex operations in hot paths.
Caveat: this should only be done if the change does not increase lock
contention.

<details markdown="1">
<summary>
Acquire lock once to free entire tree of query nodes, rather
than reacquiring lock for every node in tree.
</summary>

mustang-query.cc

{: .bad-code}
```c++
// Pool of query nodes
ThreadSafeFreeList<MustangQuery> pool_(256);
...
void MustangQuery::Release(MustangQuery* node) {
  if (node == NULL)
    return;
  for (int i=0; i < node->children_->size(); ++i)
    Release((*node->children_)[i]);
  node->children_->clear();
  pool_.Delete(node);
}
```

{: .new}
```c++
// Pool of query nodes
Mutex pool_lock_;
FreeList<MustangQuery> pool_(256);
...
void MustangQuery::Release(MustangQuery* node) {
  if (node == NULL)
    return;
  MutexLock l(&pool_lock_);
  ReleaseLocked(node);
}

void MustangQuery::ReleaseLocked(MustangQuery* node) {
#ifndef NDEBUG
  pool_lock_.AssertHeld();
#endif
  if (node == NULL)
    return;
  for (int i=0; i < node->children_->size(); ++i)
    ReleaseLocked((*node->children_)[i]);
  node->children_->clear();
  pool_.Delete(node);
}
```

</details>

### Keep critical sections short {#keep-critical-sections-short}

Avoid expensive work inside critical sections. In particular, watch out for
innocuous looking code that might be doing RPCs or accessing
files.

<details markdown="1">
<summary>
Reduce number of cache lines touched in critical section.
</summary>

Careful data structure adjustments reduce the number of cache lines accessed
significantly and improve the performance of an ML training run by 3.3%.

1.  Precompute some per-node type properties as bits within the NodeItem data
    structure, meaning that we can avoid touching the Node* object for outgoing
    edges in the critical section.
2.  Change ExecutorState::ActivateNodes to use the NodeItem of the destination
    node for each outgoing edge, rather than touching fields in the *item->node
    object. Typically this means that we touch 1 or 2 cache lines total for
    accessing the needed edge data, rather than `~2 + O(num_outgoing edges)`
    (and for large graphs with many cores executing them there is also less TLB
    pressure).

</details>

<details markdown="1">
<summary>
Avoid RPC while holding Mutex.
</summary>

trainer.cc

{: .bad-code}
```c++
{
  // Notify the parameter server that we are starting.
  MutexLock l(&lock_);
  model_ = model;
  MaybeRecordProgress(last_global_step_);
}
```

{: .new}
```c++
bool should_start_record_progress = false;
int64 step_for_progress = -1;
{
  // Notify the parameter server that we are starting.
  MutexLock l(&lock_);
  model_ = model;
  should_start_record_progress = ShouldStartRecordProgress();
  step_for_progress = last_global_step_;
}
if (should_start_record_progress) {
  StartRecordProgress(step_for_progress);
}
```

</details>

Also, be wary of expensive destructors that will run before a Mutex is unlocked
(this can often happen when the Mutex unlock is triggered by a `~MutexUnlock`.)
Declaring objects with expensive destructors before MutexLock may help (assuming
it is thread-safe).

### Reduce contention by sharding {#reduce-contention-by-sharding}

Sometimes a data structure protected by a Mutex that is exhibiting high
contention can be safely split into multiple shards, each shard with its own
Mutex. (Note: this requires that there are no cross-shard invariants between the
different shards.)

<details markdown="1">
<summary>
Shards a cache 16 ways which improves throughput under a
multi-threaded load by ~2x.
</summary>

cache.cc

{: .new}
```c++
class ShardedLRUCache : public Cache {
 private:
  LRUCache shard_[kNumShards];
  port::Mutex id_mutex_;
  uint64_t last_id_;

  static inline uint32_t HashSlice(const Slice& s) {
    return Hash(s.data(), s.size(), 0);
  }

  static uint32_t Shard(uint32_t hash) {
    return hash >> (32 - kNumShardBits);
  }
  ...
  virtual Handle* Lookup(const Slice& key) {
    const uint32_t hash = HashSlice(key);
    return shard_[Shard(hash)].Lookup(key, hash);
  }
```

</details>

<details markdown="1">
<summary>
Shards spanner data structure for tracking calls.
</summary>

transaction_manager.cc

{: .bad-code}
```c++
absl::MutexLock l(&active_calls_in_mu_);
ActiveCallMap::const_iterator iter = active_calls_in_.find(m->tid());
if (iter != active_calls_in_.end()) {
  iter->second.ExtractElements(&m->tmp_calls_);
}
```

{: .new}
```c++
ActiveCalls::LockedShard shard(active_calls_in_, m->tid());
const ActiveCallMap& active_calls_map = shard.active_calls_map();
ActiveCallMap::const_iterator iter = active_calls_map.find(m->tid());
if (iter != active_calls_map.end()) {
  iter->second.ExtractElements(&m->tmp_calls_);
}
```

</details>

If the data structure in question is a map, consider using a concurrent hash map
implementation instead.

Be careful with the information used for shard selection. If, for example, you
use some bits of a hash value for shard selection and then those same bits end
up being used again later, the latter use may perform poorly since it sees a
skewed distribution of hash values.

<details markdown="1">
<summary>
Fix information used for shard selection to prevent hash
table issues.
</summary>

netmon_map_impl.h

{: .bad-code}
```c++
ConnectionBucket* GetBucket(Index index) {
  // Rehash the hash to make sure we are not partitioning the buckets based on
  // the original hash. If num_buckets_ is a power of 2 that would drop the
  // entropy of the buckets.
  size_t original_hash = absl::Hash<Index>()(index);
  int hash = absl::Hash<size_t>()(original_hash) % num_buckets_;
  return &buckets_[hash];
}
```

{: .new}
```c++
ConnectionBucket* GetBucket(Index index) {
  absl::Hash<std::pair<Index, size_t>> hasher{};
  // Combine the hash with 42 to prevent shard selection using the same bits
  // as the underlying hashtable.
  return &buckets_[hasher({index, 42}) % num_buckets_];
}
```

</details>

<details markdown="1">
<summary>
Shard Spanner data structure used for tracking calls.
</summary>

This CL partitions the ActiveCallMap into 64 shards. Each shard is protected by
a separate mutex. A given transaction will be mapped to exactly one shard. A new
interface LockedShard(tid) is added for accessing the ActiveCallMap for a
transaction in a thread-safe manner. Example usage:

transaction_manager.cc

{: .bad-code}
```c++
{
  absl::MutexLock l(&active_calls_in_mu_);
  delayed_locks_timer_ring_.Add(delayed_locks_flush_time_ms, tid);
}
```

{: .new}
```c++
{
  ActiveCalls::LockedShard shard(active_calls_in_, tid);
  shard.delayed_locks_timer_ring().Add(delayed_locks_flush_time_ms, tid);
}
```

The results show a 69% reduction in overall wall-clock time when running the
benchmark with 8192 fibers

{: .bad-code}
```
Benchmark                   Time(ns)        CPU(ns)     Iterations
------------------------------------------------------------------
BM_ActiveCalls/8k        11854633492     98766564676            10
BM_ActiveCalls/16k       26356203552    217325836709            10
```

{: .new}
```
Benchmark                   Time(ns)        CPU(ns)     Iterations
------------------------------------------------------------------
BM_ActiveCalls/8k         3696794642     39670670110            10
BM_ActiveCalls/16k        7366284437     79435705713            10
```

</details>

### SIMD Instructions {#simd-instructions}

Explore whether handling multiple items at once using
[SIMD](https://en.wikipedia.org/wiki/Single_instruction,_multiple_data)
instructions available on modern CPUs can give speedups (e.g., see
`absl::flat_hash_map` discussion below in [Bulk Operations](#bulk-operations)
section).

### Reduce false sharing {#reduce-false-sharing}

If different threads access different mutable data, consider placing the
different data items on different cache lines, e.g., in C++ using the `alignas`
directive. However, these directives are easy to misuse and may increase object
sizes significantly, so make sure performance measurements justify their use.

<details markdown="1">
<summary>
Segregate commonly mutated fields in a different cache
line than other fields.
</summary>

histogram.h

{: .bad-code}
```c++
HistogramOptions options_;
...
internal::HistogramBoundaries *boundaries_;
...
std::vector<double> buckets_;

double min_;             // Minimum.
double max_;             // Maximum.
double count_;           // Total count of occurrences.
double sum_;             // Sum of values.
double sum_of_squares_;  // Sum of squares of values.
...
RegisterVariableExporter *exporter_;
```

{: .new}
```c++
  HistogramOptions options_;
  ...
  internal::HistogramBoundaries *boundaries_;
  ...
  RegisterVariableExporter *exporter_;
  ...
  // Place the following fields in a dedicated cacheline as they are frequently
  // mutated, so we can avoid potential false sharing.
  ...
#ifndef SWIG
  alignas(ABSL_CACHELINE_SIZE)
#endif
  std::vector<double> buckets_;

  double min_;             // Minimum.
  double max_;             // Maximum.
  double count_;           // Total count of occurrences.
  double sum_;             // Sum of values.
  double sum_of_squares_;  // Sum of squares of values.
```

</details>

### Reduce frequency of context switches

<details markdown="1">
<summary>
Process small work items inline instead of on device
thread pool.
</summary>

cast_op.cc

{: .new}
```c++
template <typename Device, typename Tout, typename Tin>
void CastMaybeInline(const Device& d, typename TTypes<Tout>::Flat o,
                     typename TTypes<Tin>::ConstFlat i) {
  if (o.size() * (sizeof(Tin) + sizeof(Tout)) < 16384) {
    // Small cast on a CPU: do inline
    o = i.template cast<Tout>();
  } else {
    o.device(d) = i.template cast<Tout>();
  }
}
```

</details>

### Use buffered channels for pipelining {#use-buffered-channels-for-pipelining}

Channels can be unbuffered which means that a writer blocks until a reader is
ready to pick up an item. Unbuffered channels can be useful when the channel is
being used for synchronization, but not when the channel is being used to
increase parallelism.

### Consider lock-free approaches

Sometimes lock-free data structures can make a difference over more conventional
mutex-protected data structures. However, direct atomic variable manipulation
can be [dangerous][atomic danger]. Prefer higher-level abstractions.

<details markdown="1">
<summary>
Use lock-free map to manage a cache of RPC channels.
</summary>

Entries in an RPC stub cache are read thousands of times a second and modified
rarely. Switching to an appropriate lock-free map reduces search latency by
</details>

<details markdown="1">
<summary>
Use a fixed lexicon+lock-free hash map to speed-up
determining IsValidTokenId.
</summary>

dynamic_token_class_manager.h

{: .bad-code}
```c++
mutable Mutex mutex_;

// The density of this hash map is guaranteed by the fact that the
// dynamic lexicon reuses previously allocated TokenIds before trying
// to allocate new ones.
dense_hash_map<TokenId, common::LocalTokenClassId> tid_to_cid_
    GUARDED_BY(mutex_);
```

{: .new}
```c++
// Read accesses to this hash-map should be done using
// 'epoch_gc_'::(EnterFast / LeaveFast). The writers should periodically
// GC the deleted entries, by simply invoking LockFreeHashMap::CreateGC.
typedef util::gtl::LockFreeHashMap<TokenId, common::LocalTokenClassId>
    TokenIdTokenClassIdMap;
TokenIdTokenClassIdMap tid_to_cid_;
```

</details>

## Protocol Buffer advice {#protobuf-advice}

Protobufs are a convenient representation of data, especially if the data will
be sent over the wire or stored persistently. However, they can have significant
performance costs. For example, a piece of code that fills in a list of 1000
points and then sums up the Y coordinates, speeds up by a **factor of 20** when
converted from protobufs to a C++ std::vector of structs!

<details markdown="1">
<summary>
Benchmark code for both versions.
</summary>

{: .bench}
```
name                old time/op  new time/op  delta
BenchmarkIteration  17.4µs ± 5%   0.8µs ± 1%  -95.30%  (p=0.000 n=11+12)
```

Protobuf version:

{: .bad-code}
```proto
message PointProto {
  int32 x = 1;
  int32 y = 2;
}
message PointListProto {
  repeated PointProto points = 1;
}
```

{: .bad-code}
```c++
void SumProto(const PointListProto& vec) {
  int sum = 0;
  for (const PointProto& p : vec.points()) {
    sum += p.y();
  }
  ABSL_VLOG(1) << sum;
}

void BenchmarkIteration() {
  PointListProto points;
  points.mutable_points()->Reserve(1000);
  for (int i = 0; i < 1000; i++) {
    PointProto* p = points.add_points();
    p->set_x(i);
    p->set_y(i * 2);
  }
  SumProto(points);
}
```

Non-protobuf version:

{: .new}
```c++
struct PointStruct {
  int x;
  int y;
};

void SumVector(const std::vector<PointStruct>& vec) {
  int sum = 0;
  for (const PointStruct& p : vec) {
    sum += p.y;
  }
  ABSL_VLOG(1) << sum;
}

void BenchmarkIteration() {
  std::vector<PointStruct> points;
  points.reserve(1000);
  for (int i = 0; i < 1000; i++) {
    points.push_back({i, i * 2});
  }
  SumVector(points);
}
```

</details>

In addition, the protobuf version adds a few kilobytes of code and data to the
binary, which may not seem like much, but adds up quickly in systems with many
protobuf types. This increased size creates performance problems by creating
i-cache and d-cache pressure.

Here are some tips related to protobuf performance:

<details markdown="1">
<summary>
Do not use protobufs unnecessarily.
</summary>

Given the factor of 20 performance difference described above, if some data is
never serialized or parsed, you probably should not put it in a protocol buffer.
The purpose of protocol buffers is to make it easy to serialize and deserialize
data structures, but they can have significant code-size, memory, and CPU
overheads. Do not use them if all you want are some of the other niceties like
</details>

<details markdown="1">
<summary>
Avoid unnecessary message hierarchies.
</summary>

Message hierarchy can be useful to organize information in a more readable
fashion. However, the extra level of message hierarchy incurs overheads like
memory allocations, function calls, cache misses, larger serialized messages,
etc.

E.g., instead of:

{: .bad-code}
```proto
message Foo {
  optional Bar bar = 1;
}
message Bar {
  optional Baz baz = 1;
}
message Baz {
  optional int32 count = 1;
}
```

Prefer:

{: .new}
```proto
message Foo {
  optional int32 count = 1;
}
```

A protocol buffer message corresponds to a message class in C++ generated code
and emits a tag and the length of the payload on the wire. To carry an integer,
the old form requires more allocations (and deallocations) and emits a larger
amount of generated code. As a result, all protocol buffer operations (parsing,
serialization, size, etc.) become more expensive, having to traverse the message
</details>

<details markdown="1">
<summary>
Use small field numbers for frequently occurring fields.
</summary>

Protobufs use a variable length integer representation for the combination of
field number and wire format (see the
[protobuf encoding documentation](https://protobuf.dev/programming-guides/encoding/)).
This representation is 1 byte for field numbers between 1 and 15, and two bytes
for field numbers between 16 and 2047. (Field numbers 2048 or greater should
typically be avoided.)

Consider pre-reserving some small field numbers for future extension of
</details>

<details markdown="1">
<summary>
Choose carefully between int32, sint32, fixed32, and uint32 (and
similarly for the 64 bit variants).
</summary>

Generally, use `int32` or `int64`, but use `fixed32` or `fixed64` for large
values like hash codes and `sint32` or `sint64` for values are that are often
negative.

A varint occupies fewer bytes to encode small integers and can save space at the
cost of more expensive decoding. However, it can take up more space for negative
or large values. In that case, using fixed32 or fixed64 (instead of uint32 or
uint64) reduces size with much cheaper encoding and decoding. For small negative
</details>

<details markdown="1">
<summary>
For proto2, pack repeated numeric fields by annotating them with
<code>[packed=true]</code>.
</summary>

In proto2, repeated values are serialized as a sequence of (tag, value) pairs by
default. This is inefficient because tags have to be decoded for every element.

Packed repeated primitives are serialized with the length of the payload first
followed by values without tags. When using fixed-width values, we can avoid
reallocations by knowing the final size the moment we start parsing; i.e., no
reallocation cost. We still don't know how many varints are in the payload and
may have to pay the reallocation cost.

In proto3, repeated fields are packed by default.

Packed works best with fixed-width values like fixed32, fixed64, float, double,
etc. since the entire encoded length can be predetermined by multiplying the
number of elements by the fixed value size, instead of having to calculate the
</details>

<details markdown="1">
<summary>
Use <code>bytes</code> instead for <code>string</code> for binary data
and large values.
</summary>

The `string` type holds UTF8-encoded text, and can sometimes require validation.
The `bytes` type can hold an arbitrary sequence of bytes (non-text data) and is
</details>

<details markdown="1">
<summary>
Consider using <code>Cord</code> for large fields to reduce copying
costs.
</summary>

Annotating large `bytes` and `string` fields with `[ctype=CORD]` may reduce
copying costs. This annotation changes the representation of the field from
`std::string` to `absl::Cord`. `absl::Cord` uses reference counting and
tree-based storage to reduce copying and appending costs. If a protocol buffer
is serialized to a cord, parsing a string or bytes field with `[ctype=CORD]` can
avoid copying the field contents.

{: .new}
```proto
message Document {
  ...
  bytes html = 4 [ctype = CORD];
}
```

Performance of a Cord field depends on length distribution and access patterns.
</details>

<details markdown="1">
<summary>
Use protobuf arenas in C++ code.
</summary>

Consider using arenas to save allocation and deallocation costs, especially for
protobufs containing repeated, string, or message fields.

Message and string fields are heap-allocated (even if the top-level protocol
buffer object is stack-allocated). If a protocol buffer message has a lot of sub
message fields and string fields, allocation and deallocation cost can be
significant. Arenas amortize allocation costs and makes deallocation virtually
free. It also improves memory locality by allocating from contiguous chunks of
</details>

<details markdown="1">
<summary>
Keep .proto files small
</summary>

Do not put too many messages in a single .proto file. Once you rely on anything
at all from a .proto file, the entire file will get pulled in by the linker even
if it's mostly unused. This increases build times and binary sizes. You can use
extensions and <code>Any</code> to avoid creating hard dependencies on big
</details>

<details markdown="1">
<summary>
Consider storing protocol buffers in serialized form, even in memory.
</summary>

In-memory protobuf objects have a large memory footprint (often 5x the wire
format size), potentially spread across many cache lines. So if your application
is going to keep many protobuf objects live for long periods of time, consider
</details>

<details markdown="1">
<summary>
Avoid protobuf map fields.
</summary>

Protobuf map fields have performance problems that usually outweigh the small
syntactic convenience they provide. Prefer using non-protobuf maps initialized
from protobuf contents:

msg.proto

{: .bad-code}
```proto
map<string, bytes> env_variables = 5;
```

{: .new}
```proto
message Var {
  string key = 1;
  bytes value = 2;
}
repeated Var env_variables = 5;
```

</details>

<details markdown="1">
<summary>
Use protobuf message definition with a subset of the fields.
</summary>

If you want to access only a few fields of a large message type, consider
defining your own protocol buffer message type that mimics the original type,
but only defines the fields that you care about. Here's an example:

{: .bad-code}
```proto
message FullMessage {
  optional int32 field1 = 1;
  optional BigMessage field2 = 2;
  optional int32 field3 = 3;
  repeater AnotherBigMessage field4 = 4;
  ...
  optional int32 field100 = 100;
}
```

{: .new}
```proto
message SubsetMessage {
  optional int32 field3 = 3;
  optional int32 field88 = 88;
}
```

By parsing a serialized `FullMessage` into a `SubsetMessage`, only two out of a
hundred fields are parsed and others are treated as unknown fields. Consider
using APIs that discard unknown fields to improve performance even more when
</details>

<details markdown="1">
<summary>
Reuse protobuf objects when possible.
</summary>

Declare protobuf objects outside loops so that their allocated storage can be
</details>

<!-- TODO: Flesh out the preceding examples, maybe with benchmarks. -->

## C++-Specific Advice

### absl::flat_hash_map (and set)

[Absl hash tables](https://abseil.io/docs/cpp/guides/container) usually
out-perform C++ standard library containers such as `std::map` and
`std::unordered_map`.

<details markdown="1">
<summary>
Sped up LanguageFromCode (use absl::flat_hash_map instead
of a __gnu_cxx::hash_map).
</summary>

languages.cc

{: .bad-code}
```c++
class CodeToLanguage
    ...
    : public __gnu_cxx::hash_map<absl::string_view, i18n::languages::Language,
                                 CodeHash, CodeCompare> {
```

{: .new}
```c++
class CodeToLanguage
    ...
    : public absl::flat_hash_map<absl::string_view, i18n::languages::Language,
                                 CodeHash, CodeCompare> {
```

Benchmark results:

{: .bench}
```
name               old time/op  new time/op  delta
BM_CodeToLanguage  19.4ns ± 1%  10.2ns ± 3%  -47.47%  (p=0.000 n=8+10)
```

</details>

<details markdown="1">
<summary>
Speed up stats publish/unpublish (an older change, so
uses dense_hash_map instead of absl::flat_hash_map, which did not exist at the
time).
</summary>

publish.cc

{: .bad-code}
```c++
typedef hash_map<uint64, Publication*> PublicationMap;
static PublicationMap* publications = NULL;
```

{: .new}
```c++
typedef dense_hash_map<uint64, Publication*> PublicationMap;;
static PublicationMap* publications GUARDED_BY(mu) = NULL;
```

</details>

<details markdown="1">
<summary>
Use dense_hash_map instead of hash_map for keeping track of
SelectServer alarms (would use absl::flat_hash_map today).
</summary>

alarmer.h

{: .bad-code}
```c++
typedef hash_map<int, Alarm*> AlarmList;
```

{: .new}
```c++
typedef dense_hash_map<int, Alarm*> AlarmList;
```

</details>

### absl::btree_map/absl::btree_set

absl::btree_map and absl::btree_set store multiple entries per tree node. This
has a number of advantages over ordered C++ standard library containers such as
`std::map`. First, the pointer overhead of pointing to child tree nodes is often
significantly reduced. Second, because the entries or key/values are stored
consecutively in memory for a given btree tree node, cache efficiency is often
significantly better.

<details markdown="1">
<summary>
Use btree_set instead of std::set to represent a very heavily used
work-queue.
</summary>

register_allocator.h

{: .bad-code}
```c++
using container_type = std::set<WorklistItem>;
```

{: .new}
```c++
using container_type = absl::btree_set<WorklistItem>;
```

</details>

### util::bitmap::InlinedBitVector

`util::bitmap::InlinedBitvector` can store short bit-vectors inline, and
therefore can often be a better choice than `std::vector<bool>` or other bitmap
types.

<details markdown="1">
<summary>
Use InlinedBitVector instead of std::vector&lt;bool>, and
then use FindNextBitSet to find the next item of interest.
</summary>

block_encoder.cc

{: .bad-code}
```c++
vector<bool> live_reads(nreads);
...
for (int offset = 0; offset < b_.block_width(); offset++) {
  ...
  for (int r = 0; r < nreads; r++) {
    if (live_reads[r]) {
```

{: .new}
```c++
util::bitmap::InlinedBitVector<4096> live_reads(nreads);
...
for (int offset = 0; offset < b_.block_width(); offset++) {
  ...
  for (size_t r = 0; live_reads.FindNextSetBit(&r); r++) {
    DCHECK(live_reads[r]);
```

</details>

### absl::InlinedVector

absl::InlinedVector stores a small number of elements inline (configurable via
the second template argument). This enables small vectors up to this number of
elements to generally have better cache efficiency and also to avoid allocating
a backing store array at all when the number of elements is small.

<details markdown="1">
<summary>
Use InlinedVector instead of std::vector in various places.
</summary>

bundle.h

{: .bad-code}
```c++
class Bundle {
 public:
 ...
 private:
  // Sequence of (slotted instruction, unslotted immediate operands).
  std::vector<InstructionRecord> instructions_;
  ...
};
```

{: .new}
```c++
class Bundle {
 public:
 ...
 private:
  // Sequence of (slotted instruction, unslotted immediate operands).
  absl::InlinedVector<InstructionRecord, 2> instructions_;
  ...
};
```

</details>

### gtl::vector32

Saves space by using a customized vector type that only supports sizes that fit
in 32 bits.

<details markdown="1">
<summary>
Simple type change saves ~8TiB of memory in Spanner.
</summary>

table_ply.h

{: .bad-code}
```c++
class TablePly {
    ...
    // Returns the set of data columns stored in this file for this table.
    const std::vector<FamilyId>& modified_data_columns() const {
      return modified_data_columns_;
    }
    ...
   private:
    ...
    std::vector<FamilyId> modified_data_columns_;  // Data columns in the table.
```

{: .new}
```c++
#include "util/gtl/vector32.h"
    ...
    // Returns the set of data columns stored in this file for this table.
    absl::Span<const FamilyId> modified_data_columns() const {
      return modified_data_columns_;
    }
    ...

    ...
    // Data columns in the table.
    gtl::vector32<FamilyId> modified_data_columns_;
```

</details>

### gtl::small_map

gtl::small_map uses an inline array to store up to a certain number of unique
key-value-pair elements, but upgrades itself automatically to be backed by a
user-specified map type when it runs out of space.

<details markdown="1">
<summary>
Use gtl::small_map in tflite_model.
</summary>

tflite_model.cc

{: .bad-code}
```c++
using ChoiceIdToContextMap = gtl::flat_hash_map<int, TFLiteContext*>;
```

{: .new}
```c++
using ChoiceIdToContextMap =
    gtl::small_map<gtl::flat_hash_map<int, TFLiteContext*>>;
```

</details>

### gtl::small_ordered_set

gtl::small_ordered_set is an optimization for associative containers (such as
std::set or absl::btree_multiset). It uses a fixed array to store a certain
number of elements, then reverts to using a set or multiset when it runs out of
space. For sets that are typically small, this can be considerably faster than
using something like set directly, as set is optimized for large data sets. This
change shrinks cache footprint and reduces critical section length.

<details markdown="1">
<summary>
Use gtl::small_ordered_set to hold set of listeners.
</summary>

broadcast_stream.h

{: .bad-code}
```c++
class BroadcastStream : public ParsedRtpTransport {
 ...
 private:
  ...
  std::set<ParsedRtpTransport*> listeners_ ABSL_GUARDED_BY(listeners_mutex_);
};
```

{: .new}
```c++
class BroadcastStream : public ParsedRtpTransport {
 ...
 private:
  ...
  using ListenersSet =
      gtl::small_ordered_set<std::set<ParsedRtpTransport*>, 10>;
  ListenersSet listeners_ ABSL_GUARDED_BY(listeners_mutex_);
```

</details>

### gtl::intrusive_list {#gtl-intrusive_list}

`gtl::intrusive_list<T>` is a doubly-linked list where the link pointers are
embedded in the elements of type T. It saves one cache line+indirection per
element when compared to `std::list<T*>`.

<details markdown="1">
<summary>
Use intrusive_list to keep track of inflight requests for
each index row update.
</summary>

row-update-sender-inflight-set.h

{: .bad-code}
```c++
std::set<int64> inflight_requests_ GUARDED_BY(mu_);
```

{: .new}
```c++
class SeqNum : public gtl::intrusive_link<SeqNum> {
  ...
  int64 val_ = -1;
  ...
};
...
gtl::intrusive_list<SeqNum> inflight_requests_ GUARDED_BY(mu_);
```

</details>

### Limit absl::Status and absl::StatusOr usage

Even though `absl::Status` and `absl::StatusOr` types are fairly efficient, they
have a non-zero overhead even in the success path and should therefore be
avoided for hot routines that don't need to return any meaningful error details
(or perhaps never even fail!):

<details markdown="1">
<summary>
Avoid StatusOr&lt;int64> return type for
RoundUpToAlignment() function.
</summary>

best_fit_allocator.cc

{: .bad-code}
```c++
absl::StatusOr<int64> BestFitAllocator::RoundUpToAlignment(int64 bytes) const {
  TPU_RET_CHECK_GE(bytes, 0);

  const int64 max_aligned = MathUtil::RoundDownTo<int64>(
      std::numeric_limits<int64>::max(), alignment_in_bytes_);
  if (bytes > max_aligned) {
    return util::ResourceExhaustedErrorBuilder(ABSL_LOC)
           << "Attempted to allocate "
           << strings::HumanReadableNumBytes::ToString(bytes)
           << " which after aligning to "
           << strings::HumanReadableNumBytes::ToString(alignment_in_bytes_)
           << " cannot be expressed as an int64.";
  }

  return MathUtil::RoundUpTo<int64>(bytes, alignment_in_bytes_);
}
```

best_fit_allocator.h

{: .new}
```c++
// Rounds bytes up to nearest multiple of alignment_.
// REQUIRES: bytes >= 0.
// REQUIRES: result does not overflow int64.
// REQUIRES: alignment_in_bytes_ is a power of 2 (checked in constructor).
int64 RoundUpToAlignment(int64 bytes) const {
  DCHECK_GE(bytes, 0);
  DCHECK_LE(bytes, max_aligned_bytes_);
  int64 result =
      ((bytes + (alignment_in_bytes_ - 1)) & ~(alignment_in_bytes_ - 1));
  DCHECK_EQ(result, MathUtil::RoundUpTo<int64>(bytes, alignment_in_bytes_));
  return result;
}
```

</details>

<details markdown="1">
<summary>
Added ShapeUtil::ForEachIndexNoStatus to avoid creating a
Status return object for every element of a tensor.
</summary>

shape_util.h

{: .bad-code}
```c++
using ForEachVisitorFunction =
    absl::FunctionRef<StatusOr<bool>(absl::Span<const int64_t>)>;
    ...
static void ForEachIndex(const Shape& shape, absl::Span<const int64_t> base,
                         absl::Span<const int64_t> count,
                         absl::Span<const int64_t> incr,
                         const ForEachVisitorFunction& visitor_function);

```

{: .new}
```c++
using ForEachVisitorFunctionNoStatus =
    absl::FunctionRef<bool(absl::Span<const int64_t>)>;
    ...
static void ForEachIndexNoStatus(
    const Shape& shape, absl::Span<const int64_t> base,
    absl::Span<const int64_t> count, absl::Span<const int64_t> incr,
    const ForEachVisitorFunctionNoStatus& visitor_function);
```

literal.cc

{: .bad-code}
```c++
ShapeUtil::ForEachIndex(
    result_shape, [&](absl::Span<const int64_t> output_index) {
      for (int64_t i = 0, end = dimensions.size(); i < end; ++i) {
        scratch_source_index[i] = output_index[dimensions[i]];
      }
      int64_t dest_index = IndexUtil::MultidimensionalIndexToLinearIndex(
          result_shape, output_index);
      int64_t source_index = IndexUtil::MultidimensionalIndexToLinearIndex(
          shape(), scratch_source_index);
      memcpy(dest_data + primitive_size * dest_index,
             source_data + primitive_size * source_index, primitive_size);
      return true;
    });
```

{: .new}
```c++
ShapeUtil::ForEachIndexNoStatus(
    result_shape, [&](absl::Span<const int64_t> output_index) {
      // Compute dest_index
      int64_t dest_index = IndexUtil::MultidimensionalIndexToLinearIndex(
          result_shape, result_minor_to_major, output_index);

      // Compute source_index
      int64_t source_index;
      for (int64_t i = 0, end = dimensions.size(); i < end; ++i) {
        scratch_source_array[i] = output_index[dimensions[i]];
      }
      if (src_shape_dims == 1) {
        // Fast path for this case
        source_index = scratch_source_array[0];
        DCHECK_EQ(source_index,
                  IndexUtil::MultidimensionalIndexToLinearIndex(
                      src_shape, src_minor_to_major, scratch_source_span));
      } else {
        source_index = IndexUtil::MultidimensionalIndexToLinearIndex(
            src_shape, src_minor_to_major, scratch_source_span);
      }
      // Move one element from source_index in source to dest_index in dest
      memcpy(dest_data + PRIMITIVE_SIZE * dest_index,
             source_data + PRIMITIVE_SIZE * source_index, PRIMITIVE_SIZE);
      return true;
    });
```

</details>

<details markdown="1">
<summary>
In TF_CHECK_OK, avoid creating Ok object in order to test
for ok().
</summary>

status.h

{: .bad-code}
```c++
#define TF_CHECK_OK(val) CHECK_EQ(::tensorflow::Status::OK(), (val))
#define TF_QCHECK_OK(val) QCHECK_EQ(::tensorflow::Status::OK(), (val))
```

{: .new}
```c++
extern tensorflow::string* TfCheckOpHelperOutOfLine(
    const ::tensorflow::Status& v, const char* msg);
inline tensorflow::string* TfCheckOpHelper(::tensorflow::Status v,
                                           const char* msg) {
  if (v.ok()) return nullptr;
  return TfCheckOpHelperOutOfLine(v, msg);
}
#define TF_CHECK_OK(val)                                           \
  while (tensorflow::string* _result = TfCheckOpHelper(val, #val)) \
  LOG(FATAL) << *(_result)
#define TF_QCHECK_OK(val)                                          \
  while (tensorflow::string* _result = TfCheckOpHelper(val, #val)) \
  LOG(QFATAL) << *(_result)
```

</details>

<details markdown="1">
<summary>
Remove StatusOr from the hot path of remote procedure
calls (RPCs).
</summary>

Removal of StatusOr from a hot path eliminated a 14% CPU regression in RPC
benchmarks caused by an earlier change.

privacy_context.h

{: .bad-code}
```c++
absl::StatusOr<privacy::context::PrivacyContext> GetRawPrivacyContext(
    const CensusHandle& h);
```

privacy_context_statusfree.h

{: .new}
```c++
enum class Result {
  kSuccess,
  kNoRootScopedData,
  kNoPrivacyContext,
  kNoDDTContext,
  kDeclassified,
  kNoPrequestContext
};
...
Result GetRawPrivacyContext(const CensusHandle& h,
                            PrivacyContext* privacy_context);
```

</details>

## Bulk Operations {#bulk-operations}

If possible, handle many items at once rather than just one at a time.

<details markdown="1">
<summary>
absl::flat_hash_map compares one hash byte per key from a
group of keys using a single SIMD instruction.
</summary>

See [Swiss Table Design Notes](https://abseil.io/about/design/swisstables) and
related [CppCon 2017](https://www.youtube.com/watch?v=ncHmEUmJZf4) and
[CppCon 2019](https://www.youtube.com/watch?v=JZE3_0qvrMg) talks by Matt
Kulukundis.

raw_hash_set.h

{: .new}
```c++
// Returns a bitmask representing the positions of slots that match hash.
BitMask<uint32_t> Match(h2_t hash) const {
  auto ctrl = _mm_loadu_si128(reinterpret_cast<const __m128i*>(pos));
  auto match = _mm_set1_epi8(hash);
  return BitMask<uint32_t>(_mm_movemask_epi8(_mm_cmpeq_epi8(match, ctrl)));
}
```

</details>

<details markdown="1">
<summary>
Do single operations to deal with many bytes and fix
things up, rather than checking every byte what to do.
</summary>

ordered-code.cc

{: .bad-code}
```c++
int len = 0;
while (val > 0) {
  len++;
  buf[9 - len] = (val & 0xff);
  val >>= 8;
}
buf[9 - len - 1] = (unsigned char)len;
len++;
FastStringAppend(dest, reinterpret_cast<const char*>(buf + 9 - len), len);
```

{: .new}
```c++
BigEndian::Store(val, buf + 1);  // buf[0] may be needed for length
const unsigned int length = OrderedNumLength(val);
char* start = buf + 9 - length - 1;
*start = length;
AppendUpto9(dest, start, length + 1);
```

</details>

<details markdown="1">
<summary>
Improve Reed-Solomon processing speed by handling
multiple interleaved input buffers more efficiently in chunks.
</summary>

{: .bench}
```
Run on (12 X 3501 MHz CPUs); 2016-09-27T16:04:55.065995192-04:00
CPU: Intel Haswell with HyperThreading (6 cores) dL1:32KB dL2:256KB dL3:15MB
Benchmark                          Base (ns)  New (ns) Improvement
------------------------------------------------------------------
BM_OneOutput/3/2                      466867    351818    +24.6%
BM_OneOutput/4/2                      563130    474756    +15.7%
BM_OneOutput/5/3                      815393    688820    +15.5%
BM_OneOutput/6/3                      897246    780539    +13.0%
BM_OneOutput/8/4                     1270489   1137149    +10.5%
BM_AllOutputs/3/2                     848772    642942    +24.3%
BM_AllOutputs/4/2                    1067647    638139    +40.2%
BM_AllOutputs/5/3                    1739135   1151369    +33.8%
BM_AllOutputs/6/3                    2045817   1456744    +28.8%
BM_AllOutputs/8/4                    3012958   2484937    +17.5%
BM_AllOutputsSetUpOnce/3/2            717310    493371    +31.2%
BM_AllOutputsSetUpOnce/4/2            833866    600060    +28.0%
BM_AllOutputsSetUpOnce/5/3           1537870   1137357    +26.0%
BM_AllOutputsSetUpOnce/6/3           1802353   1398600    +22.4%
BM_AllOutputsSetUpOnce/8/4           3166930   2455973    +22.4%
```

</details>

<details markdown="1">
<summary>
Decode four integers at a time (circa 2004).
</summary>

Introduced a
[GroupVarInt format](https://static.googleusercontent.com/media/research.google.com/en//people/jeff/WSDM09-keynote.pdf)
that encodes/decodes groups of 4 variable-length integers at a time in 5-17
bytes, rather than one integer at a time. Decoding one group of 4 integers in
the new format takes ~1/3rd the time of decoding 4 individually varint-encoded
integers.

groupvarint.cc

{: .new}
```c++
const char* DecodeGroupVar(const char* p, int N, uint32* dest) {
  assert(groupvar_initialized);
  assert(N % 4 == 0);
  while (N) {
    uint8 tag = *p;
    p++;

    uint8* lenptr = &groupvar_table[tag].length[0];

#define GET_NEXT                                        \
    do {                                                \
      uint8 len = *lenptr;                              \
      *dest = UNALIGNED_LOAD32(p) & groupvar_mask[len]; \
      dest++;                                           \
      p += len;                                         \
      lenptr++;                                         \
    } while (0)
    GET_NEXT;
    GET_NEXT;
    GET_NEXT;
    GET_NEXT;
#undef GET_NEXT

    N -= 4;
  }
  return p;
}
```

</details>

<details markdown="1">
<summary>
Encode groups of 4 k-bit numbers at a time.
</summary>

Added KBitStreamEncoder and KBitStreamDecoder classes to encode/decode 4 k-bit
numbers at a time into a bit stream. Since K is known at compile time, the
encoding and decoding can be quite efficient. E.g., since four numbers are
encoded at a time, the code can assume that the stream is always byte-aligned
</details>

## CLs that demonstrate multiple techniques {#cls-that-demonstrate-multiple-techniques}

Sometimes a single CL contains a number of performance-improving changes that
use many of the preceding techniques. Looking at the kinds of changes in these
CLs is sometimes a good way to get in the mindset of making general changes to
speed up the performance of some part of a system after that has been identified
as a bottleneck.

<details markdown="1">
<summary>
Speed up GPU memory allocator by ~40%.
</summary>

36-48% speedup in allocation/deallocation speed for GPUBFCAllocator:

1.  Identify chunks by a handle number, rather than by a pointer to a Chunk.
    Chunk data structures are now allocated in a `vector<Chunk>`, and a handle
    is an index into this vector to refer to a particular chunk. This allows the
    next and prev pointers in Chunk to be ChunkHandle (4 bytes), rather than
    `Chunk*` (8 bytes).

2.  When a Chunk object is no longer in use, we maintain a free list of Chunk
    objects, whose head is designated by ChunkHandle `free_chunks_list_`, and
    with the `Chunk->next` pointing to the next free list entry. Together with
    (1), this allows us to avoid heap allocation/deallocation of Chunk objects
    in the allocator, except (rarely) when the `vector<Chunk>` grows. It also
    makes all the memory for Chunk objects contiguous.

3.  Rather than having the bins_ data structure be a std::set and using
    lower_bound to locate the appropriate bin given a byte_size, we instead have
    an array of bins, indexed by a function that is log₂(byte_size/256). This
    allows the bin to be located with a few bit operations, rather than a binary
    search tree lookup. It also allows us to allocate the storage for all the
    Bin data structures in a contiguous array, rather than in many different
    cache lines. This reduces the number of cache lines that must be moved
    around between cores when multiple threads are doing allocations.

4.  Added fast path to GPUBFCAllocator::AllocateRaw that first tries to allocate
    memory without involving the retry_helper_. If an initial attempt fails
    (returns nullptr), then we go through the retry_helper_, but normally we can
    avoid several levels of procedure calls as well as the
    allocation/deallocation of a std::function with several arguments.

5.  Commented out most of the VLOG calls. These can be reenabled selectively
    when needed for debugging purposes by uncommenting and recompiling.

Added multi-threaded benchmark to test allocation under contention.

Speeds up ptb_word_lm on my desktop machine with a Titan X card from 8036 words
per second to 8272 words per second (+2.9%).

{: .bench}
```
Run on (40 X 2801 MHz CPUs); 2016/02/16-15:12:49
CPU: Intel Ivybridge with HyperThreading (20 cores) dL1:32KB dL2:256KB dL3:25MB
Benchmark                          Base (ns)  New (ns) Improvement
------------------------------------------------------------------
BM_Allocation                            347       184    +47.0%
BM_AllocationThreaded/1                  351       181    +48.4%
BM_AllocationThreaded/4                 2470      1975    +20.0%
BM_AllocationThreaded/16               11846      9507    +19.7%
BM_AllocationDelayed/1                   392       199    +49.2%
BM_AllocationDelayed/10                  285       169    +40.7%
BM_AllocationDelayed/100                 245       149    +39.2%
BM_AllocationDelayed/1000                238       151    +36.6%
```

</details>

<details markdown="1">
<summary>
Speed up Pathways throughput by ~20% via a set of
miscellaneous changes.
</summary>

*   Unified a bunch of special fast descriptor parsing functions into a single
    ParsedDescriptor class and use this class in more places to avoid expensive
    full parse calls.

*   Change several protocol buffer fields from string to bytes (avoids
    unnecessary utf-8 checks and associated error handling code).

*   DescriptorProto.inlined_contents is now a string, not a Cord (it is expected
    to be used only for small-ish tensors). This necessitated the addition of a
    bunch of copying helpers in tensor_util.cc (need to now support both strings
    and Cords).

*   Use flat_hash_map instead of std::unordered_map in a few places.

*   Added MemoryManager::LookupMany for use by Stack op instead of calling
    Lookup per batch element. This change reduces setup overhead like locking.

*   Removed some unnecessary string creation in TransferDispatchOp.

*   Performance results for transferring a batch of 1000 1KB tensors from one
    component to another in the same process:

{: .bench}
```
Before: 227.01 steps/sec
After:  272.52 steps/sec (+20% throughput)
```

</details>

<details markdown="1">
<summary>
~15% XLA compiler performance improvement through a
series of changes.
</summary>

Some changes to speed up XLA compilation:

1.  In SortComputationsByContent, return false if a == b in comparison function,
    to avoid serializing and fingerprinting long computation strings.

2.  Turn CHECK into DCHECK to avoid touching an extra cache line in
    HloComputation::ComputeInstructionPostOrder

3.  Avoid making an expensive copy of the front instruction in
    CoreSequencer::IsVectorSyncHoldSatisfied().

4.  Rework 2-argument HloComputation::ToString and HloComputation::ToCord
    routines to do the bulk of the work in terms of appending to std::string,
    rather than appending to a Cord.

5.  Change PerformanceCounterSet::Increment to just do a single hash table
    lookup rather than two.

6.  Streamline Scoreboard::Update code

Overall speedup of 14% in XLA compilation time for one important
model.

</details>

<details markdown="1">
<summary>
Speed up low level logging in Google Meet application
code.
</summary>

Speed up ScopedLogId, which is on the critical path for each packet.

*   Removed the `LOG_EVERY_N(ERROR, ...)` messages that seemed to be there only
    to see if invariants were violated.
*   Inlined the PushLogId and PopLogid() routines (since without the
    `LOG_EVERY_N_SECONDS(ERROR, ...)` statements, they are now small enough to
    inline.
*   Switched to using a fixed array of size 4 and an 'int size' variable instead
    of an `InlinedVector<...>` for maintaining the thread local state. Since we
    never were growing beyond size 4 anyway, the InlinedVector's functionality
    was more general than needed.

{: .bench}
```
Base: Baseline plus the code in scoped_logid_test.cc to add the benchmark
New: This changelist

CPU: Intel Ivybridge with HyperThreading (20 cores) dL1:32KB dL2:256KB dL3:25MB
Benchmark                                      Base (ns)    New (ns) Improvement
----------------------------------------------------------------------------
BM_ScopedLogId/threads:1                               8           4    +52.6%
BM_ScopedLogId/threads:2                               8           4    +51.9%
BM_ScopedLogId/threads:4                               8           4    +52.9%
BM_ScopedLogId/threads:8                               8           4    +52.1%
BM_ScopedLogId/threads:16                             11           6    +44.0%

```

</details>

<details markdown="1">
<summary>
Reduce XLA compilation time by ~31% by improving Shape
handling.
</summary>

Several changes to improve XLA compiler performance:

1.  Improved performance of ShapeUtil::ForEachIndex... iteration in a few ways:

    *   In ShapeUtil::ForEachState, save just pointers to the arrays represented
        by the spans, rather than the full span objects.

    *   Pre-form a ShapeUtil::ForEachState::indexes_span pointing at the
        ShapeUtil::ForEachState::indexes vector, rather than constructing this
        span from the vector on every loop iteration.

    *   Save a ShapeUtil::ForEachState::indexes_ptr pointer to the backing store
        of the ShapeUtil::ForEachState::indexes vector, allowing simple array
        operations in ShapeUtil::ForEachState::IncrementDim(), rather than more
        expensive vector::operator[] operations.

    *   Save a ShapeUtil::ForEachState::minor_to_major array pointer initialized
        in the constructor by calling shape.layout().minor_to_major().data()
        rather than calling LayoutUtil::Minor(...) for each dimension for each
        iteration.

    *   Inlined the ShapeUtil::ForEachState constructor and the
        ShapeUtil::ForEachState::IncrementDim() routines

2.  Improved the performance of ShapeUtil::ForEachIndex iteration for call sites
    that don't need the functionality of returning a Status in the passed in
    function. Did this by introducing ShapeUtil::ForEachIndexNoStatus variants,
    which accept a ForEachVisitorFunctionNoStatus (which returns a plain bool).
    This is faster than the ShapeUtil::ForEachIndex routines, which accept a
    ForEachVisitorFunction (which returns a `StatusOr<bool>`, which requires an
    expensive `StatusOr<bool>` destructor call per element that we iterate
    over).

    *   Used this variant of ShapeUtil::ForEachIndexNoStatus in
        LiteralBase::Broadcast and GenerateReduceOutputElement.

3.  Improved performance of LiteralBase::Broadcast in several ways:

    *   Introduced templated BroadcastHelper routine in literal.cc that is
        specialized for different primitive byte sizes (without this,
        primitive_size was a runtime variable and so the compiler couldn't do a
        very good job of optimizing the memcpy that occurred per element, and
        would invoke the general memcpy path that assumes the byte count is
        fairly large, even though in our case it is a tiny power of 2 (typically
        1, 2, 4, or 8)).

    *   Avoided all but one of ~(5 + num_dimensions + num_result_elements)
        virtual calls per Broadcast call by making a single call to 'shape()' at
        the beginning of the LiteralBase::Broadcast routine. The innocuous
        looking 'shape()' calls that were sprinkled throughout end up boiling
        down to "root_piece().subshape()", where subshape() is a virtual
        function.

    *   In the BroadcastHelper routine, Special-cased the source dimensions
        being one and avoided a call to
        IndexUtil::MultiDimensionalIndexToLinearIndex for this case.

    *   In BroadcastHelper, used a scratch_source_array pointer variable that
        points into the backing store of the scratch_source_index vector, and
        used that directly to avoid vector::operator[] operations inside the
        per-element code. Also pre-computed a scratch_source_span that points to
        the scratch_source_index vector outside the per-element loop in
        BroadcastHelper, to avoid constructing a span from the vector on each
        element.

    *   Introduced new three-argument variant of
        IndexUtil::MultiDimensionalIndexToLinearIndex where the caller passes in
        the minor_to_major span associated with the shape argument. Used this in
        BroadcastHelper to compute this for the src and dst shapes once per
        Broadcast, rather than once per element copied.

4.  In ShardingPropagation::GetShardingFromUser, for the HloOpcode::kTuple case,
    only call user.sharding().GetSubSharding(...) if we have found the operand
    to be of interest. Avoiding calling it eagerly reduces CPU time in this
    routine for one lengthy compilation from 43.7s to 2.0s.

5.  Added benchmarks for ShapeUtil::ForEachIndex and Literal::Broadcast and for
    the new ShapeUtil::ForEachIndexNoStatus.

{: .bench}
```
Base is with the benchmark additions of
BM_ForEachIndex and BM_BroadcastVectorToMatrix (and BUILD file change to add
benchmark dependency), but no other changes.

New is this cl

Run on (72 X 1357.56 MHz CPU s) CPU Caches: L1 Data 32 KiB (x36)
L1 Instruction 32 KiB (x36) L2 Unified 1024 KiB (x36) L3 Unified 25344 KiB (x2)

Benchmark                                      Base (ns)    New (ns) Improvement
----------------------------------------------------------------------------
BM_MakeShape                                       18.40       18.90     -2.7%
BM_MakeValidatedShape                              35.80       35.60     +0.6%
BM_ForEachIndex/0                                  57.80       55.80     +3.5%
BM_ForEachIndex/1                                  90.90       85.50     +5.9%
BM_ForEachIndex/2                               1973606     1642197     +16.8%
```

The newly added ForEachIndexNoStatus is considerably faster than the
ForEachIndex variant (it only exists in this new cl, but the benchmark work that
is done by BM_ForEachIndexNoStatus/NUM is comparable to the BM_ForEachIndex/NUM
results above).

{: .bench}
```
Benchmark                                      Base (ns)    New (ns) Improvement
----------------------------------------------------------------------------
BM_ForEachIndexNoStatus/0                             0        46.90    ----
BM_ForEachIndexNoStatus/1                             0        65.60    ----
BM_ForEachIndexNoStatus/2                             0     1001277     ----
```

Broadcast performance improves by ~58%.

{: .bench}
```
Benchmark                                      Base (ns)    New (ns) Improvement
----------------------------------------------------------------------------
BM_BroadcastVectorToMatrix/16/16                   5556        2374     +57.3%
BM_BroadcastVectorToMatrix/16/1024               319510      131075     +59.0%
BM_BroadcastVectorToMatrix/1024/1024           20216949     8408188     +58.4%
```

Macro results from doing ahead-of-time compilation of a large language model
(program does more than just the XLA compilation, but spends a bit less than
half its time in XLA-related code):

Baseline program overall: 573 seconds With this cl program overall: 465 seconds
(+19% improvement)

Time spent in compiling the two largest XLA programs in running this program:

Baseline: 141s + 143s = 284s With this CL: 99s + 95s = 194s (+31% improvement)
</details>

<details markdown="1">
<summary>
Reduce compilation time for large programs by ~22% in
Plaque (a distributed execution framework).
</summary>

Small tweaks to speed up compilation by ~22%.

1.  Speed up detection of whether or not two nodes share a common source.
    Previously, we would get the sources for each node in sorted order and then
    do a sorted intersection. We now place the sources for one node in a
    hash-table and then iterate over the other node's sources checking the
    hash-table.
2.  Reuse the same scratch hash-table in step 1.
3.  When generating compiled proto, keep a single btree keyed by `pair<package,
    opname>` instead of a btree of btrees.
4.  Store pointer to opdef in the preceding btree instead of copying the opdef
    into the btree.

Measurement of speed on large programs (~45K ops):

{: .bench}
```
name             old time/op  new time/op  delta
BM_CompileLarge   28.5s ± 2%   22.4s ± 2%  -21.61%  (p=0.008 n=5+5)
```

</details>

<details markdown="1">
<summary>
MapReduce improvements (~2X speedup for wordcount
benchmark).
</summary>

Mapreduce speedups:

1.  The combiner data structures for the SafeCombinerMapOutput class have been
    changed. Rather than using a `hash_multimap<SafeCombinerKey, StringPiece>`,
    which had a hash table entry for each unique key/value inserted in the
    table, we instead use a `hash_map<SafeCombinerKey, ValuePtr*>` (where
    ValuePtr is a linked list of values and repetition counts). This helps in
    three ways:

    *   It significantly reduces memory usage, since we only use
        "sizeof(ValuePtr) + value_len" bytes for each value, rather than
        "sizeof(SafeCombinerKey) + sizeof(StringPiece) + value_len + new hash
        table entry overhead" for each value. This means that we flush the
        reducer buffer less often.

    *   It's significantly faster, since we avoid extra hash table entries when
        we're inserting a new value for a key that already exists in the table
        (and instead we just hook the value into the linked list of values for
        that key).

    *   Since we associate a repetition count with each value in the linked
        list, we can represent this sequence:

        ```c++
        Output(key, "1");
        Output(key, "1");
        Output(key, "1");
        Output(key, "1");
        Output(key, "1");
        ```

    as a single entry in the linked list for "key" with a repetition count of 5.
    Internally we yield "1" five times to the user-level combining function. (A
    similar trick could be applied on the reduce side, perhaps).

2.  (Minor) Added a test for "nshards == 1" to the default
    MapReductionBase::KeyFingerprintSharding function that avoids fingerprinting
    the key entirely if we are just using 1 reduce shard (since we can just
    return 0 directly in that case without examining the key).

3.  Turned some VLOG(3) statements into DVLOG(3) in the code path that is called
    for each key/value added to the combiner.

Reduces time for one wordcount benchmark from 12.56s to 6.55s.

</details>

<details markdown="1">
<summary>
Reworked the alarm handling code in the SelectServer to
significantly improve its performance (adding+removing an alarm from 771 ns to
271 ns).
</summary>

Reworked the alarm handling code in the SelectServer to significantly improve
its performance.

Changes:

1.  Switched to using `AdjustablePriorityQueue<Alarm>` instead of a a
    `set<Alarm*>` for the `AlarmQueue`. This significantly speeds up alarm
    handling, reducing the time taken to add and remove an alarm from 771
    nanoseconds to 281 nanoseconds. This change avoids an
    allocation/deallocation per alarm setup (for the red-black tree node in the
    STL set object), and also gives much better cache locality (since the
    AdjustablePriorityQueue is a heap implemented in a vector, rather than a
    red-black tree), there are fewer cache lines touched when manipulating the
    `AlarmQueue` on every trip through the selectserver loop.

2.  Converted AlarmList in Alarmer from a hash_map to a dense_hash_map to avoid
    another allocation/deallocation per alarm addition/deletion (this also
    improves cache locality when adding/removing alarms).

3.  Removed the `num_alarms_stat_` and `num_closures_stat_`
    MinuteTenMinuteHourStat objects, and the corresponding exported variables.
    Although monitoring these seems nice, in practice they add significant
    overhead to critical networking code. If I had left these variables in as
    Atomic32 variables instead of MinuteTenMinuteHourStat, they would have still
    increased the cost of adding and removing alarms from 281 nanoseconds to 340
    nanoseconds.

Benchmark results

{: .bad-code}
```
Benchmark                      Time(ns)  CPU(ns) Iterations
-----------------------------------------------------------
BM_AddAlarm/1                       902      771     777777
```

With this change

{: .new}
```
Benchmark                      Time(ns)  CPU(ns) Iterations
-----------------------------------------------------------
BM_AddAlarm/1                       324      281    2239999
```

</details>

<details markdown="1">
<summary>
3.3X performance in index serving speed!
</summary>

We found a number of performance issues when planning a switch from on-disk to
in-memory index serving in 2001. This change fixed many of these problems and
took us from 150 to over 500 in-memory queries per second (for a 2 GB in-memory
index on dual processor Pentium III machine).

*   Lots of performance improvements to index block decoding speed (8.9 MB/s to
    13.1 MB/s for a micro-benchmark).
*   We now checksum the block during decoding. This allows us to implement all
    of our getsymbol operations to be done without any bounds checking.
*   We have grungy macros that hold the various fields of a BitDecoder in local
    variables over entire loops, and then store them back at the end of the
    loops.
*   We use inline assembly to get at the 'bsf' instruction on Intel chips for
    getUnary (finds index of first 1 bit in a word)
*   When decoding values into a vector, we resize the vector outside of the loop
    and just walk a pointer along the vector, rather than doing a bounds-checked
    access to store every value.
*   During docid decoding, we keep the docids in local docid space, to avoid
    multiplying by num_shards_. Only when we need the actual docid value do we
    multiply by num_shards_ and add my_shard_.
*   The IndexBlockDecoder now exports an interface 'AdvanceToDocid' that returns
    the index of the first docid &ge; "d". This permits the scanning to be done
    in terms of local docids, rather than forcing the conversion of each local
    docid to a global docid when the client calls GetDocid(index) for every
    index in the block.
*   Decoding of position data for documents is now done on demand, rather than
    being done eagerly for the entire block when the client asked for position
    data for any document within the block.
*   If the index block being decoded ends within 4 bytes of a page boundary, we
    copy it to a local buffer. This allows us to always load our bit decoding
    buffer via a 4-byte load, without having to worry about seg faults if we run
    off the end of a mmapped page.
*   We only initialize the first nterms_ elements of various scoring data
    structures, rather than initializing all MAX_TERMS of them (in some cases,
    we were unnecessarily memsetting 20K to 100K of data per document scored).
*   Avoid round_to_int and subsequent computation on intermediate scoring values
    when the value being computed is 0 (the subsequent computation was just
    writing '0' over the 0 that we had memset in these cases, and this was the
    most common case).
*   Made a bounds check on scoring data structures into a debug-mode assertion.

</details>

## Further Reading

In no particular order, a list of performance related books and articles that
the authors have found helpful:

*   [Optimizing software in C++](https://www.agner.org/optimize/optimizing_cpp.pdf)
    by Agner Fog. Describes many useful low-level techniques for improving
    performance.
*   [Understanding Software Dynamics](https://www.oreilly.com/library/view/understanding-software-dynamics/9780137589692/)
    by Richard L. Sites. Covers expert methods and advanced tools for diagnosing
    and fixing performance problems.
*   [Performance tips of the week](https://abseil.io/fast/) - a collection of
    useful tips.
*   [Performance Matters](https://travisdowns.github.io/) - a collection of
    articles about performance.
*   [Daniel Lemire's blog](https://lemire.me/blog/) - high performance
    implementations of interesting algorithms.
*   [Building Software Systems at Google and Lessons Learned](https://www.youtube.com/watch?v=modXC5IWTJI) -
    a video that describes system performance issues encountered at Google over
    a decade.
*   [Programming Pearls](https://books.google.com/books/about/Programming_Pearls.html?id=kse_7qbWbjsC)
    and
    [More Programming Pearls: Confessions of a Coder](https://books.google.com/books/about/More_Programming_Pearls.html?id=a2AZAQAAIAAJ)
    by Jon Bentley. Essays on starting with algorithms and ending up with simple
    and efficient implementations.
*   [Hacker's Delight](https://en.wikipedia.org/wiki/Hacker%27s_Delight) by
    Henry S. Warren. Bit-level and arithmetic algorithms for solving some common
    problems.
*   [Computer Architecture: A Quantitive Approach](https://books.google.com/books/about/Computer_Architecture.html?id=cM8mDwAAQBAJ)
    by John L. Hennessy and David A. Patterson - Covers many aspects of computer
    architecture, including one that performance-minded software developers
    should be aware of like like caches, branch predictors, TLBs, etc.

## Suggested Citation

If you want to cite this document, we suggest:

```
Jeffrey Dean & Sanjay Ghemawat, Performance Hints, 2024, https://google.github.io/performance-hints
```

Or in BibTeX:

```bibtex
@misc{DeanGhemawatPerformance2024,
  author = {Dean, Jeffrey and Ghemawat, Sanjay},
  title = {Performance Hints},
  year = {2024},
  publisher = {GitHub},
  journal = {GitHub repository},
  howpublished = {\url{https://google.github.io/performance-hints}},
}
```

## Acknowledgments

Many colleagues have provided helpful feedback on this document, including:

*   Adrian Ulrich
*   Alexander Kuzmin
*   Alexei Bendebury
*   Alexey Alexandrov
*   Amer Diwan
*   Austin Sims
*   Benoit Boissinot
*   Brooks Moses
*   Chris Kennelly
*   Chris Ruemmler
*   Danila Kutenin
*   Darryl Gove
*   David Majnemer
*   Dmitry Vyukov
*   Emanuel Taropa
*   Felix Broberg
*   Francis Birck Moreira
*   Gideon Glass
*   Henrik Stewenius
*   Jeremy Dorfman
*   John Dethridge
*   Kurt Kluever
*   Kyle Konrad
*   Lucas Pereira
*   Marc Eaddy
*   Michael Marty
*   Michael Whittaker
*   Mircea Trofin
*   Misha Brukman
*   Nicolas Hillegeer
*   Ranjit Mathew
*   Rasmus Larsen
*   Soheil Hassas Yeganeh
*   Srdjan Petrovic
*   Steinar H. Gunderson
*   Stergios Stergiou
*   Steven Timotius
*   Sylvain Vignaud
*   Thomas Etter
*   Thomas Köppe
*   Tim Chestnutt
*   Todd Lipcon
*   Vance Lankhaar
*   Victor Costan
*   Yao Zuo
*   Zhou Fang
*   Zuguang Yang

[go benchmarks]: https://pkg.go.dev/testing#hdr-Benchmarks
[fast39]: https://abseil.io/fast/39
[fast53]: https://abseil.io/fast/53
[cpp benchmarks]: https://github.com/google/benchmark/blob/main/README.md
[jmh]: https://github.com/openjdk/jmh
[xprof]: https://www.tensorflow.org/tensorboard/tensorboard_profiling_keras#debug_performance_bottlenecks
[profile sources]: https://gperftools.github.io/gperftools/heapprofile.html
[annotated source]: https://github.com/google/pprof/blob/main/doc/README.md#annotated-source-code
[disassembly]: https://github.com/google/pprof/blob/main/doc/README.md#annotated-source-code
[atomic danger]: https://abseil.io/docs/cpp/atomic_danger
