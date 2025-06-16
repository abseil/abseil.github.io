---
title: "C++ Tips of the Week"
layout: tips
sidenav: side-nav-tips.html
type: markdown
---

Background: About five years ago, within Google we started publishing a series 
of C++ tips, about once a week, that became known as the "C++ Tips of the Week"
(TotW). They became wildly successful, and we are still publishing them to
this day (indicating that a language as rich as C++ will not deplete us of
topics anytime soon).

Not only do we discuss the finer points of the language, but in true "tip"
fashion, offer our advice or design preferences. The collective set of C++
TotW has become a canon within Google itself, cited thousands of times per
week in code reviews and internal mailing list discussions. Often they are
cited by number, and some have become known simply as "totw/110" or "totw/77".

We've decided to expose most of these tips to the Abseil development community,
and the C++ community at large. Over the coming months, we'll be posting new
tips as we review and refine them for publication. Not all the entries we've
written are relevant to the outside world; some were
specific to our internal tools and abstractions, and some have become obsolete
as the language has changed. But we'll publish what we can and what we find
valuable (and write new tips!) on this page as they become available.

<p class="note">
Note: we will be keeping the original numbering scheme on these tips, and 
original publication date, so that the 12K or so people that have some exposure
to the original numbering don't have to learn new citations. As a result, some
tips may appear missing and/or  out of order to a casual reader. But rest
assured, we're giving you the good stuff.
<br/><br/>
Some tips may include historical information that, though accurate, may reflect
philosophy and/or usage at the time the tip was originally written. In most
cases, we have updated that information to reflect current practices, and note
exceptions that are historical, where applicable.
</p>

**Because these tips are being published out of original order, we've listed them
below in the order of re-publication.**

<ul>
  {% assign sorted_posts = site.posts | sort: 'date' | reverse %}
  {% assign datelist = '' %}
  {% assign new = true %}

  {% for post in sorted_posts %}
    {% if post.url contains "/tips/" %}
      {% assign cur_date = post.date | date_to_string %}
      {% unless datelist contains cur_date %}
        <li><b>{{post.date | date: '%B %d, %Y' }}</b></li>
        {% assign datelist = datelist | append: cur_date %}
      {% endunless %}
        <p style="text-indent:25px;line-height:5px;">
        <a href="{{ post.url }}">{{ post.title }}</a>
        </p>
    {% endif %}
  {% endfor %}
</ul>

