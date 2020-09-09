---
title: "Status User Guide"
layout: docs
sidenav: side-nav-cpp.html
type: markdown
---

# Status User Guide

Abseil contains two Status libraries within the `absl/status` directory:

* A `status` library containing an `absl::Status` class for holding error
  handling information, a set of canonical `absl::StatusCode` error codes, and
  associated utilities for generating and propogating status codes.
* A `statusor` library containing the `absl::StatusOr<T>` class template for use
  in returning either an `absl::Status` error or an object of type `T`. (This
  `StatusOr<T>` abstraction is similar to the C++ proposal for `std::expected`.)

## Overview of `absl::Status`

Within Google, `absl::Status` is the primary mechanism to gracefully handle
errors across API boundaries (and in particular across RPC boundaries). Some of
these errors may be recoverable, but others may not. Most functions which can
produce a recoverable error should be designed to return either an
`absl::Status` (or the similar `absl::StatusOr<T>`, which holds either an object
of type `T` or an error).

Example:

```c++
absl::Status myFunction(absl::string_view fname, ...) {
  ...
  // encounter error
  if (error condition) {
    return absl::InvalidArgumentError("bad mode");
  }
  // else, return OK
  return absl::OkStatus();
}
```

Most operations in Abseil (or Google) code return an
[`absl::Status`](http://google3/third_party/absl/status/status.h) (abbreviated
`Status` in the text below). A `Status` is designed to either return "OK" or one
of a number of different error codes, corresponding to typical error conditions.
In almost all cases, when using `absl::Status` you should use the canonical
error codes (of type `absl::StatusCode`). These canonical codes are understood
across the codebase and will be accepted across all API and RPC boundaries. A
function which has a return value of `Status` *must be handled* (and is marked
`ABSL_MUST_USE_RESULT`).

## Using `Status` for Returning Errors

Success of any particular operation is indicated by a `Status` error code of
"OK" (technically a status error code of `absl::StatusCode::kOk`). API
developers should construct their operations to return `absl::OkStatus()` upon
success, or an `absl::StatusCode` upon another type of error (e.g. an
`absl::StatusCode::kInvalidArgument` error). The API provides convenience
functions to constuct each particular status code. (See
[Canonical Errors](#canonical_errors) below.)

For example, the following piece of code shows how to return an error
encountered while implementing a file operation:

```
absl::Status Open(absl::string_view fname, absl::string_view mode, ...) {
  if (...) return absl::OkStatus();  // Signal success
  if (...) return absl::InvalidArgumentError("bad mode");

  absl::Status result;  // Default constructor creates an OK value as well.
  if (...) {
    // Short-hand for result = absl::Status(absl::StatusCode::kNotFound, ...)
    result = absl::NotFoundError(absl::StrCat(fname, " is missing"));
  } else {
    ...
  }
  return result;  // could be "OK" or "NOT_FOUND"
}
```

A non-OK Status typically includes both an error code
(`absl::StatusCode::kNotFound`, which maps to "NOT_FOUND") and a message ("The
file.txt filename is missing"). The API provides `code()` and `message()` member
functions to retrieve these values. The error code is intended for programs to
examine (e.g., the caller might react differently based on the error code it
sees). The message is not intended for end users; it may get logged somewhere
for a developer or SRE to examine and find out what went wrong.

Note that low-level routines such as a file `Open()` should typically not log
status values themselves, but should pass them up to the caller who will have
better context on how to handle any error.

## Canonical Errors :{canonical_errors}

`Status` returns errors using an `absl::StatusCode`, which is an enumerated type
indicating either no error ("OK") or an error condition. These error codes map
to the `google.rpc.Code` RPC error codes indicated in
https://github.com/googleapis/googleapis/blob/master/google/rpc/code.proto.
E.g. an `absl::StatusCode::kInvalidArgument` value corresponds to an RPC error
code of "INVALID_ARGUMENT".

These canonical errors associated with `absl::Status` are used throughout the
codebase. As a result, these error codes are somewhat generic. When constructing
an `absl::Status` using one of these codes, you may want to provide more context
within the `Status` object's message.

For a full list of canonical error codes and advice on how to select the
appropriate one for your use case, see the
[Choosing Canonical Error Codes](status-codes) guide.

## Checking Errors

Just as an API provider must properly construct and return `absl::Status`, a
caller must properly handle receipt of that `Status`. This involves checking
whether the operation completed successfully (checking for "OK") and
determining the exact error and how to handle it, if the operation did not
succeed.

Instead of checking for a specific "OK" status code (e.g.
`absl::StatusCode::kOk`), the Abseil Status library provides a `Status::ok()`
member function. Users handling status error codes should prefer checking for an
OK status using this `Status::ok()` member function.

`absl::Status` values can be logged directly without requiring any conversion to
a string value.

```c++
absl::Status my_status = DoSomething();
// Don't do this:
//
//   if (my_status.code() == absl::StatusCode::kOk) { ... }
//
// Use the Status.ok() helper function:
if (!my_status.ok()) {
  LOG(WARNING) << "Unexpected error " << s;
}
```

Similarly, instead of checking for specific `absl::StatusCode` error codes such
as `absl::StatusCode::kInvalidArgument` may use helper functions such as
`absl::IsInvalidArgument(status)`.

Handling multiple error codes may justify use of a switch statement, but only
check for error codes you know how to handle; do not try to exhaustively match
against all canonical error codes. Errors that cannot be handled should be
logged and/or propagated for higher levels to deal with.

If you do use a switch statement to discriminate status codes, make sure that
you also provide a `default:` switch case, so that code does not break as other
canonical codes are added to the API.)

```c++
absl::Status s = Open(filename, "r");
if (absl::IsNotFound(s)) {
  s = Create(...);
}
if (!s.ok()) {  // Either Open or Create failed
  LOG(WARNING) << "Unexpected error " << s;
}
```

### Returning a Status or a Value

Suppose a function needs to return a value on success or, alternatively, a
`Status` on error. The Abseil Status library provides an `absl::StatusOr<T>`
class template for this purpose. An `absl::StatusOr<T>` represents a union of an
`absl::Status` object and an object of type `T`. The `absl::StatusOr<T>` will
either contain an object of type `T` (indicating a successful operation), or an
error (of type `absl::Status`) explaining why such a value is not present. Note
that `StatusOr<T>` cannot hold an OK status as that would imply a value should
be present.

In general, check the success of an operation returning an
`absl::StatusOr<T>` like you would an `absl::Status` by using the `ok()`
member function.

```c++
StatusOr<Foo> result = Calculation();
if (result.ok()) {
  result->DoSomethingCool();
} else {
  LOG(ERROR) << result.status();
}
```

Upon success, accessing the object held by an `absl::StatusOr<T>` should be
performed via `operator*` or `operator->`, after a call to `ok()` confirms that
the `absl::StatusOr<T>` holds an object of type `T`:

```c++
absl::StatusOr<int> i = GetCount();
if (foo.ok()) {
  updated_total += *i
}
```

An `absl::StatusOr<T*>` can be constructed from a null pointer like any other
pointer value, and the result will be that `ok()` returns `true` and `value()`
returns `nullptr`. Checking the value of pointer in an `absl::StatusOr<T>`
generally requires a bit more care, to ensure both that a value is present and
that value is not null:

```c++
StatusOr<std::unique_ptr<Foo>> result = FooFactory::MakeNewFoo(arg);
if (!result.ok()) {
  LOG(ERROR) << result.status();
} else if (*result == nullptr) {
  LOG(ERROR) << "Unexpected null pointer";
} else {
  (*result)->DoSomethingCool();
}
```

### Ignoring Status Results

Our compilers produce errors if a `Status` value returned by a function is
ignored. In some cases, ignoring the result is the correct thing to do, which
you can achieve by using `IgnoreError`:

```c++
// Don't let caching errors fail the response.
StoreInCache(request, response).IgnoreError();
```

Think carefully before using `IgnoreError()`. Unless you have a good reason,
prefer to actually handle the return value: perhaps you can verify that the
result matches the error you are expecting, or perhaps you can export it for
monitoring.

### Keeping Track of the First Error Encountered

Use `Status::Update()` to keep track of the first non-ok status encountered in a
sequence. `Update()` will overwrite an existing "OK" status, but will not
overwrite an existing error code of another value.

For example, suppose you want to execute two operations (regardless of whether
or not the first operation failed), but want to return an error if either of the
operations failed. Instead of:

```c++ {.bad}
absl::Status s = Operation1();
absl::Status s2 = Operation2();
if (s.ok()) s = s2;
```

use

```c++ {.good}
absl::Status s = Operation1();
s.Update(Operation2());
```

`Update()` will preserve the information of the first encountered error, such as
its error code, message, and any payloads.
