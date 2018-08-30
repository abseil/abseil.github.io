---
title: "Using clang-tidy Checks for Abseil"
layout: docs
sidenav: side-nav-cpp.html
type: markdown
---

# Using clang-tidy Checks for Abseil

## Why Use clang-tidy?

**Clang-tidy** is a Clang-based C++ “linter” tool that provides a framework to
diagnose and fix common programming errors, and now incorporates some
Abseil-specific checks that look for a variety of common errors when using
Abseil, including known bugs, whether code uses Abseil’s APIs efficiently, and
whether code meets Abseil’s
[compatibility guidelines](/about/compatibility).

These checks are easy to run on all new code you write and when integrated into
your programming practice will eliminate common errors and cut down on time
spent debugging. Along with Abseil specific checks, `clang-tidy` also provides
more generic checks that look for other bug-prone code and ways to improve
readability. See
[Clang-Tidy Checks](http://clang.llvm.org/extra/clang-tidy/checks/list.html)
for a list of all checks that are currently available.

## Setting Up clang-tidy

`Clang-tidy` is a component of the **Clang** framework, and is being
continuously upgraded with new checks, but only periodically contains updates
including the latest checks. To download the most recent pre-built binaries from
LLVM, see the
[LLVM Download Page](http://releases.llvm.org/download.html).

If the most recent binary releases do not match the latest list of available
`clang-tidy` checks, you will need to build the repository from source. See
[Getting Started with the LLVM System](http://llvm.org/docs/GettingStarted.html#getting-started-with-the-llvm-system),
for instructions, making sure you check out **clang-tools-extra**, the
repository where `clang-tidy` lives.

## Running clang-tidy Checks

Now that you have downloaded `clang-tidy` you are ready to start running the
checks! For documentation on how to run these checks, see
[Using clang-tidy](http://clang.llvm.org/extra/clang-tidy/#using-clang-tidy).
Note that Abseil checks are not included by default. To run Abseil-specific
checks use the following commands:

```
$ clang-tidy YourProject.cpp -checks=abseil-*
  // runs the default clang-tidy checks and Abseil specific checks
$ clang-tidy YourProject.cpp -checks=-*,abseil-*
  // runs only Abseil specific checks
```

## Contributing to clang-tidy

The `clang-tidy` framework makes it easy to use checks that have already been
written, but it also makes it easy to write your own checks. If you come up with
an idea for a new check that you think would be helpful, it is easy to write new
`clang-tidy` checks and share them with others. See
[Getting Involved](http://clang.llvm.org/extra/clang-tidy/#getting-involved) for
more information on how to write, configure, test and share your check(s).
