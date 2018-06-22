---
title: Abseil Release Management
layout: about
sidenav: side-nav-about.html
type: markdown
---

# Abseil Release Management

Abseil provides its repository as source code, and specifically does not offer
binary releases. Instead, we encourage you to either "live at head" (build
from the latest version of Abseil) or, if necessary, build against a known,
supported branch, known as a Long Term Support (LTS) branch.

This document outlines the specifics of what releases we provide, and options
for how you build and distribute Abseil within your source code, binary, or
library.

## Long Term Support (LTS) Branches

Abseil encourages developers to ["live at head"](/blog/20171004-cppcon-plenary)
but we understand that philosophy may not work for everyone. We are therefore
providing snapshots of the Abseil codebase. These snapshots are available as
"Long Term Support" (LTS) branches of Abseil, and we intend to provide a new
snapshot every 6 months or so.

We pledge to support these LTS snapshots for at least 2 years. If critical bug
fixes, such as security issues, require us to change Abseil, we will also change
them within any supported LTS snapshot.

NOTE: we don't want you to think of these snapshots as "versions." They are
simply a snapshot of the codebase at a specific point in time. If you cannot
build from source or otherwise live at head, prefer to use the latest LTS
branch of Abseil instead.

## Obtaining an LTS Branch

The set of LTS branches of Abseil is available on our
[Long Term Support (LTS) Branches][LTS] page. As LTS branches are added to
this page, entries will be added to the list. We will also list any critical
fixes to specific LTS branches on this page.

## Options for Using Abseil Code In Your Source Code or Binary

Including Abseil code in your project, as long as it is provided as source
code or within your own binary, is relatively straightfoward. You have a few
options, listed in order of higher preference:

* Live at HEAD, depend on and build the latest snapshot of Abseil.<br/><br/>
    * *ENCOURAGED*: For now, this requires manually updating the snapshot of
      Abseil used, for example, within a Bazel `WORKSPACE` file. Note that if
      you build from source and use an unsupported build system, we can't
      support you at the moment, though we are open to adding support if you
      [contact us](mailto:abseil-io@googlegroups.com) or provide us with a pull
      request.
*   Tie your release to a specific snapshot of Abseil. This can be
    done in a few ways:<br/><br/>
    * *ALLOWED*: Build Abseil from source at a Long Term Support (LTS)
      branch. LTS branches of Abseil are “supported” branches we aim to cut
      every 6 months, which will be frozen except for critical bug fixes, such
      as security patches. We enforce an LTS branch's integrity through the use
      of inline namespaces.
    * *DISCOURAGED*: Build Abseil from source at a specific commit. This is
      straightforward, but you’re on your own if problems pop up.
    * *DISCOURAGED*: Copy Abseil code into your project and provide it within
      your own repository. Obviously, this makes maintenance difficult, though
      not impossible.

## Options for Including Abseil Code In Your Library

Including Abseil code in your library requires more care, as that library in
turn may be used by other projects that depend on Abseil. In particular, to
avoid ODR violations, your library must be built with the same compiler flags
as other binaries or libraries using Abseil. See
[Abseil Compiler Flags](https://abseil.io/docs/cpp/platforms/compilerflags).
(Building Abseil with the different compiler flags would cause ABI changes
between different builds of Abseil.)

* *ENCOURAGED*: Distribute your source code, so users build both your library
  and Abseil at the same time.
* *ALLOWED*: Distribute a *static* library built with an
  [LTS branch of Abseil][LTS]. Because LTS branches use inline namespaces for
  all `absl::` symbols, collisions between potential Abseil "versions" should
  not occur, though your library may incur code bloat.
* *DISCOURAGED*: Distribute a *static* library not based on an LTS branch of
  Abseil, that exports no Abseil symbols. This option implies that no Abseil
  types exist within your library's public API, and all Abseil symbols must be
  hidden by the linker.
* *DISCOURAGED*: Distribute a *dynamic* library. Abseil does not support dynamic
  loading or unloading of any shared libraries at this time. We are
  investigating if we can support dynamic loading without unloading. Consult
  our [Compatibility Guidelines](https://abseil.io/about/compatibility) when in
  doubt.

[LTS]: https://github.com/abseil/abseil-cpp/blob/master/LTS.md
