---
title: "Abseil Support for CMake"
layout: blog
sidenav: side-nav-blog.html
published: true
permalink: blog/20190402-cmake-support
type: markdown
category: blog
excerpt_separator: <!--break-->
---

By [Jon Cohen](mailto:cohenjon@google.com), Abseil Engineer

CMake is a popular tool used to build multi-platform C++ projects.
Abseil has had unofficial CMake support for some time, but support
has never been as robust as that for Bazel. We are happy to
announce that Abseil now fully supports the CMake build system.

<!--break-->

Abseil supports CMake through the `add_subdirectory` command for
full source inclusion, or by [local installation][cmake-installs]
into your project. Future Abseil LTS releases will be supported
for installation in system-wide locations (such as `/usr/local`,
CMake's default install location).

We hope that this support will make it easier for users to adopt
Abseil and for package managers to successfully and easily
package Abseil.

For more information on getting Abseil working with CMake, consult
our [CMake Quickstart][cmake-quickstart]

[cmake-quickstart]: /docs/cpp/quickstart-cmake
[cmake-installs]: /docs/cpp/tools/cmake-installs
