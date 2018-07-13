---
title: "Coroutine Types"
layout: blog
sidenav: side-nav-blog.html
published: true
permalink: blog/20180713-coroutine-types
type: markdown
category: blog
excerpt_separator: <!--break-->
---

By [Titus Winters](mailto:titus@google.com)

The first hint of standard library design that takes advantage of coroutines
([P1056](http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2018/p1056r0.html)) 
came through the Library Evolution Working Group (LEWG, responsible for design 
for the C++ standard library) during the Rapperswil meeting this summer. It was
... surprising. As much as I want coroutines in the language, the design smell
here was disconcerting. I want to point out what LEWG saw before we commit to
this direction irrevocably - coroutine types as currently designed are baffling.

<!--break-->

## Background

Coroutines are an important new language feature for C++, but also a very old 
idea.  In its current incarnation, the major force behind Coroutines in C++ is 
Gor Nishanov (whom I absolutely love working with).  If you aren't familiar 
with the history, or want a refresher on how Coroutines are a generalization of 
subroutines (function calls), try watching Gor's talk from CppCon 2015:
"[C++ Coroutines, a negative overhead abstraction.](https://www.youtube.com/watch?v=_fu0gx-xseY)"

In a function call/subroutine world, the caller invokes some function, the 
function runs, and then the function returns execution control to the caller. 
We're all familiar with this. In an asynchronous programming model we often 
have a logically-related sequence of operations we want to execute (for 
instance, kicking off a sequence of async operations one by one) but cannot 
express as a single function, because we need to jump in and out of that flow 
of control. As a result, all necessary state gets bundled up and passed around 
as a "continuation," to be invoked at some point in the future. This is
generally known as
[continuation passing](https://en.wikipedia.org/wiki/Continuation-passing_style)
and you see it in languages/libraries/frameworks that are very 
functional-style, very asynchronous, or very callback-driven. It's powerful,
but not nearly as clear as direct style programming.

Coroutines are an attempt to provide a language-level ability to write in a 
direct style and execute in a continuation-passing style. For example, consider
an example from [P1056](http://wg21.link/P1056):


```cpp
struct record {
  int id;
  std::string name;
  std::string description;
};
  
std::task<record> load_record(int id);
std::task<> save_record(record r);
  
std::task<void> modify_record() {
  record r = co_await load_record(123);
  r.description = "Look, ma, no blocking!";
  co_await save_record(std::move(r));
}
```

In this snippet we're imagining a to-be-specified type `std::task<T>` that is 
in many ways a lighter-weight `std::future<T>`. It isn't promising anything to 
do with concurrency or synchronization, and has no allocation or shared state. 
Functions that return `std::task` are coroutines - they can suspend (by calling 
`co_await`) and return execution to the caller - leaving any variables local to 
the coroutine's stack intact. 

A caller can invoke `modify_record()` as a coroutine, allowing the caller to be 
part of the continuation chain.  This requires returning a coroutine-enabled 
type like `std::task<>` - but note that the types don't have to line up.


```cpp
std::task<void> f() {
  std::cout << "About to modify" << std::endl;
  co_await modify_record();
  std::cout << "Done modifying" << std::endl;
}  
```

In such an invocation, the two log statements will happen in order, but all 
sorts of computation may happen in the caller of `f()` between the two log 
outputs, because execution is yielded at the point of the `co_await` "call" to 
`modify_record()`. (This is expected: that is the whole point of coroutines.)

Note that because any function that uses the new coroutine keywords is now by 
definition a coroutine, there are some potential surprises. For example, if we 
were to invoke `f()` directly:


```cpp
void invoke_f() {
  f();
}
```

This (maybe) compiles, but generates none of the logging output because the 
body of `f()` is not executed at all until something invokes `co_await` on the 
`task` returned by `f()` - which we just ignored.  Many/most coroutine types 
are thus expected to be marked `[[nodiscard]]` - there is no point in calling a 
function that returns a type like `std::task<>` without operating on the task. 
(Remember: pay attention to those `[[nodiscard]]` warnings!)

The current specification provides no way for an ordinary (non-coroutine) 
function to usefully invoke a coroutine that returns `task<T>` nor to obtain 
the `T` that it wraps. In order to invoke `f()` like a function we would need 
some special coroutine-execution machinery - the
[cppcoro repository](https://github.com/lewissbaker/cppcoro) provides this in 
the form of a `sync_wait()` function. The specification of a `sync_wait()` has 
not yet been produced, but there will eventually be one overarching 
`sync_wait()` that works with anything satisfying the Awaitable concept.

There are a host of other interesting points and gotchas in coroutines, and 
also a competing proposal produced by my Google colleagues 
([P1063](http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2018/p1063r0.pdf)). 
All of that additional background is interesting and worth getting into, but is 
separate from the point of this post.


## The `task<>` API

The main question here is "What does `std::task<>` look like?" Given that 
coroutines are inherently slicing apart something as fundamental as "what is a 
function call," we're likely going to see something interesting/exotic in the 
best case.  Whether those exotic results are acceptable in trade for this very 
powerful feature is clearly a matter of taste, and what I want to bring to the 
attention of the community.

That said, here is the complete callable API for the proposed `std::task`:

```cpp
template <typename T> class [[nodiscard]] task {
  public:
    task(task&& rhs) noexcept;
    ~task();
    auto operator co_await();  // exposition only
};   
```

Take a close look at that.  

This is a type that wraps a `T` … but has no interfaces that mention that `T`. 
This is a type that can be move-constructed, and destroyed. Per the "exposition 
only" comment, it can be used via the new `co_await` keyword. That's it. 
Strictly speaking, `co_await` doesn't even return `T`, it returns a bunch of 
customization machinery that configures coroutine machinery so that you can get 
a `T`. The only way for a user to know that `co_await` yields a `T` is to see
it in use, or read the comments. The user-facing API for coroutine types like
this do not actually show you what you expect to see.

This would represent an unusual step for type design - producing types whose 
interface does not (and arguably cannot) describe its expected usage. IDEs are 
going to choke on this, autocompleters are useless, 
[cppreference.com](http://cppreference.com) documentation will be novel at best.

The
[simplest current implementation of task<>](https://wandbox.org/permlink/Xb1Lu7DMmm1NVkNC)
(thanks Gor!) runs about 40 lines and is illustrative - most of the body of 
such a type is detailing its interaction with the coroutine machinery and 
definition of its related promise type. 

It's well worth spending a few minutes reading through
[P1056](http://wg21.link/P1056r0) and the above implementation link. It is
certainly possible that coroutines require this complexity and subtlety - it is
a fundamental extension to basic programming concepts. But we should be sure
that this is well understood including its impact on the language, library,
documentation, and the rest of the ecosystem. We should also be sure that we
have found the right abstraction boundaries, not just something that works.

## Coroutine Type Design

Since the earliest days of the Coroutines proposals it's been clear that 
implementing coroutine types is not something that we expect most developers to 
do: this is specialist work, and libraries like Abseil, Boost, and the standard 
library will probably do the heavy lifting for most developers. Considering the 
results that we've been able to see with the coroutines Technical Specification 
and coroutine demos, that's probably fine - this is powerful, and the resulting 
user code is pretty reasonable.

That said, if this is the style of specification and user-facing API for 
coroutine types, I have concerns.  The user-facing APIs produced using this 
machinery are nonsensical and impossible to understand with normal patterns 
(like "reading the API") - all of their details are literally hidden in the 
coroutine customization machinery. It's technically correct and functional, of 
course, but something smells wrong. 

On the other hand, some coroutine-backed designs seem basically OK. A 
[generator demonstration](https://godbolt.org/g/mCKfnr) uses iterators as the 
user-facing portion of the coroutine API, and the iterator certainly tells me 
that I get a `T` when I dereference `generator<T>::begin()`. Perhaps this is 
nothing more than "asynchrony is complicated" which should come as little 
surprise.

Looking at both the [generator example](https://godbolt.org/g/mCKfnr) and 
[task<> example](https://godbolt.org/g/mCKfnr) (both graciously provided by 
Gor), perhaps the real question is this: how confident are we (the committee 
and the community) that `promise_type` and the other coroutine customization 
points are the right design?  Clearly they are a correct and functional design 
; as always, I'm terribly impressed with the end result of the code that uses 
all of this. I'm less convinced that all of these apparent knobs are proveably 
the right set of basic operations and customization.

I'm not sure what the better answer is, and I have largely been uninvolved in my
colleagues' proposal ([P1063](http://wg21.link/p1063)) - I'm not sure that such
a proposal would produce clearer types or customization points that I was more
confident in. But even absent a better proposal, I want the community to look at
this and pause. Is anyone else uncomfortable with designs like these? Are we
sure we want to rush to include coroutines in the next C++ release, even with
these design smells?

As is often the case, I urge the committee and community to take the time to be 
sure. If we proceed as-is, we're likely stuck with these designs for a long 
time to come.
