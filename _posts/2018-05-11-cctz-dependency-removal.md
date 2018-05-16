---
title: "Abseil No Longer Depends on CCTZ"
layout: blog
sidenav: side-nav-blog.html
published: true
permalink: blog/20180511-cctz-removal
type: markdown
category: blog
excerpt_separator: <!--break-->
---

### An Update On Our Dependencies

By [Shaindel Schwartz](mailto:shaindel@google.com), Abseil Engineer

As of the April 23 update, 
[af78826](https://github.com/abseil/abseil-cpp/commit/af7882601aad93ada881486eeaabc562f1733961)
, Abseil no longer requires an external dependency on CCTZ. If you have
included the CCTZ project solely to satisfy the Abseil dependency, you can now
safely remove it from your project’s setup.

<!--break-->

We are in the process of adding some updates to our Time library. As a
transitional step in this set of planned updates, we have added an internal
fork of the CCTZ types and dropped the dependency on the external CCTZ project.
To avoid potential name conflicts with a project’s independent use of the CCTZ
library, our internal copy lives in a unique, internal absl namespace. The
internal copy is intended solely as an implementation detail underpinning our
provided Time APIs. As with all internal types, users should not depend on or
use them directly. 

Note that if your project has its Abseil dependency pinned at a specific
commit, you may still need the dependency on CCTZ. (For a commit earlier than
[af78826](https://github.com/abseil/abseil-cpp/commit/af7882601aad93ada881486eeaabc562f1733961)
, the dependency on CCTZ is still required.) We encourage you to live at head.
