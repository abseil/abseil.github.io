---
title: "Abseil Platforms"
layout: docs
sidenav: side-nav-cpp.html
type: markdown
---

# Abseil Platforms

The Abseil C++ code is supported on the following platforms. By "platforms",
we mean the union of operating system, architecture (e.g. little-endian vs.
big-endian), compiler, and standard library.

## Support Levels

Abseil has two basic levels of support:

<ul>
  <li><b>Supported</b> means that the indicated platform is officially
  supported. We pledge to test our code on that platform, have automated
  continuous integration (CI) tests for that platform, and bugs within that
  platform will be treated with high priority.</li>
  <li><b>Best Effort</b> means that we may or may not run continuous integration
  tests on the platform, but we are fairly confident that Abseil should work on
  the platform. Although we may not prioritize bugs on the associated platforms,
  we will make our best effort to support it, and we will welcome patches based
  on this platform. We may at some point officially support such a
  platform.</li>
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

macOS:

* gcc, clang: `-std=c++11`
* gcc, clang: `-std=c++14`
* clang < 5.0: `-std=c++1z`
* gcc, clang 5.0+: `-std=c++17`

Windows:

* msvc: `/std:c++14`
* msvc: `/std:c++latest`

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
      <td>gcc 5.1+<br/>clang 3.7+</td>
      <td>libstdc++<br/>libc++</td>
    </tr>
  </tbody>
</table>

<p style="background-color: #89CFF0; padding: 5px; width: 80%;" id="id09012020">
<br/>
Abseil now requires gcc 5.1 or above. Usage of gcc 4.9 is now unsupported.
</p>

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
      <td>ChromeOS, armv7a, little-endian, 32-bit</td>
      <td>clang 5.0+</td>
      <td>libstdc++</td>
    </tr>
  </tbody>
</table>

### macOS / Darwin Family

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
      <td>macOS 10.7+, endian-neutral, 64-bit</td>
      <td>Xcode 7.3.1+</td>
      <td>libc++</td>
    </tr>
    <tr>
      <td>iOS 7+, endian-neutral, 64-bit</td>
      <td>Xcode 7.3.1+</td>
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
      <td>Xcode 7.3.1+</td>
      <td>libc++</td>
    </tr>
  </tbody>
</table>

### Windows

<p style="background-color: #89CFF0; padding: 5px; width: 80%;" id="id06272019">
<br/>
On Windows platforms, Abseil does not include <code>winsock2.h</code>, as it
also pulls in <code>windows.h</code> (and defines a set of macros that may
conflict with Abseil users). Instead, we forward declare <code>timeval</code>
and require Windows users to explicitly include <code>winsock2.h</code>
themselves.
</p>

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
      <td>MVC 2015 Update 3, MSVC 2017</td>
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
      <td>Clang/LLVM 3.7+</td>
      <td>msvc</td>
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
      <td>Android NDK r11c+</td>
      <td>gcc 5.1+</td>
      <td>libc++, libstdc++</td>
    </tr>
  </tbody>
</table>

<p style="background-color: #89CFF0; padding: 5px; width: 80%;" id="id08192019">
<br/>
Abseil now requires gcc 5.1 or above. Usage of gcc 4.9 is now unsupported.
</p>

<!-- Styles for dated updates/changes to platform support -->
<style>#id06272019:before { content: "06/27/2019";font-weight:bold; color:black}</style>
<style>#id09012020:before { content: "09/01/2020";font-weight:bold; color:black}</style>
