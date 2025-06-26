---
title: "Performance Guide"
layout: fast
sidenav: side-nav-fast.html
type: markdown
---

This Performance Guide consists of a set of [Performance Hints](hints)
and a selection of our Performance Tips of the
Week. The Performance Tips of the Week form a sort of "Effective analysis and
optimization of production performance and resource usage": a gallery
of "do"s and "don't"s gathered from the hard-learned lessons of optimizing
performance of production systems running on machines in Google data
centers.

This set of tips started as an internal series at Google and it has been
hugely popular, with thousands of monthly readers and dozens of episodes
published. We are making some of these episodes available to a wider
external audience as they discuss topics that are common to the industry.
We publish this content to help spread knowledge in this area of production
optimization and profiling which we feel is as important as ever. We hope
you find these tips valuable and welcome your feedback.

<p class="note">
Note: the numbering of the published episodes is sparse: we retain the
original numbering of the episodes to make it easier for their authors to
refer to them and keep track of them. We also use short alias “fast” to
name the series where appropriate - this also reuses the naming convention
we use internally: it’s very common to see people referring to the episodes
as “fast/55” or “fast/23” in code discussions, bugs and other publications.
The numbering gaps will get filled as we publish more episodes.

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
    {% if post.url contains "/fast/" %}
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

