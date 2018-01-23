---
title: Abseil Blog
layout: blog
sidenav: side-nav-blog.html
type: markdown
---

<ul>
  {% for post in site.posts %}
    {% unless post.title contains "Tip of the Week" %}
    <li>
        <a href="{{ post.url }}">{{post.date | date_to_string}} - {{ post.title }}</a>
    </li>
    {% endunless %}
  {% endfor %}
</ul>