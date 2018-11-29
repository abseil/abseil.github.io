---
title: "CppCon 2018: Modern C++ Design"
layout: blog
sidenav: side-nav-blog.html
published: true
permalink: blog/20181129-moderncpp
type: markdown
category: blog
excerpt_separator: <!--break-->
---

### Titus Winters and Modern C++

By [Tom Manshreck](mailto:shreck@google.com), Abseil Tech Writer

[CppCon 2018](https://cppcon.org/cppcon-2018-program/) was held in
Bellevue, WA at the end of September.

C++ has changed a lot since the transformative introduction of C++11.
It is now all too apparent that C++ API Design itself also needs to
change as the lessons learned about, for example, type design
become more understood.

Titus Winters reflects on the changes to C++ and how the introduction
of new principles such as move-only types have affected API design
in this two-part talk.

In the first part, Titus focuses on parameter passing and an API's
overload set in providing a powerful conceptual framework for API
design. In the second part, we focus on the properties of well-designed
types, and how to think about things like Regularity. We discuss how
Regularity affects the design of non-owning reference types
like string_view or span.

If you haven't already, check out Titus' original blog post on
["Revisiting Regular Types"][regular-types] for more background
information.)

<!--break--> 

<a href="https://www.youtube.com/watch?v=xTdeZ4MxbKo" target="_blank">
<img src="/img/cppcon-modern-cpp-1.png" />
</a>

<a href="https://www.youtube.com/watch?v=tn7oVNrPM8I" target="_blank">
<img src="/img/cppcon-modern-cpp-2.png" />
</a>

[cppcon]: https://www.youtube.com/user/CppCon
[regular-types]: /blog/20180531-regular-types

