---
title: Mark Something Fun!
slug: docs/introduction
date: 2019-12-01
category: Product
---

> Make pie, or invent universe. [@soasme](https://www.douban.com/people/soasme/)

Hi guys, my name is Ju Lin. I'm making a fun website, entitled MarkSthFun (<https://marksth.fun>).
You can pronounce it as "Mark Something Fun."

## Motivate

I was a [douban](https://www.douban.com) user, in which I can mark the books I have read, the movies I have watched, and the albums I have listened to. I was even a former Douban employee during 2012-2015. It was the best of the moments in my career. I met a lot of the most talented engineers there. It's like a sacred place in my mind. Even today, I still feel Douban's culture has influenced me the most. However, I was no longer able to live with it. Based on the cybersecurity law of the People's Republic of China, a user account without a verified phone number is prohibited from using the website. But I refuse to provide it. Not to mention years' carefulness of avoiding my content being censored. I had enough.

I could have marked my book on Goodreads, marked my traces on Google Maps. But I do not trust Amazon/Google as well. (Facebook is the worst.)

Since there is no tool/service in the market that fits me well, as an engineer, I started building my own.

## Introduction

So, this is it. In MarkSthFun, you can mark the books you have read, the movies you have watched,
the albums you have listened, the games you have played, the places you have visited, the software you have used, the papers you have read, the concepts you have learned, etc.
You can write notes for your marks and manage things by tags.
You can decide whether to share your marks publicly or not.
You can discover fun things marked by fun people, of course, if they're willing to share.
You can search for marks by types, tags, and keywords.

## Principles

Below are the principles that I keep in mind when building this new website.

* Marking is way more important than socializing.
* Keep your data safe over the long term.
* If you want to know more about a person, read his RSS feed.
* You deserve a private account if you're an introverted person.
* Unshare your mark if you don't expose too much of your life traces.
* No ads.
* No third-party tracking.
* No like, no vote, no comment, no retweet.
* Display as less images as possible.
* Encrypt your requests when browsing.
* Don't overkill.
* Be conservative about adding new features.
* Pay for what you get.
* Use boring technology stack for sane people.

## Implementation

Currently, MarkSthFun is written in Python, Flask, SQLAlchemy. The site uses PostgreSQL as the database. Redis is used as the cache and the message queue. It uses Prometheus and Grafana for monitoring. The site runs servers provisioned as Digitalocean droplets with 1cpu-1gb to save the cost. Terraform, and ansible are used for provisioning cloud resources and deploying code. I use Heroku for staging. You'll be bored for the most part of the implementation, no Kubernetes, no container, no serverless, no big data, no machine learning.

Here is a [list](https://marksth.fun/u/soasme/t/marksthfun-stack/) of the technology stack that MarkSthFun is using, and of course, it's being listed in a MarkSthFun-style list. ;)

## Conclusion

If you like what I'm building, do not hesitate to sign up.
It only cost you a cup of coffee ☕ per quarter.

Enjoy your marking from today! [https://marksth.fun](https://marksth.fun)
