---
title: "Choosing Canonical Error Codes"
layout: docs
sidenav: side-nav-cpp.html
type: markdown
---

# Choosing Canonical Error Codes

`Status` returns errors using an `absl::StatusCode`, which is an enumerated type
indicating either no error ("OK") or an error condition. These error codes map
to the `google.rpc.Code` RPC error codes indicated in
https://github.com/googleapis/googleapis/blob/master/google/rpc/code.proto.

This is a cheat sheet you can use to pick an appropriate error. Pick the most
specific error code that applies.

Condition                                                                                                               | Code
----------------------------------------------------------------------------------------------------------------------- | ----
The request succeeded                                                                                                   | `OK`
The request was cancelled, typically by the caller                                                                      | `CANCELLED`
The request parameters would never work                                                                                 | `INVALID_ARGUMENT`
The operation did not complete within the specified deadline                                                            | `DEADLINE_EXCEEDED`
The requested entity does not exist                                                                                      | `NOT_FOUND`
The entity being created already exists                                                                                 | `ALREADY_EXISTS`
The caller does not have permission to execute the operation                                                            | `PERMISSION_DENIED`
The caller's identity cannot be verified                                                                                | `UNAUTHENTICATED`
Some resource is exhausted (quota, server capacity, etc)                                                                | `RESOURCE_EXHAUSTED`
The system is not in the required state for the operation                                                               | `FAILED_PRECONDITION`
The operation was aborted, typically due to a concurrency issue like sequencer check failures, transaction aborts, etc. | `ABORTED`
There was a transient error                                                                                             | `UNAVAILABLE`
The client has iterated too far, and should stop                                                                        | `OUT_OF_RANGE`
There is no implementation for the requested operation                                                                  | `UNIMPLEMENTED`
A serious internal invariant is broken (i.e. worthy of a bug or outage report)                                          | `INTERNAL`
Unrecoverable data loss or corruption                                                                                   | `DATA_LOSS`
There is no way to determine a more specific error code                                                                 | `UNKNOWN`

*Note*: Choosing between `FAILED_PRECONDITION`, `ABORTED`, and `UNAVAILABLE` is
subtle, especially with respect to the retry strategy the caller should use.
Some guidelines that may help a service implementer:

* Use `UNAVAILABLE` if the client can retry just the failing call.
* Use `ABORTED` if the client should retry at a higher transaction level (such
  as when a client-specified test-and-set fails, indicating the client should
  restart a read-modify-write sequence).
* Use `FAILED_PRECONDITION` if the client should not retry until the system
  state has been explicitly fixed. For example, if an "rmdir" fails because the
  directory is non-empty, `FAILED_PRECONDITION` should be returned since the
  client should not retry unless the files are deleted from the directory.

