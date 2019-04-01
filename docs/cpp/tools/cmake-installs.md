---
title: "Using Abseil via CMake Installation Binaries"
layout: docs
sidenav: side-nav-cpp.html
type: markdown
---

# Using Abseil via CMake Installation Binaries

This document describes how to use prebuilt static libraries of Abseil within a
CMake build environment. This is often how package managers will ship Abseil and
also may cut down on your rebuild times. The Abseil footprint in this case will
consist of the API header files, but instead of source code will only include
Abseil's pre-compiled libraries.

## Initialize Your Project

Create a new directory, `CMakeProject` in your source directory:

```
$ mkdir ~/Source/CMakeProject/
```

This project will be injected with the Abseil prebuilt static libraries and
header files.

## Generate the Abseil Static Binaries

Clone Abseil into its own source directory.

```
# Change to the directory where you want to create the code repository
$ cd ~/Source
$ git clone https://github.com/abseil/abseil-cpp.git
Cloning into 'abseil-cpp'...
remote: Total 1935 (delta 1083), reused 1935 (delta 1083)
Receiving objects: 100% (1935/1935), 1.06 MiB | 0 bytes/s, done.
Resolving deltas: 100% (1083/1083), done.
$
```

Now, invoke CMake to configuration its build, passing `CMAKE_INSTALL_PREFIX` to
instruct CMake to use the passed directory as its installation location instead
of the current directory.

Although it might be tempting to install Abseil into a common location usable by
multiple projects, it is unsafe and prone to One-Definition Rule (ODR)
violations to install Abseil's HEAD branch into a system install directory such
as `/usr/local`.

```
$ cd abseil-cpp
$ mkdir build && cd build
$ cmake .. -DCMAKE_INSTALL_PREFIX=~/Source/CMakeProject/install
-- The C compiler identification is GNU 7.3.0
-- The CXX compiler identification is GNU 7.3.0
...
-- Build files have been written to: ~/Source/abseil-cpp/build
$
```

Finally, build Abseil, instructing CMake to use the aforementioned install
location:

```
$ cmake --build . --target install
Scanning dependencies of target spinlock_wait
[  1%] Building CXX object absl/base/CMakeFiles/spinlock_wait.dir/internal/spinlock_wait.cc.o
...
-- Installing: ~/Source/CMakeProject/install/lib/libabsl_bad_variant_access.a
$
```

Notice how CMake automatically created `CMakeProject/install` in `~/Source`.
Header files will be generated within the `install/include` directory and
compiled libraries will be built within the `install/lib` directory.

## Create and Run Your Project

Navigate back to your project's directory:

```
$ cd ~/Source/CMakeProject
```

Now, create a `hello_world.cc` C++ file within your `CMakeProject`
directory:

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

Our `CMakeLists.txt` for this local project needs to be slightly different than
the one we used in the
[CMake Quickstart](/docs/ccp/quickstart-cmake) -- we use
`find_package` to import Abseil's targets from our local `install` directory.

```
cmake_minimum_required(VERSION 3.5)

project(my_project)

# Abseil requires C++11
set(CMAKE_CXX_STANDARD 11)

# Import Abseil's CMake targets
find_package(absl REQUIRED)

add_executable(hello_world hello_world.cc)

# Declare dependency on the absl::strings library
target_link_libraries(hello_world absl::strings)
```

Now create a build directory and invoke CMake to configure and build the
project. Note how we set `CMAKE_PREFIX_PATH` to the `install` directory we
installed Abseil into previously. This tells CMake where to look for the Abseil
installation.

```
$ mkdir build && cd build
$ cmake .. -DCMAKE_PREFIX_PATH=~/Source/InstallProject/install
...
-- Build files have been written to: ~/Source/InstallProject/build
$ cmake --build . --target hello_world
[ 50%] Building CXX object CMakeFiles/hello_world.dir/hello_world.cc.o
[100%] Linking CXX executable hello_world
[100%] Built target hello_world
$
```

We can now run our application:

```
$ ./hello_world
Joined string: foo-bar-baz
$
```

Congratulations! You've created your first binary using installed Abseil
libraries!

