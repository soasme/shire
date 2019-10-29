---
title: Mark Something Fun!
slug: docs/introduction
date: 2019-12-01
category: Product
---

> Make pie, or invent universe. [@soasme](https://www.douban.com/people/soasme/)

Hi guys, my name is Ju Lin. I'm making a fun website, entitled MarkSthFun (<https://marksth.fun>).
You can pronounce it as "Mark Something Fun".

## Motivate

I was a [douban](https://www.douban.com) user, in which I can mark the books I have read, movies I have watched, and albums I have listened. I was even a former Douban employee during 2012-2015. It was the best of the moments in my career. I met a lot of the most talented engineers there. It's like a sacred place in my mind. Even today, I still feel Douban's culture has influenced me the most. However, I was no longer able to live with it. Based on the cyber security law of the People's Republic of China, a user account without a verified phone number is prohibited from using the website. But I refuse to provide it. Not to mention years' carefulness of avoiding my content being censored. I had enough, really. Enough.

I could have marked my book on goodreads, marked my traces on google maps. But I do not trust Amazon/Google as well. (Facebook is the worst.)

Since there is no tool / service in the market that fits me well, as an engineer, I started building my own.

## Introduction

So, this is it. In MarkSthFun, you can mark the books you have read, the movies you have watched,
the albums you have listened, the games you have played, the places you have visited, the software you have used, the papers you have read, the concepts you have learned, etc.
You can write notes for your marks and manage things by tags.
You can decide whether to share your things publicly or not.
You can discover fun things marked by fun people, of course, if they're willing to share.
You can search marks by types, tags and keywords.

## Principles

Below are the principles that I keep in mind when building this new website.

* Marking is way more important than socializing.
* Keep your data safe over the long term.
* If you want to know more about a person, read his RSS feed.
* You deserve a private account if you're an introverted person.
* Unshare your mark if you don't to expose too much of your life traces.
* No ads.
* No third-party tracking.
* No like, no vote, no comment, no retweet.
* The fewer images displaying on the site the better.
* Encrypt your requests when browsing.
* Use boring technology stack for sane people.
* Don't overkill.
* Be alone. Develop and operate this site by a single-person team.
* Be conservative on adding new features.
* Pay for what you get. You'll need to pay me $1 per month.

## Implementation

Currently, MarkSthFun is written in Python, Flask, SQLAlchemy. The site uses PostgreSQL as database. Redis is used as cache and message queue. It uses prometheus and grafana for monitoring. The site runs servers provisioned as digitalocean droplets with 1cpu-1gb to save the cost. Terraform and ansible are used for provisioning cloud resources and deploying code. Heroku is used for staging. You'll be bored for the most part of the implementation, no kubernetes, no container, no serverless, no big data, no machine learning.

Here is a [list](https://marksth.fun/u/soasme/t/marksthfun-stack/) of technology stack that MarkSthFun is using, and of course, it's being listed in a MarkSthFun-style list. ;)

## Conclusion

If you like what I'm building, do not hesitated signing up.
It only cost you a cup of coffee ☕ per quarter.
If you can invite a friend to join, you don't need to pay for the next year subscription fee.

Enjoy your marking from today! [https://marksth.fun](https://marksth.fun)
