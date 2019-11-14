---
title: "Abseil Option Configurations"
layout: docs
sidenav: side-nav-cpp.html
type: markdown
---

# Abseil Option Configurations

Abseil provides a file (`options.h`) for static configuration of certain
implementation details. Such static configurations are not often necessary but
may be useful for providers of binaries/libraries which wish to ensure that
their built-upon copies of Abseil are exactly the same.

## Motivation

Abseil promises no ABI stability, even from one day to the next. Two different
source revisions of Abseil cannot be safely used in the same program. If two
libraries in your program depend on Abseil, they must be built against the exact
same version of Abseil, or things will break through violation of the One
Definition Rule: loudly if you're lucky, or subtly if not. This “diamond
dependency problem” is a common problem with all library code, and is why we
recommend building all code in your project from source.

However, while we discourage relying on compiled representations of libraries,
we recognize this isn't always possible for providers of binaries or compiled
libraries (such as package managers). This options mechanism is provided to
allow those providers to ensure that copies of Abseil use the same
implementation.

## Caveats

Two copies of Abseil configured with different options are incompatible, in
exactly the same way that two different source snapshots of Abseil are
incompatible. Abseil options must be set consistently across an entire program.
They cannot be changed on a per-library basis.

These options are dangerous if used incorrectly, and can only be safely used in
some contexts.

## Usage

We have placed Abseil options in a common file, `absl/base/options.h`. The
options file documents and enforces the feature selections used to build the
Abseil library. Setting these flags on the command like (via a `-D` compiler
flag, for instance) won't work: you must edit the `options.h` file directly, and
distribute the patched `options.h` file, so that users are forced to compile
their program with the same set of options that were used to build the
pre-compiled library.

A good rule of thumb is that it is safe to edit the options file only if you
maintain the source of truth of Abseil for your build. Some examples of this:

* You are using a Bazel WORKSPACE file to import Abseil and build from source,
  and are using the `patches=` feature of the `http_archive()` rule to override
  the options consistently.
* You maintain a copy of Abseil in your source code repository which your
  project builds against.
* You are a binary package manager, and are installing Abseil headers on users’
  systems.

Because of the increased testing burden this imposes, we plan to keep the set of
options we support small. If you change any options, we recommend that you run
the Abseil unit tests, to ensure your settings work with your toolchain. The
default options we ship with reflect how we use Abseil internally. This is the
configuration that is “battle tested” in Google’s C++ codebase.
