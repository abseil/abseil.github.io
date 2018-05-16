---
title: Abseil Blog
layout: blog
sidenav: side-nav-blog.html
type: markdown
---

<ul>
  {% for post in site.categories.blog  limit: 5%}
    <h2>{{ post.title }}</h2>
    <b>{{ post.date | date_to_string }}</b>
    {{ post.excerpt }}
    {% capture content_words %} 
      {{ post.content | number_of_words }} 
    {% endcapture %} 
    {% capture excerpt_words %} 
      {{ post.excerpt | number_of_words }} 
    {% endcapture %} 
    {% if excerpt_words != content_words %}
    <p><a href="{{ post.url }}/#read-more" role="button">Read more</a></p>
    {% endif %}
    <hr style="height:2px;border:none;background-color: #3F51B5;" />
  {% endfor %}
</ul>