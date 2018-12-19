---
title: "Duration Conversion Upgrade Tool"
layout: docs
sidenav: side-nav-cpp.html
type: markdown
---

# Duration Conversion Upgrade Tool

The Abseil Duration Conversion upgrade tool finds calls to `absl::Duration`
arithmetic operators and factories that rely on deprecated overloads. These
calls invoke implicit conversions that can lead to subtle bugs. After upcoming
API changes, an explicit cast will be required for affected call sites to
continue compiling.

The clang-tidy check to apply necessary changes is
[abseil-upgrade-duration-conversions][duration-conversions].

## Background

The arithmetic operators (`*=`, `/=`, `*`, and `/`) for `absl::Duration`
currently have templated overloads to accept an argument of class type that is
convertible to any arithmetic type. The implementation always converts such an
argument to an `int64_t`. This happens even in a case such as
`std::atomic<float>`, which leads to loss of precision:

```c++
absl::Duration d;
d *= std::atomic<float>(3.5f);  // actually multiplies by 3!
```

The following factory functions have a similar issue we are addressing:

*   `absl::Nanoseconds`
*   `absl::Microseconds`
*   `absl::Milliseconds`
*   `absl::Seconds`
*   `absl::Minutes`
*   `absl::Hours`

Currently, each of these factories has an overload that accepts an `int64_t`.
This overload ends up being chosen for calls with an argument of class type that
is convertible to any arithmetic type. As before, this can lead to unexpected
and unintended behavior that is difficult to spot at the call site.

In the case of both the operators and factories, current calls using floating
point types or integral types are unaffected by these issues.

## API Changes

These operators and factories will be changed to only accept arithmetic types in
order to prevent unintended behavior. The fix ahead of this change is to
explicitly cast arguments of class type that are currently getting passed to the
affected APIs.

You can use the released clang-tidy check to do this in an automated way.
However, if clang-tidy is not an option, here is an example of the manual fixes
required:

```c++
std::atomic<int> a;
absl::Duration d = absl::Milliseconds(a);
d *= a;
```

becomes

```c++
std::atomic<int> a;
absl::Duration d = absl::Milliseconds(static_cast<int>(a));
d *= static_cast<int>(a);
```

[duration-conversions]: https://clang.llvm.org/extra/clang-tidy/checks/abseil-upgrade-duration-conversions.html
