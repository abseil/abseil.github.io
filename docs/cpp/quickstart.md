---
title: Quickstart
layout: docs
sidenav: side-nav-cpp.html
type: markdown
---

## Prerequisites

Running the Abseil code within this tutorial requires:

* A compatible platform (e.g. Windows, Mac OS X, Linux, etc.). Most platforms
  are fully supported. Consult the
  [Platforms Guide](/docs/cpp/platforms/platforms) for more information.
* A compatible C++ compiler *supporting at least C++11*. Most major compilers
  are supported.
* [Git](https://git-scm.com/) for interacting with the Abseil source code
  repository, which is contained on [GitHub](http://github.com). To install Git,
  consult the [Set Up Git](https://help.github.com/articles/set-up-git/) guide
  on GitHub.

<p class="note">
Note: this Quickstart uses Bazel as the official build system for Abseil,
which is supported on most major platforms (Linux, Windows, MacOS, for example)
and compilers. The Abseil source code assumes you are using Bazel and contains
`BUILD.bazel` files for that purpose.
</p>

Although you are free to use your own build system, most of the documentation
within this guide will assume you are using [Bazel](https://bazel.build/).

To download and install Bazel (and any of its dependencies), consult the
[Bazel Installation Guide](https://docs.bazel.build/versions/master/install.html).

## Getting the Abseil Code

Once you have Bazel and Git installed, you can obtain the Abseil code from its
repository on GitHub:

```
# Change to the directory where you want to create the code repository
$ cd ~
$ mkdir Source; cd Source
$ git clone  https://github.com/abseil/abseil-cpp.git
Cloning into 'abseil-cpp'...
remote: Total 1935 (delta 1083), reused 1935 (delta 1083)
Receiving objects: 100% (1935/1935), 1.06 MiB | 0 bytes/s, done.
Resolving deltas: 100% (1083/1083), done.
$
```

Git will create the repository within a directory named `abseil-cpp`.
Navigate into this directory and run all tests:

```
$ cd abseil-cpp
$ bazel test //absl/...
..............
INFO: Found 12 targets...
INFO: Elapsed time: 3.677s, Critical Path: 0.03s
$
```

## Creating and Running a Binary

Now that you've obtained the Abseil code and verified that you can build and
test it, you're ready to use it within your own project.

### Linking Your Code to the Abseil Repository

First, create (or select) a source code directory for your work. This directory
should generally not be the `abseil-cpp` directory itself;
instead, you will link into that repository from your own source directory.

```
# Change to your main development directory and create a new development
# directory. (If you already have a development directory you'd wish to use,
# you can use that.)
$ cd ~/Source
$ mkdir TestProject; cd TestProject
```

Bazel allows you to link other Bazel projects using `WORKSPACE` files in the
root of your development directories. To add a link to your local Abseil
repository within your new project, add the following into a `WORKSPACE` file:

```
local_repository(
  # Name of the Abseil repository. This name is defined within Abseil's
  # WORKSPACE file, in its `workspace()` metadata
  name = "com_google_absl",

  # NOTE: Bazel paths must be absolute paths. E.g., you can't use ~/Source
  path = "/PATH_TO_SOURCE/Source/abseil-cpp",
)
```

The "name" in the `WORKSPACE` file identifies the name you will use in Bazel
`BUILD` files to refer to the linked repository (in this case
"com_google_absl").

### Creating Your Test Code

Within your `TestProject` create an `examples` directory:

```
$ cd TestProject; mkdir examples; cd examples
```

Now, create a `hello_world.cc` C++ file within your `examples` directory:

```
#include <iostream>
#include <string>
#include <vector>
#include "absl/strings/str_join.h"

int main() {
  std::vector<std::string> v = {"foo","bar","baz"};
  std::string s = absl::StrJoin(v, "-");

  std::cout << "Joined string: " << s << "\n";

  return(0);
}
```

Note that we include an Abseil header file using the `absl` prefix.

### Creating Your BUILD File

Now, create a `BUILD` file within your `examples` directory like the following:

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

```
# It's often good practice to build files from the workspace root
$ cd ~/Source/TestProject
$ bazel build //examples:hello_world
INFO: Analysed target //examples:hello_world (12 packages loaded).
INFO: Found 1 target...
Target //examples:hello_world up-to-date:
  bazel-bin/examples/hello_world
INFO: Elapsed time: 0.180s, Critical Path: 0.00s
INFO: Build completed successfully, 1 total action

$ bazel run //examples:hello_world
INFO: Running command line: bazel-bin/examples/hello_world
Joined string: foo-bar-baz
$
```

Congratulations! You've created your first binary using Abseil code.

## What's Next

* Read our [design philosophy](/about/philosophy) and
  [compatibility guidelines](/about/compatibility), if you haven't
  already.
* Read through the C++ developer guide.
* Consult the Abseil C++ .h header files, which contain valuable reference
  information.
* Read our [contribution guidelines](/community/contribute), if you intend to
  submit code to our repository.
