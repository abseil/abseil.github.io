---
title: Compiler Macros Guide
layout: docs
sidenav: side-nav-cpp.html
type: markdown
---

## Platform Check Macros

C and C++ compilers automatically define some macros that can be used to:

 * Identify platforms (architecture, endianness, OS, compiler,
   C++ standard, library)
 * Detect compiler configurations (debug mode, exception handling, etc.)

Collectively, these macros are known as *pre-defined compiler macros*,
and are used in Abseil to conditionally compile code for
various purposes like portability, performance, functionality, etc. This
document lists the compiler macros Abseil uses to write preprocessor
conditionals and build configuration macros.

This document is designed solely to document Abseil's usage of these
macros, and assist developers who need to add architecture-specific
code to Abseil.

Note: [Feature Check Macros](feature_checks), which developers can use to
check for the presence of certain language features, are documented within
their own, separate guide.

The macros that Abseil uses are listed below, in tables that list the
macro, what it identifies, and what standard defines the macro.

<p class="note">
If you wish to check what macros your compiler has defined, see
<a
href="http://nadeausoftware.com/articles/2011/12/c_c_tip_how_list_compiler_predefined_macros">
How to List Compiler Predefined Macros</a>.
</p>

## Architecture

|**Macro**|**Architecture**|**Compiler**|**Notes**|
|------------|----------|---------------|--------|
|`__x86_64__`|AMD64|GNU C, Clang/LLVM||
|`_M_X64`|AMD64|Visual Studio||
|`__arm__`|ARM||32-bit only|
|`_M_ARM`|ARM|Visual Studio||
|`__aarch64__`|ARM64|||
|`__i386__`|Intel x86|||
|`_M_IX86`|Intel x86|Visual Studio\*||
|`__ia64__`|Intel Itanum (IA-64)|||
|`_M_IA64`|Intel Itanum (IA-64)|Visual Studio||
|`__ppc__`<br/>`__PPC__`<br/>`__ppc64__`<br/>`__PPC64__`|PowerPC|||
|`_M_PPC`|PowerPC|Visual Studio||
|`__myriad2__`|Myriad2|Myriad Development Kit (Intel Movidius)||
|`__mips__`|MIPS|GNU C||

\* Only defined for 32-bits architectures.

References:

* [Architectures](https://sourceforge.net/p/predef/wiki/Architectures/)
  within the Sourceforge Pre-defined Compiler Macros guide.
* [How to detect the processor type using compiler predefined macros](http://nadeausoftware.com/articles/2012/02/c_c_tip_how_detect_processor_type_using_compiler_predefined_macros)

## Endianness

No standard portable pre-defined macro exists that can be used to
determine endianness. Instead, Abseil defines the following macros in
`absl/base/config/h`:

* `ABSL_IS_LITTLE_ENDIAN`
* `ABSL_IS_BIG_ENDIAN`

References:

* [Endian Neutral Code](https://sourceforge.net/p/predef/wiki/Endianness/)
  within the Sourceforge Pre-defined Compiler Macros guide.

## Operating Systems

|**Macro**|**Operating System**|**Compiler**|
|------------|----------|----------|
|`__ANDROID__`|Android|Android NDK|
|`__APPLE__`|MacOS, iOS|GNU C, Intel C++, and Apple LLVM|
|`_WIN32`|Windows|For both 32-bit and 64-bit environments|
|`__linux__`|Linux|Android NDK, GNU C, Clang/LLVM|
|`__ros__`|Akaros||
|`__Fushsia__`|Fuchsia||

References:

* [Operating Systems](https://sourceforge.net/p/predef/wiki/OperatingSystems/)
  within the Sourceforge Pre-defined Compiler Macros guide.

## Compilers

|**Macro**|**Compiler**|**Version Macro**|**Notes**|
|------------|----------|--------|---------|
|`__GNUC__`|GCC|`__GNUC__`<br/>`__GNUC_MINOR__`<br/>`__GNUC_PATCHLEVEL__`|Clang also defines `__GNUC__` for compatibility with GCC. If you want Clang-only, write `defined(__GNUC__) && !defined(__clang__)`|
|`__clang__`|Clang/LLVM|`__clang_major__`<br/>`__clang_minor__`<br/>`__clang_patchlevel__`||
|`_MSC_VER`|MSVC|`_MSC_VER`<br/>`_MSC_FULL_VER` ||
|`__EMSCRIPTEN__`|Emscripten|`__EMSCRIPTEN_major__`<br/>`__EMSCRIPTEN_minor__`<br/>`__EMSCRIPTEN_tiny__`||
|`__asmjs__`|asm.js|||
|`__NVCC__`|NVCC|||

References:

* [Compilers](https://sourceforge.net/p/predef/wiki/Compilers/)
  within the Sourceforge Pre-defined Compiler Macros guide.

## Libraries

Library headers need to be included before checking the macros. For example,
`base/config.h` includes `<cstddef>` for `__GLIBCXX__`, `_LIBCPP_VERSION`.

Note that these macros are not compiler-dependent as they are defined within
header files.

|**Macro**|**Library**|
|------------|----------|
|`__GLIBCXX__`|libstdc++|
|`_LIBCPP_VERSION`|libc++|
|`_MSC_VER`|MSVC|
|`__GLIBC__`|GNU glibc|
|`__BIONIC__`|Bionic libc|

References:

* [Libraries](https://sourceforge.net/p/predef/wiki/Libraries/)
  within the Sourceforge Pre-defined Compiler Macros guide.
