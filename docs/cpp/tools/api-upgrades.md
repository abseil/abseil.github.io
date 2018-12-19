---
title: "C++ Automated Upgrade Guide"
layout: docs
sidenav: side-nav-cpp.html
type: markdown
---

# C++ Automated Upgrade Guide

Abseil notes in its
[Compatibility Guidelines][compatibility] that we
will strive not to break API compatibility. In particular, we noted that we
would “never break an API in a single change ... We will introduce a new API and
a tool, wait some time, and then remove the old.” Until now, that tool has been
unspecified (as we haven’t yet had any true breaking changes), but we are now
ready to outline the process and tooling we will use to effect such API-breaking
changes, when necessary.

The process will consist of two steps, a deprecation followed by an API removal.

The deprecation process consists of the following:

* A change to the API itself. In most cases, we will aim to have both the
  deprecated API and the replacement API available concurrently (for example,
  via a separate overload).
* An associated LLVM [clang-tidy][clang-tidy] check (or checks) living upstream
  in LLVM’s repository to warn or change usages of the deprecated API to the
  replacement.
* Documentation on our [C++ Upgrade Tools][upgrade-tools] page denoting the
  availability of the tool, and, if necessary, any notes for effecting the
  change without clang-tidy if such a change cannot be sufficiently automated.
* An announcement blog post noting the change and containing links to the
  associated clang-tidy checks and documentation.

At a later time, based on the LLVM release cycle, we will remove the deprecated
API, which will consist of the following:

* Removal of the deprecated API from Abseil itself.
* Additional communication via a blog post announcing this formal removal of the
  deprecated API.

The deprecation and removal process is outlined in more detail below.

## Adding LLVM Clang Tidy Checks

When we determine that an API-breaking change is either necessary or
sufficiently beneficial, we will first introduce a suitable replacement and
release that code to Abseil (if possible).  We will always strive to make
refactoring of existing code non-atomic. Such refactoring should therefore not
require upgrading your version of Abseil.

Once a replacement is available, we will create a new clang-tidy check (or
checks) that will automate as much of the upgrade process for our users as
possible.  All Abseil API-breaking Clang Tidy checks will be prefixed by
“abseil-upgrade-” and listed on the
[Clang Tidy Checks documentation page][clang-tidy-checks].

Wherever it is deemed safe to do so, the check will provide fixes that
clang-tidy can apply automatically.  As this is C++, edge cases such as macro
bodies and complicated template logic may require manual changes. In such
situations, the clang-tidy check will still provide warning diagnostics to flag
deprecated uses, just without an automated fix. In those cases, we will provide
documentation for effecting the needed change.

It’s important to note that code will continue to compile after fixes without
updating any project dependencies.  As a result, upgrade checks can be used as
part of pre-submit testing and / or be included in the usual clang-tidy workflow
to prevent backsliding.

## Communicating API-Breaking Changes

After a new check undergoes review and lands upstream on the LLVM site, we will
announce the details with an [Abseil blog post][abseil-blog] of the
upcoming change as well as instructions for upgrading. Any associated
documentation regarding the change will be noted within the
[C++ Upgrade Tools][upgrade-tools] page. That guide will contain a list of all
changes.

Once posted on both LLVM and the Abseil blog, we will wait an appropriate amount
of time for the check to become available through the regular LLVM release
cycle. Once available, users can obtain (e.g. [download from llvm][llvm]) and
run a sufficiently fresh version of clang-tidy to generate the needed changes to
their code.

Prior to releasing any API breaking changes, we will attempt to ensure that the
upgrade check, the old API, and its replacement coexist for at least one LTS
branch cut.  Then, when the time comes to actually remove the deprecated API,
we will add a release notes blog post as a helpful reminder.  Similar notes will
be repeated as part of any LTS branch cut announcements that include API
breaking changes.

[compatibility]: /about/compatibility
[clang-tidy]: http://clang.llvm.org/extra/clang-tidy/
[upgrade-tools]: upgrades/
[clang-tidy-checks]: https://clang.llvm.org/extra/clang-tidy/checks/list.html
[abseil-blog]: https://abseil.io/blog/
[llvm]: http://releases.llvm.org/

