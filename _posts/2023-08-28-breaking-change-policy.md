---
title: Abseil Breaking Change Policy Update
layout: blog
sidenav: side-nav-blog.html
published: true
permalink: blog/20230828-breaking-change-policy
type: markdown
category: blog
excerpt_separator: <!--break-->
---

### Abseil Breaking Change Policy Update

By [Derek Mauro](mailto:dmauro@google.com)

Today we are announcing that Abseil is adopting the Google
[OSS Library Breaking Change Policy](https://opensource.google/documentation/policies/library-breaking-change).
What does this mean for Abseil users? Let's take a look.

Abseil's original compatibility policy made this statement:

<i>We will always strive to not break API compatibility. If we feel that we
must, we will provide a compiler-based refactoring tool to assist in the upgrade
… any time we are making a change publicly we’re also doing the work to update
the 250MLoC+ internal Google codebase — we very rarely do such refactoring that
cannot be automated.</i>

<!--break-->

In the 6 years since Abseil has been available to the open source community, we
have released only one tool, and we believe that there is a good chance that no
one ever needed to use that tool.

There are a few reasons why we never really needed to make use of our policy of
providing an automated update tool.

First, Abseil only ships production-ready APIs. While these APIs did evolve in
their early life, APIs must be considered stable and have thousands of usages in
Google's internal codebase before they are eligible for inclusion in Abseil.

Second, as stated in the original policy, when we do change an API, we also have
to update Google's internal code base. While we do use automated tooling to do
this, the fact that Google's internal code base is so large constrains the types
of changes that we can make.

The policy of releasing a tool for automated upgrades has not worked out in
practice. Not only have we not made changes that would have made upgrading
difficult without the use of a tool, but the policy of requiring releasing a
tool has also made it harder for us to release fixes that are technically API
breaks but that impact very few callsites.

Under the new policy, despite claiming the right to make breaking changes
without shipping an automated upgrade tool, we still commit to making upgrading
as easy as possible, and only making breaking changes when we believe they will
provide benefit to our users. We will announce these changes prominently in our
commit messages as well as in the release notes for
[LTS releases](https://github.com/abseil/abseil-cpp/releases), and will provide
guidance on how to resolve issues.

Please read our updated
[compatibility guidelines](https://abseil.io/about/compatibility) for more
information about what users must (and must not) do to successfully update to
newer versions of Abseil.
