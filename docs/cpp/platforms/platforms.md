---
title: Abseil Platforms
layout: docs
sidenav: side-nav-cpp.html
type: markdown
---

The Abseil C++ code is supported on the following platforms. (By "platforms",
we mean the union of operating system, architecture (e.g. little-endian vs.
big-endian), compiler, and standard library.

## Support Levels

Abseil has two basic levels of support:

<ul>
	<li><b>Supported</b> means that the indicated platform is officially
    supported. We pledge to test our code on that platform, have automated
	continuous integration (CI) tests for that platform, and bugs within that
	platform will be treated with high priority.</li>
	<li><b>Best Effort</b> means that we may or may not run continuous
	integration tests on the platform, but we are fairly confident that Abseil
	should work on the platform. Although we may not prioritize bugs on the
	associated platforms, we will make our best effort to support it, and we
	will welcome patches based on this platform. We may at some point
	officially support such a platform.</li>
</ul>

Any other platform that is not explicitly mentioned as **Supported** or
**Best Effort** is *not supported*. We will not accept patches for such
platforms and we will not prioritize bugs related to such platforms.

## C++11 and Above

Abseil requires a code base that at least supports C++11 and our code is
C++11-compliant. Often, we include C++11 versions of standard library
functionality available in a later version (e.g C++14 and C++17). Many of these
C++11 utlities will silently revert to their official standard library
functionality when compiled on C++14 and C++17
platforms. That is, we guarantee that our code will compile under any of the
following compilation flags:

Linux:

* gcc, clang: `-std=c++11`
* gcc, clang: `-std=c++14`
* clang < 5.0: `-std=c++1z`
* gcc, clang 5.0+: `-std=c++17`

Mac OS X:

* gcc, clang: `-std=c++11`
* gcc, clang: `-std=c++14`
* clang < 5.0: `-std=c++1z`
* gcc, clang 5.0+: `-std=c++17`

Windows:

* msvc `/std:c++14`
* msvc `/std:c++latest`

## Supported Platforms

The document below lists each platform, broken down by Operating System,
Archiecture, Specific Compiler, and Standard Library implementation.

### Linux

**Supported**

<table width="80%">
  <col width="360">
  <col width="120">
  <tbody>
    <tr>
      <th>Operating System/Architecture</th>
      <th>Compilers</th>
      <th>Standard Libraries</th>
    </tr>
    <tr>
      <td>Linux, little-endian, 64-bit</td>
      <td>gcc 4.8+<br/>clang 3.3+</td>
      <td>libstdc++<br/>libcxx</td>
    </tr>
  </tbody>
</table>

**Best Effort**

<table width="80%">
  <col width="360">
  <col width="120">
  <tbody>
    <tr>
      <th>Operating System/Architecture</th>
      <th>Compilers</th>
      <th>Standard Libraries</th>
    </tr>
    <tr>
      <td>ChromeOS, little-endian, 64-bit</td>
      <td>gcc 4.9+, clang 5.0+</td>
      <td>libstdc++</td>
    </tr>
  </tbody>
</table>

### Mac OS X / Darwin Family

**Supported**

<table width="80%">
  <col width="360">
  <col width="120">
  <tbody>
    <tr>
      <th>Operating System/Architecture</th>
      <th>Compilers</th>
      <th>Standard Libraries</th>
    </tr>
    <tr>
      <td>Mac OSX 10.7+, endian-neutral, 64-bit</td>
      <td>XCode 7.3.1+</td>
      <td>libc++</td>
    </tr>
    <tr>
      <td>iOS 7+, endian-neutral, 64-bit</td>
      <td>XCode 7.3.1+</td>
      <td>libc++</td>
    </tr>
  </tbody>
</table>

**Best Effort**

<table width="80%">
  <col width="360">
  <col width="120">
  <tbody>
    <tr>
      <th>Operating System/Architecture</th>
      <th>Compilers</th>
      <th>Standard Libraries</th>
    </tr>
    <tr>
      <td>watchOS 2+, endian-neutral, 64-bit</td>
      <td>XCode 7.3.1+</td>
      <td>libc++</td>
    </tr>
  </tbody>
</table>

### Windows

**Supported**

<table width="80%">
  <col width="360">
  <col width="120">
  <tbody>
    <tr>
      <th>Operating System/Architecture</th>
      <th>Compilers</th>
      <th>Standard Libraries</th>
    </tr>
    <tr>
      <td>Windows, little-endian, 32/64-bit</td>
      <td>MVC 2015, MSVC 2017</td>
      <td>msvc</td>
    </tr>
  </tbody>
</table>

**Best Effort**

<table width="80%">
  <col width="360">
  <col width="120">
  <tbody>
    <tr>
      <th>Operating System/Architecture</th>
      <th>Compilers</th>
      <th>Standard Libraries</th>
    </tr>
    <tr>
      <td>Windows, little-endian, 32/64-bit</td>
      <td>clang+</td>
      <td>???</td>
    </tr>
  </tbody>
</table>

## Android

**Best Effort**

<table width="80%">
  <col width="360">
  <col width="120">
  <tbody>
    <tr>
      <th>Operating System/Architecture</th>
      <th>Compilers</th>
      <th>Standard Libraries</th>
    </tr>
    <tr>
      <td>Android NDK r9b+</td>
      <td>gcc 4.8+</td>
      <td>libc++, libstdc++</td>
    </tr>
  </tbody>
</table>
