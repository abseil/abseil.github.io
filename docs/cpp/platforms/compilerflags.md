---
title: "Abseil Compiler Flags"
layout: docs
sidenav: side-nav-cpp.html
type: markdown
---

# Abseil Compiler Flags

The Abseil C++ code is compiled using flags indicated within this guide. Our
objective is to support as many warning flags as possible, to minimize the
chance that your code will be impacted by flags that you may need in your
development environment. However, given the plethora of possible compilation
configurations, that is not always possible, and we've found some flags to be
counter-productive.

This guide describes the warning flags we are using, per compiler. We do disable
some flags to keep our code as noise-free as possible. Notes on flags that we do
not support and have intentionally disabled are provided within this guide.
Separately, some flags are also disabled within existing tests. In both cases,
we will continue to work to reduce the number of flags we need to disable.

These flags (and flags sets) are defined in the Abseil code repository within
the
[copts.bzl](https://github.com/abseil/abseil-cpp/blob/master/absl/copts.bzl)
file.

<p class="note">
Note that, in general, Abseil treats all compiler <i>warnings</i> as
<b>errors</b> (<code>-Werror</code> in GCC/Clang, <code>/WX</code> in MSVC),
and our Kokoro continuous integration tests do likewise. However, we do not
enable "warnings as errors" within the GCC and Clang flag sets here; we can't
control what warnings future compilers may add to the existing flag sets. (We do
enable warnings as errors within the MSVC flag set.)
</p>

## Abseil Warning Flags

At a high level, Abseil defines two sets of flags:

* `ABSL_DEFAULT_COPTS`
* `ABSL_TEST_COPTS`

`ABSL_TEST_COPTS` includes all flags within `ABSL_DEFAULT_COPTS` but
disables a number of them to avoid problems with certain tests. In general, you
should treat `ABSL_DEFAULT_COPTS` as the canonical list of Abseil compiler
flags. We hope to harmonize these flag sets in the future.

In practice, `ABSL_DEFAULT_COPTS` contains one of the following flag sets,
depending on the compiler it is invoked under:

* `ABSL_GCC_FLAGS` for GNU gcc compilers
* `ABSL_LLVM_FLAGS` for Clang compilers
* `ABSL_MSVC_FLAGS` for Visual Studio/msvc compilers

These flag sets are documented below.

### GCC Flags

The `ABSL_GCC_FLAGS` set of compiler flags has the following characteristics:

* All "normal" flags are set via `-Wall` and `-Wextra`. (Note that not "all"
  flags are contained with the GCC `all` set.)
* Additionally, Abseil enables the following flags, which are generally
  recommended for all C++ code:
    * `-Wcast-qual`
    * `-Wconversion-null`
    * `-Wmissing-declarations`
    * `-Woverlength-strings`
    * `-Wpointer-arith`
    * `-Wunused-local-typedefs`
    * `-Wunused-result`
    * `-Wvarargs`
    * `-Wvla`
    * `-Wwrite-strings`
* Abseil disables `-Wsign-compare` because of the presence of signed and
  unsigned integer comparisons in our codebase (mostly between Abseil and the
  standard library).

References:

[Options to Request or Suppress Warnings](https://gcc.gnu.org/onlinedocs/gcc/Warning-Options.html#Warning-Options)

### Clang Flags

The `ABSL_LLVM_FLAGS` set of compiler flags is the most extensive set and
provides the most code analysis, which is why we recommend a Clang compiler.
The Clang compiler flag set has the following characteristics:

* All "normal" flags are set via `-Wall`, `-Wextra` and `-Weverything`. (Note
  that, like with GCC, not "all" flags are contained with the Clang `all`
  set.)
* `-Wconversion` is disabled to turn off the overly-broad set of implicit
  conversion warnings. Many (but not all) of these implicit conversion warnings
  are later turned on.
* Additionally, the following flags are disabled to prevent warnings based
  on implicit type casts:
    * `-Wno-double-promotion`
    * `-Wno-float-conversion`
    * `-Wno-old-style-cast`
    * `-Wno-shorten-64-to-32`
    * `-Wno-sign-conversion`
* `-Wrange-loop-analysis` is disabled because Clang's implementation only
  ignores actual POD types; turning this warning on would require even small
  value types such as `absl::string_view` to be defined as const references
  within a range loop.
* `-Wglobal-constructors` is disabled because some low-level initialization
  abstractions (mostly internal) require them. In general, however, you should
  avoid global constructors.
* `-Wpadded` and `-Wpacked` are disabled because these flags are typically
  used as advisory warnings, but we treat warnings as errors within Abseil code.
* `-Wundef` is disabled because some Abseil dependencies
  ([CCTZ](https://github.com/google/cctz) and
  [pcg_random](http://www.pcg-random.org/)) use `#undef`. (We only do so on
  macros we define ourselves for local use, to prevent the definition from
  leaking globally.)
* `-Wgcc-compat` is disabled because we want to use Clang-specific features in
  a Clang compilation branch and not get unnecessary warnings about GCC.
* `-Wcomma` and `-Wextra-semi` are disabled because they are still valid C++
  code (and occur in cases of macro expansion).
* `-Wformat-literal` is disabled because some of our logging code passes their
  literal arguments to helper functions as non-literal variables.
* `-Wswitch-enums` is disabled because it would break any users of existing
  enums, if additional enum entries were added.

References:

* [Clang Command Line Argument Reference](https://clang.llvm.org/docs/ClangCommandLineReference.html)
* [Diagnostic Flags in Clang](https://clang.llvm.org/docs/DiagnosticsReference.html)

### MSVC Flags

The `ABSL_MSVC_FLAGS` set of compiler flags is specific to MSVC/Visual Studio
and has the following characteristics:

* All "level 3" flags are set via the `\W3` flag. (See
  [Warning Levels](https://msdn.microsoft.com/en-us/library/thxezb7y.aspx)).
* All warnings are treated as errors (as is the case above for Clang and GCC)
  via the `\WX` flag.
* The following flags are disabled because they are advisory, and ignoring them
  is better than treating them as errors:
    * `/wd4005` prevents warnings about macro redefinitions.
    * `/wd4068` prevents warnings on unknown pragmas.
    * `/wd4244` prevents warnings on implicit conversions.
    * `/wd4267` prevents warnings on conversion from `size_t` to `int`.
    * `/wd4800` prevents warnings on implicit conversion to type
      `bool`.
* The following Windows macro definitions are also defined:
    * `/DNOMINMAX` to prevent Windows overrides of `std` min/max functions.
    * `/DWIN32_LEAN_AND_MEAN` to reduce the amount of Windows-specific header
      files.
    * `/D_CRT_SECURE_NO_WARNINGS` to prevent Windows from complaining about
      standard C++ functions.

References:

* [MSVC Compiler Options](https://msdn.microsoft.com/en-us/library/fwkeyyhe.aspx)

