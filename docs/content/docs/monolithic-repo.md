---
title: MarkSthFun Uses Monolithic Repository!
slug: docs/monolithic-repo
date: 2019-12-01
category: Engineering
---

In software engineering, you have two typical choices managing your code:

1. A single repo that includes all of your code.
2. Many small repos, each of which is a component of your app.

People has debated the pros/cons of the two options for a long time, especially after the rise of microservices architecture.

In particular, a monolithic repo refers the option 1. And MarkSthFun uses monolithic repo.

Below are reasons I prefer using monolithic repo.

* I'm in a one-person team, doing all kinds of work, including feature prioritizing, development, bug fixes, operations, etc. Gathering all things in one place just help me do my job faster. And time matters me the most.
* Because of the size of the team, communication problem isn't important. I don't need to split the codebase and make different contracts between repos.
* My [technology stack](https://marksth.fun/u/soasme/t/marksthfun-stack/) is small and consistent. Various pats of the code base share the same coding styles.
* As far as I can see, the size of the repo can still be manageable, as I'm conservative of adding any new code.

In short, it suits me.
