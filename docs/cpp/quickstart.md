---
title: "C++ Quickstart"
layout: docs
sidenav: side-nav-cpp.html
type: markdown
---

# C++ Quickstart

Note: this Quickstart uses Bazel as the official build system for Abseil, which
is supported on most major platforms (Linux, Windows, macOS, for example) and
compilers. The Abseil source contains a `WORKSPACE` file and `BUILD.bazel` files
for that purpose.

This document is designed to allow you to get the Abseil development
environment up and running. We recommend that each person starting
development with Abseil code at least run through this quick tutorial.

Abseil also supports building with CMake.  For information, please see the
[CMake Quickstart](/docs/cpp/quickstart-cmake).

## Prerequisites

Running the Abseil code within this tutorial requires:

*   A compatible platform (e.g. Windows, macOS, Linux, etc.). Most platforms are
    fully supported. Consult the [Platforms Guide](platforms/platforms) for more
    information.
*   A compatible C++ compiler *supporting at least C++11*. Most major compilers
    are supported.

Although you are free to use your own build system, most of the documentation
within this guide will assume you are using [Bazel](https://bazel.build/).

To download and install Bazel (and any of its dependencies), consult the
[Bazel Installation Guide](https://docs.bazel.build/versions/master/install.html).

## Set Up a Bazel Workspace to Work with Abseil

A [Bazel
workspace](https://docs.bazel.build/versions/master/build-ref.html#workspace) is
a directory on your filesystem that contains the source files for the software
you want to build. Each workspace directory has a text file named `WORKSPACE`
which may be empty, or may contain references to external dependencies required
to build the outputs.

First, set up your development directory:

```
mkdir my_workspace && cd my_workspace
```

A common and recommended way to consume Abseil is to use [Bazel's external
dependencies
feature](https://docs.bazel.build/versions/master/external.html). One way to do
this is with an [`http_archive`
rule](https://docs.bazel.build/versions/master/repo/http.html#http_archive). To
do this, create a `WORKSPACE` file in the root directory of your Bazel workspace
with the following content:

```
load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

http_archive(
  name = "com_google_absl",
  urls = ["https://github.com/abseil/abseil-cpp/archive/98eb410c93ad059f9bba1bf43f5bb916fc92a5ea.zip"],
  strip_prefix = "abseil-cpp-98eb410c93ad059f9bba1bf43f5bb916fc92a5ea",
)
```

In the above example, a ZIP archive of the Abseil code is downloaded from
GitHub. `98eb410c93ad059f9bba1bf43f5bb916fc92a5ea` is the `git` commit hash of
the Abseil version being used (it is recommended that this value be updated
often to point to the most recent commit). Bazel strongly recommends that you
provide the SHA-256 of the specified file within the `sha256` field of the
`http_archive` rule. See the [Bazel reference](
https://docs.bazel.build/versions/master/repo/http.html#http_archive-sha256)
for more information.

Bazel also requires a dependency on the [`rules_cc`
repository](https://github.com/bazelbuild/rules_cc) to build C++ code, so add
the following `http_archive` rule to the `WORKSPACE` file:

```
http_archive(
  name = "rules_cc",
  urls = ["https://github.com/bazelbuild/rules_cc/archive/262ebec3c2296296526740db4aefce68c80de7fa.zip"],
  strip_prefix = "rules_cc-262ebec3c2296296526740db4aefce68c80de7fa",
)
```

If you wish to run Abseil's unit tests to verify it works properly in your
environment, you will also need to add a dependency on
[GoogleTest](https://github.com/google/googletest):

```
http_archive(
  name = "com_google_googletest",
  urls = ["https://github.com/google/googletest/archive/011959aafddcd30611003de96cfd8d7a7685c700.zip"],
  strip_prefix = "googletest-011959aafddcd30611003de96cfd8d7a7685c700",
)
```

Some targets are benchmarks. These targets require a dependency on the
[Google Benchmark](https://github.com/google/benchmark) framework:

```
http_archive(
    name = "com_github_google_benchmark",
    urls = ["https://github.com/google/benchmark/archive/bf585a2789e30585b4e3ce6baf11ef2750b54677.zip"],
    strip_prefix = "benchmark-bf585a2789e30585b4e3ce6baf11ef2750b54677",
    sha256 = "2a778d821997df7d8646c9c59b8edb9a573a6e04c534c01892a40aa524a7b68c",
)
```

Now you can optionally run Abseil's unit tests with a single `bazel` command:

<pre><code>$ <b>bazel test --test_tag_filters=-benchmark @com_google_absl//...</b>
INFO: Analyzed 346 targets (42 packages loaded, 1890 targets configured).
INFO: Found 189 targets and 157 test targets...
...
Executed 157 out of 157 tests: 157 tests pass.
INFO: Build completed successfully, 1660 total actions</code></pre>

## Creating and Running a Binary

Now that you've setup a Bazel workspace with Abseil as a dependency, you're
ready to use it within your own project.

In this example, we will create a `hello_world.cc` C++ file within your Bazel
workspace directory:

```
#include <iostream>
#include <string>
#include <vector>

#include "absl/strings/str_join.h"

int main() {
  std::vector<std::string> v = {"foo", "bar", "baz"};
  std::string s = absl::StrJoin(v, "-");

  std::cout << "Joined string: " << s << "\n";

  return 0;
}
```

Note that we include an Abseil header file using the `absl` prefix.

### Creating Your BUILD File

Now, create a `BUILD` file with a `cc_binary` rule in the same directory as your
`hello_world.cc` file:

```
cc_binary(
  name = "hello_world",
  deps = ["@com_google_absl//absl/strings"],
  srcs = ["hello_world.cc"],
)
```

For more information on how to create Bazel BUILD files, consult the
[Bazel Tutorial](https://docs.bazel.build/versions/master/tutorial/cpp.html).

We declare a dependency on the Abseil strings library (`//absl/strings`) using
the prefix we declared in our `WORKSPACE` file (`@com_google_absl`).

Build our target ("hello_world") and run it:

<pre><code>$ <b>bazel build //examples:hello_world</b>
INFO: Analysed target //examples:hello_world (12 packages loaded).
INFO: Found 1 target...
Target //examples:hello_world up-to-date:
  bazel-bin/examples/hello_world
INFO: Elapsed time: 0.180s, Critical Path: 0.00s
INFO: Build completed successfully, 1 total action

$ <b>bazel run //examples:hello_world</b>
INFO: Running command line: bazel-bin/examples/hello_world
Joined string: foo-bar-baz</code></pre>

Congratulations! You've created your first binary using Abseil code. If you want
to see a full, working example of code using Abseil, see the [`bazel-hello`
directory in the abseil-hello
repository](https://github.com/abseil/abseil-hello/tree/master/bazel-hello).

## What's Next

* Read our [design philosophy](/about/philosophy) and
  [compatibility guidelines](/about/compatibility), if
  you haven't already.
* Read through the C++ developer guide.
* Consult the Abseil C++ .h header files, which contain valuable reference
  information.
* Read our
  [contribution guidelines](/community/contribute), if
  you intend to submit code to our repository.
