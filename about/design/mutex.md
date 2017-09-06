---
title: Mutex Design Notes
layout: about
sidenav: side-nav-about.html
type: markdown
---

## `Mutex` Design Notes

The C++ library standard includes its own `std::mutex`. Why does Google
use its own `Mutex` class, and why is Abseil releasing it?

### API Issues

`Mutex` and `std::mutex` both provide capabilities to perform locks under
certain conditions. condition variables, allows 


|`Mutex` behavior|`std::mutex`|
|----------------|------------|
|worker.cc
|void Finish() {
  shared_lock_->Lock();
  shared_state_ += 1;
  shared_lock_->Unlock();
}

waiter.cc
void Wait() {
  shared_lock_>Lock();
  shared_lock_->Await(Condition([this]() { 
      return shared_state_ == 1; 
  }));
  shared_lock_->Unlock();
}
