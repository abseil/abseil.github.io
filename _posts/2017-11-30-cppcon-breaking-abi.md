---
title: "CppCon 2017: How to Break an ABI"
layout: blog
sidenav: side-nav-blog.html
published: true
permalink: blog/20171023-cppcon-breaking-abi
type: markdown
category: blog
excerpt_separator: <!--break-->
---

### Gennadiy Rozental's Lightning Talk

By [Tom Manshreck](mailto:shreck@google.com), Abseil Tech Writer

Breaking an
[ABI](https://en.wikipedia.org/wiki/Application_binary_interface){:target="_blank"}
is seldom your first choice, but what do you do if you simply must
break this contract with your developers?

Check out Gennadiy Rozental's talk on how we implemented our own `::string`
class in Google, decided we eventually should move back to a `std::string`,
and how we kept Google's engineers happy during the transition.

<a href="https://www.youtube.com/watch?v=NzaYUlAw93k" target="_blank">
<img src="/img/cppcon-breaking-abi.png" />
</a>