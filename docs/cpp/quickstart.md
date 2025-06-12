---
title: "C++ Quickstart"
layout: docs
sidenav: side-nav-cpp.html
type: markdown
---

# C++ Quickstart

Note: this Quickstart uses [Bazel](https://bazel.build/) version 7.0 or higher
as the official build system for Abseil, which is supported on most major
platforms (Linux, Windows, macOS, for example) and compilers.

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
*   A compatible C++ compiler *supporting at least C++17*. Most major compilers
    are supported.

Although you are free to use your own build system, most of the documentation
within this guide will assume you are using [Bazel](https://bazel.build/).

To download and install Bazel (and any of its dependencies), consult the
[Bazel Installation Guide](https://docs.bazel.build/versions/master/install.html).

## Set Up a Bazel Workspace to Work with Abseil

A
[Bazel workspace](https://docs.bazel.build/versions/master/build-ref.html#workspace)
is a directory on your filesystem that contains the source files for the
software you want to build. Each workspace directory has a text file named
`MODULE.bazel` which may be empty, or may contain references to external
dependencies required to build the outputs.

First, set up your development directory:

```
mkdir my_workspace && cd my_workspace
```

As of Bazel 7.0, the recommended way to consume Abseil is through the
[Bazel Central Registry](https://registry.bazel.build/modules/abseil-cpp). To do
this, create a `MODULE.bazel` file in the root directory of your Bazel workspace
with the following content:

```
# MODULE.bazel

# Choose the most recent version available at
# https://registry.bazel.build/modules/abseil-cpp.
bazel_dep(name = "abseil-cpp", version = "20240116.0")
```

This will bring in Abseil along with all of its dependencies into your new Bazel
workspace.

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

### Creating Your BUILD.bazel file

Now, create a `BUILD.bazel` file with a `cc_binary` rule in the same directory
as your `hello_world.cc` file:

```
cc_binary(
  name = "hello_world",
  deps = ["@abseil-cpp//absl/strings"],
  srcs = ["hello_world.cc"],
)
```

We declare a dependency on the Abseil strings library
(`@abseil-cpp//absl/strings`) using the prefix we declared in our `MODULE.bazel`
file (`@abseil-cpp`).

For more information on how to create Bazel `BUILD.bazel` files, consult the
[Bazel Tutorial](https://docs.bazel.build/versions/master/tutorial/cpp.html).

Build our target (`hello_world`) and run it:

<pre><code>$ <b>bazel build //:hello_world</b>
INFO: Analysed target //:hello_world (12 packages loaded).
INFO: Found 1 target...
Target //:hello_world up-to-date:
  bazel-bin/hello_world
INFO: Elapsed time: 0.180s, Critical Path: 0.00s
INFO: Build completed successfully, 1 total action

$ <b>bazel run //:hello_world</b>
INFO: Running command line: bazel-bin/hello_world
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
