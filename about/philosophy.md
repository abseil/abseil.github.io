---
title: Abseil Philosophy
layout: about
sidenav: side-nav-about.html
type: markdown
---

## Why Adopt Abseil?

Or: Why the world has room for another collection of C++ utility libraries

There are a few main reasons we recommend Abseil as your first choice for
utility code when starting a new C++ project:

* Compatibility with current and future C++ standards, and planned evolution
  over time
* Compatibility with Google OSS projects - these are the foundational types for
  things like Protocol Buffers, gRPC, and TensorFlow
* Upgrade Support - make it easy to live at head
* Production Experience - These are the interfaces that we are using in Google
  production
* Interest in a different set of design priorities than the C++ standard

The extent to which any of these arguments applies to your project will depend
on lots of things: we don't claim that Abseil is a silver bullet, or a perfect
solution for everyone's problems. On the other hand, these libraries have grown
inside Google for many years and we've learned a lot in their evolution. We know
that these libraries and our upgrade policies can be a good solution for some
types of problems that are important in the industry, and over time we've
learned how to provide this sort of infrastructure in an evolving but
maintainable fashion. 

### Compatibility With Current and Future C++ Standards

Google has developed many abstractions that either match or closely match
features incorporated into C++14, C++17, and beyond. Using the Abseil versions
of these abstractions allows you to access these features now, even if your code
is not yet ready for life in a post C++11 world. Take C++17's `std::string_view`
for example: this type was proposed for standardization largely based on
Google's experience with an internal type we called `StringPiece`. We've done
extensive work internally to mutate our `StringPiece` type to have the same API
as `string_view`, and now we are publishing it with Abseil - not as
`std::string_view`, but as `absl::string_view`.

Why would we do that? Doesn't that mean there are now two near-identical types?
Won't this cause confusion?

We think not: if you look at the preprocessor conditional structure in our
`string_view.h` you'll see that we are trying to identify whether your C++
installation has `std::string_view`. If you do, `absl::string_view` is defined
only as an alias to the standard type. If you don't, you get a C++11/C++14
compatible implementation of the type.  This means you can adopt Abseil, and for
types we are "pre-releasing" you can use the type from the `absl` namespace. As
soon as your project is built with the appropriate compiler/standard library
version, we'll fall away and leave you with the standard type, albeit spelled
funny. Better: as soon as you know that your project will only build with the
appropriate language version you can run tools that we will provide to change
the places that refer to `absl::string_view` to spell it `std::string_view`
&mdash; since those are the same type, this is safe to do, even across API
boundaries.

So, one reason you might want to adopt Abseil: early access to facilities from
upcoming C++ standard library releases, with a clear migration path.

### Compatibility with Google OSS Projects

Over the years, Google's needs for compatibility with other codebases and OSS
projects have changed.  A decade ago, most of our code was completely internal
and we would occasionally open-source something that we thought was cool. These
days, things are different: we want Protocol Buffers and gRPC to be healthy
independent projects. These APIs are the entry points into Google's Cloud
offerings &mdash; in conjunction with our view that Cloud providers function
best when customers aren't locked in, we want these entry points to be open and
sustainable. That said, the initial C++ versions of those projects came from a
codebase that made use of certain idioms and APIs, and it's been a source of
friction to not have a good supported OSS version of those APIs for those
projects to depend upon.

If you work heavily with Google Cloud or other Google OSS projects, adopting
Abseil should be a clear win: these libraries are going to be part of your
dependency chain anyway, and will be increasingly present in the APIs you
interact with.

### Upgrade Support

#### We Recommend That You Choose to Live at Head:

We've spoken publicly about Google's internal code base, and our efforts to keep
that code maintainable as it grows. With over 250M lines of C++ code and nearly
every project building from head, we've demonstrated a different approach to
software engineering: one largely free of version mismatch issues and one where
even the most common libraries can be refactored regularly, and safely. With
Abseil we aim to bring some of that experience to the Open Source world.

To that end, we make the following promises:

* If your code behaves according to our compatibility guidelines, it shouldn't
  break in the face of our changes.
* If we need to refactor an API that you depend on, we will provide a tool
  that should be able to perform the refactoring for well-behaved code.

In exchange, we want to see how you call us, and we want you to live at head.
Yes, you heard that right: live at head.

We believe that the current paradigm for software is inherently unsustainable:
dependency management is brutally complex.  Unsolvable "diamond dependency"
issues are common &mdash; the only ways to avoid these are to never change, or
to ensure that there aren't multiple versions. We prefer the latter, so we will
do what we can to get you to live at head along with us &mdash; if everything is
built from source at head, there can be no more diamond dependencies, branch
conflicts, and complicated discussions about merge policy.  All of that time
spent could be spent on more useful things, like actually writing code and
solving problems for users. Join with Abseil, and stop paying the
content-management tax!

#### If You Choose to Not Live at Head:

* You are of course free to fork Abseil, include it in your project and manage
  dependencies any way that is convenient for your development practices. 
* We will periodically mark a tag as "supported" and branch it &mdash; if we
  discover security issues or major performance problems, we'll update those
  branches. Our expectation is to do this every 6 months and support those
  branches for 2 years. 

### Production Experience

The libraries we are releasing come with a pedigree: many years of experience
using these APIs in Google's production environments. We've seen what works and
what doesn't, what designs lead to bugs, performance problems, and misuse. We've
long tried to keep designs simple &mdash; don't support features without strong
motivation, because every additional feature has a maintenance cost and imposes
constraints on future changes. What you see here is what we found to be a good
balance between simplicity and meeting the needs of production use and an
ever-evolving codebase.

For example, when we release our updated commandline flag API we will include a
novel feature &mdash; retired flags. These are flags that are recognized by the
parser, but ignored (and inaccessible to the code depending on commandline
flags). On its own, this feature may not make sense to most users. However, in a
massive shared codebase, where multiple products are cutting releases at
different times and with different job configurations, it can become difficult
to *remove* a flag once it has outlived its usefulness. Retired flags are
designed to provide a temporal bridge so that changes can be rolled out slowly
without breaking builds or production deployments.  Abseil is full of these
small features, making this a set of utility libraries well-suited for
supporting real production issues.

### Different Design Priorities than the Standard

The C++ standard holds two goals above all else:

* You don't pay (at runtime) for things you don't use
* The standard API should be usable for any domain (it is generally
  unopinionated about platform or problem domain).

Those are good goals, and perfectly sensible for something like a standard
library. That said, those aren't the only sensible goals &mdash; we could
instead decide to provide *excellent* support for the most common use cases and
little or no support for unusual cases.

For example, take our `absl::Time` and `absl::Duration` types. These are
conceptually equivalent to `std::chrono::time_point` and
`std::chrono::duration`, and in fact the two types inter-convert. However, the
standard requires usability in domains supporting durations from 32-bit
full-second to 128-bit nanosecond resolution over billions of years, so the
`std::chrono` abstractions are not types but class templates. On the upside,
such generic definitions are good no matter if you are doing physics simulations
or uptime tracking on embedded devices. On the downside, code using
`std::chrono` tends to be template-heavy and verbose.

Abseil tried a different approach: we've chosen a representation that optimizes
reasonably and still gives useful sub-nanosecond (non-floating-point) resolution
over a period of many thousands of years: obviously, this resolution won't work
in some domains, but for a wide range of tasks we can operate on concrete types
and work with simpler (non-template) code. Alternatively, on the other end of
the usability spectrum: in a domain where integral-second granularity is
sufficient, the standard would not dare force finer granularity types on users
&mdash; you shouldn't pay for what you don't use. We find the likelihood of
having CPU-bound time-processing code that cannot afford to use 96 or 128 bits
for time representation sufficiently unlikely compared to the cost of
time-programming bugs.

If your use cases are "normal" (or at least, in-line with what we've found to be
normal), Abseil may provide a useful counterpoint to the designs chosen by the
C++ standard. When we put out something that conflicts with the standard, we'll
be clear about why we are diverging and try our best to remain interoperable.

### Summary

We are explicitly prioritizing measured progress, careful API design,
prioritization for what we find to be common needs, and compatibility over time
&mdash; these are not the goals that every project should be optimizing for. If
your project is only going to live for a year, you may be perfectly served by
finding a cool new project, taking a single release of it and never upgrading
it. However, if you find yourself on a C++11 project looking forward to C++17
and beyond, or you use protobufs or gRPC, you might be well served with Abseil.
Or maybe you don't care much about what utility library you use, but are
intrigued by our "live at head" approach. Or maybe you know that your platforms
and use cases are well-defined, and want slightly more forgiving designs than
the standard will provide.  

Regardless of what makes Abseil interesting, we're glad you're taking a look.
Read up on our policies and the compatibility guidelines. Sign up for our
community mailing list. Take our libraries out for a spin &mdash; little things
like `StrCat` and `StrSplit` turn out to be surprisingly pleasant to have on
hand. And if you don't see anything interesting yet, be patient: this is just
the beginning of an ongoing process to make our
most-common utility libraries portable and available.  
