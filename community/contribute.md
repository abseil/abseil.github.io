---
layout: community
title: Contribution Guidelines
sidenav: side-nav-community.html
type: markdown
---

We definitely welcome your patches and contributions to Abseil!

If you are new to github, please start by reading [Pull Request howto](https://help.github.com/articles/about-pull-requests/)

## Legal Requirements

In order to protect both you and ourselves, you will need to sign the
[Contributor License Agreement](https://cla.developers.google.com/clas).

## Running Tests

Use `tools/run_tests/run_tests.py` script to run the unit tests.
See [tools/run_tests](tools/run_tests) for how to run tests for a given language.

Prerequisites for building and running tests are listed in [INSTALL.md](INSTALL.md)
and in `src/YOUR-LANGUAGE` (e.g. `src/csharp`)

## Guidelines for Pull Requests

* Create **small PRs** that are narrowly focused on **addressing a single concern**. 
  We often time receive PRs that are trying to fix several things at a time, but only
  one fix is considered acceptable, nothing gets merged and both author's & review's
  time is wasted. Create more PRs to address different concerns and everyone will be happy.
 
* For speculative changes, consider opening an issue and discussing it first. If you
  are suggesting a behavioral or API change, consider starting with an [Abseil 
  proposal](https://github.com/abseil/proposal). 
 
* Provide a good **PR description** as a record of **what** change is being made and **why** it was made. Link to a github issue if it exists.
 
* Don't fix code style and formatting unless you are already changing that line to address an issue. PRs with irrelevant changes won't be merged. If you do want to fix formatting or style, do that in a separate PR.
 
* Unless your PR is trivial, you should expect there will be reviewer comments that you'll need to address before merging. We expect you to be reasonably responsive to those comments, otherwise the PR will be closed after 2-3 weeks of inactivity.
 
* Maintain **clean commit history** and use **meaningful commit messages**. PRs with messy commit history are difficult to review and won't be merged. Use `rebase -i upstream/master` to curate your commit history and/or to bring in latest changes from master (but avoid rebasing in the middle of a code review).
 
* Keep your PR up to date with upstream/master (if there are merge conflicts, we can't really merge your change).
 
* If you are regenerating the projects using `tools/buildgen/generate_projects.sh`, make changes to generated files a separate commit with commit message `regenerate projects`. Mixing changes to generated and hand-written files make your PR difficult to review.
 
* **All tests need to be passing** before your change can be merged. We recommend you **run tests locally** before creating your PR to catch breakages early on (see [tools/run_tests](tools/run_tests). Ultimately, the green signal will be provided by our testing infrastructure. The reviewer will help you if there are test failures that seem not related to the change you are making.
 
* Exceptions to the rules can be made if there's a compelling reason for doing so.