---
title: Testing
layout: docs
sidenav: side-nav-python.html
type: markdown
---

# Testing

## Introduction

Abseil Python's testing library is similar to Python's standard `unittest`
module (sometimes referred to as PyUnit) but offers some additional useful
features on top of the standard library, such as interfacing with Abseil Flags.

To use the Abseil testing library, do the following in your unit tests:

* import the `absltest` module
* import the `flags` module, which gives you access to the variables
`FLAGS.test_srcdir` and `FLAGS.test_tmpdir`.
* call `absltest.main()` instead of `unittest.main()`

## Unit Tests Basics

Within a unit test class, any method name starting with 'test' will be run
automatically as part of the unit test. Test names should describe the
particular case being tested.

### What is Unittest/Absltest Doing?

The pattern is simple and common to most xUnit frameworks. Basically:

*   `main()` scans the current file for classes derived from `TestCase`
*   `main()` then scans each class for methods prefixed by `"test"` (e.g.
    `testInitialize(self):`)
*   For each class and each test method, the framework:
    *   instantiates the class
    *   calls the `setUp()` method, if one exists
    *   try:
        *   call the test method
        *   if any assertions fail, or the test method terminates with an
            exception, mark this test as a failure
        *   otherwise, mark this test as a success
    *   finally:
        *   calls the `tearDown()` method, if one exists
    *   stores any tracebacks for reporting after all tests have run

Note that `setUp()` and `tearDown()` are run once for each test method, so they
are a great place to put data initialization and resource cleanup.

### Using Validation Methods

Validation methods such as `assertEqual()` raise an exception on failure,
which terminates the current test method. Unit test execution will continue with
the remaining test methods.

Additional methods, inherited from `absltest`, are available to validate
results:

*   `self.assertTrue`
*   `self.assertFalse`
*   `self.assertEqual`
*   `self.assertNotEqual`
*   `self.fail`

The Abseil testing library contains many more methods than the five above; some
are in Python's built-in [unittest.TestCase](https://docs.python.org/2/library/unittest.html#unittest.TestCase) while others
are in Abseil Python's subclass [absl.testing.absltest](https://github.com/abseil/abseil-py/blob/master/absl/testing/absltest.py).

### Example Code

More examples are forthcoming, but for now please see [absl-py's own tests](https://github.com/abseil/abseil-py/blob/master/absl/tests/app_test.py) for
examples of how to use `absltest`.
