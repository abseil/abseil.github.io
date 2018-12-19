---
title: "Automated Upgrade Tooling for Abseil"
layout: blog
sidenav: side-nav-blog.html
published: true
permalink: blog/20181221-upgrade-tooling
type: markdown
category: blog
excerpt_separator: <!--break-->
---

By [Alex Strelnikov](mailto:strel@google.com), Abseil Engineer

As we promised when we released our [Compatibility Guidelines][compatibility],
we have developed a process for announcing and handling any API-breaking
changes we may need to make within the Abseil code base. Our
[C++ Automated Upgrade][api-upgrades] guide outlines this process,
which consists of [clang-tidy][clang-tidy] tooling and associated
communication regarding the change. A list of all such tools will be
listed on our [Upgrade Tools][upgrade-tools] page.

At this time, we are also releasing our first such tool: a clang-tidy check
for
[removing bug-prone implicit conversions in calls to several
`absl::Duration` functions][duration-conversions].

<!--break-->

As outlined in our upgrade guide, we will always first serve notice of
such a tool via this blog, and will also blog once we've officially
removed, if necessary, the deprecated API.

[compatibility]: /about/compatibility
[api-upgrades]: /docs/cpp/tools/api-upgrades
[clang-tidy]: http://clang.llvm.org/extra/clang-tidy/
[upgrade-tools]: /docs/cpp/tools/upgrades/
[duration-conversions]: https://clang.llvm.org/extra/clang-tidy/checks/abseil-upgrade-duration-conversions.html
