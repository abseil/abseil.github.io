---
title: "Performance Tips of the Week"
layout: fast
sidenav: side-nav-fast.html
type: markdown
---

Intro Statement

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

