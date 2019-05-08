---
title: "Abseil Flags"
layout: blog
sidenav: side-nav-blog.html
published: true
permalink: blog/20190509-flags
type: markdown
category: blog
excerpt_separator: <!--break-->
---
By [Gennadiy Rozenthal](mailto:rogeef@google.com), Abseil Engineer

Abseil is very happy to announce the release of the Abseil Flags
library. Abseil's flags library provides a standard, readable way
to pass command-line values to a program.

```cpp
#include <iostream>
#include <string>

#include "absl/flags/flag.h"
#include "absl/flags/parse.h"

ABSL_FLAG(std::string, name, "you", "Name of the person to greet");

int main(int argc, char** argv) {
  absl::ParseCommandLine(argc, argv);
  std::cout << "Hello " << absl::GetFlag(FLAGS_name) << "!" << std::endl;
  return 0;
}
```

```sh
$ greet
Hello you!
$ greet --name=Alice
Hello Alice!
```

<!--break-->

Flag variables of the following types are supported out of the box:

* `bool`
* `int32_t`
* `int64_t`
* `uint64_t`
* `double`
* `std::string`
* `std::vector<std::string>`
* `absl::Duration`
* `absl::Time`

For more information, consult the
[Abseil Flags library documentation][abseil-flags].

[abseil-flags]: /docs/cpp/guides/flags
