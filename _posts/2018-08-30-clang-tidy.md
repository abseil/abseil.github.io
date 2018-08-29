---
title: "Clang-Tidy Checks for Abseil"
layout: blog
sidenav: side-nav-blog.html
published: true
permalink: blog/20180830-clang-tidy
type: markdown
category: blog
excerpt_separator: <!--break-->
---

By [Deanna Garcia]() and [Hugo Gonzalez]()

Abseil wants to help developers avoid common mistakes unique to our collection
of libraries. Therefore, we have developed a set of clang-tidy checks for
Abseil, allowing you to catch these errors early on before they become
bigger problems.

<!--break-->

[Clang-Tidy](http://clang.llvm.org/extra/clang-tidy/)) is a useful tool to help
developers write C++ code in a correct and efficient manner. Clang-Tidy now
supports a set of Abseil checks designed to diagnose and fix typical programming
errors specific to Abseil including:

* Compatibility guideline violations
* Style violations
* Interface misuse
* Bugs that can be deduced via static analysis 

We hope that these checks will help projects that depend on Abseil have high
standards of code quality. 

Our checks can be found on llvm’s **clang-tools-extra** repository, in the
[**clang-tidy/abseil** directory](https://github.com/llvm-mirror/clang-tools-extra/tree/master/clang-tidy/abseil).
The following checks have been released:

* Duration Division Check
* Faster StrSplit Delimiter Check 
* No Internal Dependencies Check 
* No Namespace Check 
* Redundant StrCat Calls Check
* StrCat-Append Check 
* String Find Starts with Check

For more information, consult Abseil’s [Clang-Tidy Check Guide](/docs/cpp/tools/clang-tidy).

You can also write your own checks and share them with the Abseil community. For more
information on clang-tidy, and if you are interested in learning more to get involved
in writing your own Abseil clang-tidy checks, consult the
[Clang-Tidy documentation](http://clang.llvm.org/extra/clang-tidy/).
