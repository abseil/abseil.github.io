---
title: app.py
layout: docs
sidenav: side-nav-python.html
type: markdown
---

# `app.py`

`app.py` is the generic entry point for Abseil Python applications.

When the program starts, `app.run()` parses the flags, printing a usage message
and failing if illegal flags or flag values are specified.

When using `app.py`'s `run()` to start your program, C++ flags will
automatically be available if your application links against wrapped C++
libraries. So be sure to use `app.run()`, as it will do its best to *Do The
Right Thing* in as many cases as possible.
