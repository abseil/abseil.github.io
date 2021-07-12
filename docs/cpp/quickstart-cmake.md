---
title: "C++ Quickstart With CMake"
layout: docs
sidenav: side-nav-cpp.html
type: markdown
---

# C++ Quickstart With CMake

This document is designed to allow you to get the Abseil development
environment up and running using CMake. We recommend that each person starting
development with Abseil code at least run through this quick tutorial.  If your
project uses [Bazel](https://bazel.build/) instead, please find the
[Bazel Quickstart](/docs/cpp/quickstart).

## Prerequisites

Running the Abseil code within this tutorial requires:

*   A compatible platform (e.g. Windows, macOS, Linux, etc.). Most platforms are
    fully supported. Consult the [Platforms Guide](platforms/platforms) for more
    information.
*   A compatible C++ compiler *supporting at least C++11*. Most major compilers
    are supported.
*   [Git](https://git-scm.com/) for interacting with the Abseil source code
    repository, which is contained on [GitHub](http://github.com). To install
    Git, consult the [Set Up Git](https://help.github.com/articles/set-up-git/)
    guide on GitHub.
*   [CMake](https://cmake.org/) for building your project and Abseil. Abseil
    supports CMake 3.5+.

## Getting the Abseil Code

Building and testing Abseil is relatively straightforward:

```
# Change to the directory where you want to create the code repository
$ cd ~
$ mkdir Source && cd Source
$ git clone https://github.com/abseil/abseil-cpp.git
Cloning into 'abseil-cpp'...
remote: Enumerating objects: 149, done.
...
Resolving deltas: 100% (1083/1083), done.
$
```

Git will create the repository within a directory named `abseil-cpp`.
Navigate into this directory and run all tests:

```
$ cd abseil-cpp
$ mkdir build && cd build
$ cmake -DBUILD_TESTING=ON -DABSL_USE_GOOGLETEST_HEAD=ON -DCMAKE_CXX_STANDARD=11 ..
...
-- Configuring done
-- Generating done
-- Build files have been written to: ${PWD}
```

`CMAKE_CXX_STANDARD=11` instructs CMake to build using the C++11 standard, which
is our minimum language level of support.

Now you can build the CMake target tests:

```
$ cmake --build . --target all
...
[ 99%] Linking CXX executable absl_flat_hash_map_test
[ 99%] Built target absl_flat_hash_map_test
[100%] Linking CXX executable absl_hash_test
[100%] Built target absl_hash_test
```

Once you have built the CMake tests, run them in parallel with the `ctest`
command:

```

$ ctest
Test project ${PWD}
      Start  1: absl_absl_exception_safety_testing_test
...
100% tests passed, 0 tests failed out of 98
$
```

## Creating and Running a Binary

Now that you've obtained the Abseil code and verified that you can build and
test it, you're ready to use it within your own project.

### Linking Your Code to the Abseil Repository

First, create (or select) a source code directory for your work. This directory
should generally not be the `abseil-cpp` directory itself -- we prefer that
`abseil-cpp` reside as a subdirectory of your project's source tree.

```
# Change to your main development directory and create a new development
# directory. (If you already have a development directory you'd wish to use,
# you can use that.)
$ cd ~/Source
$ mkdir TestProject; cd TestProject
$
```

### Creating Your Test Code

Within your `TestProject` create an `examples` directory and populate it with a
copy of the Abseil source code.

```
$ mkdir examples; cd examples
$ git clone https://github.com/abseil/abseil-cpp.git
Cloning into 'abseil-cpp'...
$
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
}
```

Note that we include an Abseil header file using the `absl` prefix.

### Creating Your CMakeLists.txt File

Now, create a `CMakeLists.txt` file within your `examples` directory like the following:

```
cmake_minimum_required(VERSION 3.5)

project(my_project)

# Abseil requires C++11
set(CMAKE_CXX_STANDARD 11)

# Process Abseil's CMake build system
add_subdirectory(abseil-cpp)

add_executable(hello_world hello_world.cc)

# Declare dependency on the absl::strings library
target_link_libraries(hello_world absl::strings)
```

For more information on how to create CMakeLists.txt files, consult the
[CMake Tutorial](https://cmake.org/cmake-tutorial/).

Configure the CMake build from a fresh binary directory. This configuration is
called an "out of source" build and is the preferred method for CMake projects.

```
$ cd ~/Source/TestProject/examples
$ mkdir build && cd build
$ cmake ..
-- The C compiler identification is GNU 7.3.0
-- The CXX compiler identification is GNU 7.3.0
...
-- Build files have been written to: ~/Source/CMakeTest/TestProject/examples/build
```

Now build our target ("hello_world"):

```
$ cmake --build . --target hello_world
Scanning dependencies of target strings_internal
[  3%] Building CXX object abseil-cpp/absl/strings/CMakeFiles/strings_internal.dir/internal/ostringstream.cc.o
...
[100%] Linking CXX executable hello_world
[100%] Built target hello_world
```

Now run your binary:

```
$ ./hello_world
Joined string: foo-bar-baz
$
```

Congratulations! You've created your first binary using Abseil code.

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
