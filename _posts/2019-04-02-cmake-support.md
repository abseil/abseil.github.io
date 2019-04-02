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



CMake is a popular tool used to build multi-platform C++ projects.  Abseil has had a CMake buildsystem in some states since almost its inception, but it has always been considered secondary to Bazel.  This has now changed.

Abseil now offers full support for the CMake buildsystem.  We support usage either via CMake's `add_subdirectory` command for full source inclusion, or by local installation into your project.  Abseil LTS releases will be supported to be installed in system-wide locations (such as `/usr/local`, CMake's default install location) starting with the next after this blog post.

We hope that this will make it easier for users to adopt Abseil and for package managers to successfully and easily package Abseil.

[cmake-quickstart]: /docs/cpp/quickstart-cmake
[cmake-installs]: /docs/cpp/tools/cmake-installs
