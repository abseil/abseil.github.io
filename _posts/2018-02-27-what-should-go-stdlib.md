---
title: "What Should Go Into the C++ Standard Library"
layout: blog
sidenav: side-nav-blog.html
published: true
permalink: blog/20180227-what-should-go-stdlib
type: markdown
---

By Titus Winters (titus@google.com), @TitusWinters

<i><b>About the Author - </b> Titus holds a PhD in Computer Science Education
from UC Riverside. He created most of Google’s internal C++ coursework, and
plays an active role in the C++ mentoring program that serves several thousand
Google C++ engineers.  He has been deeply involved in C++ library infrastructure
since 2011, through the Google C++ Library Team and now Abseil.  He chairs the
Library Evolution Working Group (LEWG) - the sub-committee of the C++ Standard
that focuses on the design of the C++ standard library.</i>

A few interesting pieces on the direction and design for C++ have circulated
recently.  First off, I strongly recommend everyone read through 
[Direction for ISO C++](http://wg21.link/P0939r0) ; it provides a lot of 
excellent detail and suggestions, as well as some much-needed guidance on how
the language should evolve.  In particular, I think it's really important to
note "No language can be everything for everybody," the technical "pillars" upon
which C++ rests, and the call to remind everyone to go read "The Design and
Evolution of C++". The Direction Group is very rightly showing concern about the
breadth of things being proposed for the standard, as well as how to maintain
velocity and stability as we continue to move forward at an ever more rapid
pace.

### Batteries Included?

An [interesting piece](https://hatcat.com/?p=16) by Guy Davidson also
specifically focuses on what should be included in the C++ Standard Library,
with emphasis on a proposed 
[Graphics library.](http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2018/p0267r7.pdf)
Guy (again, rightly) is concerned with what can and cannot be done with C++
easily and out of the box.  Guy argues we should aim for "batteries included," a
much more all-inclusive approach than what is currently standardized. Especially
when you compare C++ to other languages, there's a pretty strong argument to be
made for a more inclusive and even all-encompassing standard library - look at
the richness of the standard libraries for Java or Python.

Interestingly, the Graphics library proposal is mentioned specifically in both
of these pieces. In the Direction Group's paper, Graphics is forwarded as a way
to make C++ more accessible for beginners. In Guy's piece, it's an exemplar of
the "batteries included" philosophy, drawing comparisons from other languages
and trying to make C++ feel more fully-featured out of the box.

I don't agree with either of those conclusions.  But the reasoning behind this
objection requires a little bit of a detour. Please bear with me.

### Literate and Algorithmic Thinking

I've done studies on what undergraduate CS1 students know and think about CS
when they show up, day 1.  If you ask such students what it means to program on
day 1, in a majority of cases they have basically no idea. The popular vision of
programmers and hackers comes from movies like The Matrix, Hackers, and
Swordfish, or the "It's a UNIX system" scene from Jurassic Park.  Programming is
like magic and the act of programming in popular culture has more to do with
portrayals of magic than opening up a text editor. A skilled programmer, like
Harry Potter as much as Neo, can do anything - and will probably be surrounded
by some impressive visual effects in the process.

Then, we introduce them to "Hello World".  Java gives me a great punching bag
here: "public static void main string bracket-bracket args, system dot out dot
println, quote Hello World".  Yes, you can draw comparison between the
boilerplate necessary there with the incantations within magic, but if we are
being honest we turn off CS1 students from that very first program if we aren't
careful.  "Don't worry about all of this stuff" is not a great way to inspire
curiosity and a desire to learn. Boilerplate is the enemy for intro
programmers. For a day 1 use-case, I love Python. You must explain "Print
doesn't mean to the printer, it just means to the screen. And quotes are just
like in prose - saying exactly this thing in quotes."  For kick-starting some
simple demonstrations without boilerplate, that's pretty hard to beat.  C++
falls somewhere between the two - if we stick to Hello World and iostreams, it's
not too bad.  The well-travelled path is pretty narrow (explaining strings
vs. char*s, namespaces, ADL, operators, etc), but it's certainly not as bad as
Java.

Once we get past the first day, we need to start thinking about what it means to
become a programmer. By "programmer", I don't mean an expert in any given
language - most anyone that can call themselves a programmer knows that the
syntax and details in a specific language is a largely separable thing from the
effort to learn to be an algorithmic / programmatic thinker. That transition
into algorithmic thinking transcends any particular language. It's a cognitive
shift, thinking in abstractions and control flow, more than learning the syntax
and edge cases for any particular language.

For comparison, there's a book called Orality and Literacy by Walter Ong that
goes into great detail on the differences between oral and literate people and
cultures, pointing out the significant cultural and cognitive shifts that happen
when you transition to a world that relies on the written word and the ability
to communicate ideas without being face to face.  I cannot prove it, but I
firmly and fundamentally believe that a shift of equal magnitude happens when
you transition from a literate mindset to an algorithmic one.

Assuming that the magnitude of the shift to an algorithmic mindset comparable to
becoming literate, consider how hard is it to become literate. How much effort
do we put into making that transition easy, with cardboard books and whole
genres devoted to helping learners make that transition?  Why would we think
that shifting from literate to algorithmic is any less difficult?  Bringing this
back to C++: why would we assume that the right tool for a high-performance
super-professional domain can also satisfy an "easy reader" in the process of
becoming an algorithmic thinker? To me, and certainly to most people I know, C++
isn't a kid-friendly Goodnight Moon - it's more of a Finnegan's Wake. Simply
put: developing an algorithmic mindset is hard on its own, even in a language
that is designed to hold your hand. C++ is not well-suited for being a starter
language - come to us when you've gotten over those first hurdles.

Approaching it from another angle: according to
[P0939](http://wg21.link/P0939r0), C++ cannot afford to be all things to all
people.  Hopefully nobody disagrees when I say that C++ is a language that
prioritizes efficiency and performance above pretty much everything else -
including user-friendliness, ease of use, etc.  Citing
[P0939](http://wg21.link/P0939r0) and [P0684](http://wg21.link/P0684r2) - one of
the few perspectives I expect everyone on the Committee to agree with is that
"C++ leaves no room for another language between itself and the hardware", and
that you don't pay for what you don't use.  Protections against programmer error
can be costly, and are thus not a priority for C++.  That's all perfectly fine,
so long as we keep that in mind and stay true to that philosophy. In many
respects this is what makes C++ the important language it is: when efficiency
counts, this is the language you go to. We will not make you pay for having your
hand held.

If we know that we cannot be the one language for all tasks, and we know that we
are focused on performance above all else - why are we thinking that a Graphics
library to make it easy to visualize things for novices is a good fit?

As an educator, I don't buy it.

### What Makes C++ Special?

There's a separate chain of reasoning that concerns me with Guy's "Batteries
Included" approach. Some of this was presented in 
[Corentin's reply](https://hackernoon.com/a-cake-for-your-cherry-what-should-go-in-the-c-standard-library-804fcecccef8)
to Guy's article, but I've got a bit of a different approach and experience with
it.

One of the other things that C++ has been good at, historically, is
stability. In many respects I think we take that too far - I regularly leave
standards meetings frustrated at our inability to fix mistakes, but I do also
see the value that stability provides the community.  At the committee level we
pay pretty close attention to what will break user code (well, at least
well-behaved user code, see [P0921](http://wg21.link/p0921r0)), up to and
including support for pre-compiled code depending on an ever-changing standard
library.  That is, we provide not just API (source level) compatibility over
time, we almost always provide ABI (binary level) compatibility. And that means
that a huge number of possible changes are infeasible: if it involves how a type
is represented in memory, it will not change for decades.

My friend Matt Kulukundis 
[spoke at CPPCon](https://www.youtube.com/watch?v=ncHmEUmJZf4) about work that
Google has been doing on hashing - a huge amount of performance and memory
savings is available beyond what is provided by `std::unordered_map.`  However,
the standard can never realize those savings: even a change to `std::hash` is
infeasible because we have to maintain binary compatibility with code compiled
years ago with a sub-par approach to hashing. The implementation for `std::hash`
as it stands leaves little room for important things like hash-flood mitigation.
As a community, we're paying in both resources and safety because of our
addiction to binary compatibility.

Even ignoring binary compatibility, the standard is very reticent to make
changes that might break existing code.  As an example (one of many, I assure
you), numerous proposals to resolve issues with `std::function `have circulated
in the past few years. One of my favorite gripes is that it is the only type
(AFAIK) in the standard library that is not thread-compatible: calls to const
methods from multiple threads can still cause race conditions. This
inconsistency is because the specification of the call operator is slightly
bogus: even when called in a const context, `std::function` is perfectly willing
to call non-const call operators, potentially mutating the contained
callable. This defect was pointed out years ago, and it was pointed out that the
only code that would be broken by fixing this would be code that is not thread
safe and likely buggy. The committee was unwilling to break existing code - even
at that early date.

Given this demonstration of prioritizing efficiency and stability, why would
something as high-level and changeable as Graphics be a good fit for the
standard?  I often legitimately question whether hashed associative containers
are a good fit for C++, given the potential for advancement that we've seen in
the last few years.  Anything complex enough that research tasks on how to
optimize it are still ongoing should probably not be in the C++ standard. At
least, not until we figure out how to deal with change a little more
aggressively.

### Dependency Management, not Standardization

The section of Guy's "Batteries Included" piece that resonates with me is this:
it isn't that the **standard** has to provide these things, but that there needs
to be **some** mechanism to readily distribute libraries and dependencies in the
C++ community.  It is far past time that we as a community find an answer that
is somewhere between "this is chaos" and "this is in the standard".  This is
particularly hard in C++, where the preponderance of build flags, preprocessor
directives, build systems, compilers, standard library variants makes true
portability challenging (to say the least).  But I know it can be done.  It will
require library providers to be more clear about what compatibility they
promise, and library consumers to understand what they are asking, but it can be
done.

So, what should go in the standard library?  Fundamentals. Things that can only
be done with compiler support, or compile-time things that are so subtle that
only the standard should be trusted to get it right. Vocabulary.  Time, vector,
string. Concurrency.  Mutex, future, executors.  The wide array of "sometimes
useful data structure" and "random metaprogramming" could and should be shuffled
off into a semi-standard repository of available but distinct utility libraries.
Those may themselves have different design and stability philosophies, like
Boost or Abseil - the principles that make the standard what it is are not
necessarily universal even if they are good for the standard.  Graphics is too
much - many won't want it, and those that think they do may not understand what
they are asking for.

Graphics won't make C++ a teaching language - learning to be an algorithmic
thinker should be done in a language that has fewer sharp edges.  C++ won't make
Graphics easy, and tying any sort of Graphics API to the legacy constraints of
C++ won't make for a great API in that space. But using the Graphics API as a
high-value seed for a centralized repository of C++ dependencies … that would go
a long way toward solving some very real problems.
