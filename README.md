# Python LISP: Solution In Search Of A Problem

A couple of years ago I heard about the book "Structure and
Interpretation of Computer Programs" (SICP, available at
https://web.mit.edu/6.001/6.037/sicp.pdf). I dedcided to give
it a read and immediately ran into a problem: I didn't know
Scheme. After looking around at the 10,000 Scheme-s I decided
that *I* would be best served by implementing my own LISP-y
thing. It wasn't successful; I just didn't *get it* despite
having read a bunch of code and docs.

In the meantime I read the Trampoline paper
(https://dl.acm.org/doi/pdf/10.1145/317636.317779) and became
interested in continuations, trampolines, and continuation
passing style (CPS). But I still didn't *get* LISP enough to
implement it.

About 18 months later while on vacation, I woke up one morning
*getting it*. Being a 30-year Python veteran, I chose that as
my implentation language, and soon had a simple recursive
implementation up and running. Turns out that you can't do too
much with a pure-recursive Python LISP unless you introduce
abominations like `(while)` and do thing iteratively. Which sort
of defeats the purpose of the whole exercise.


## License

This code is licensed under the GPLv3:

```
sisoap - python lisp: solution in search of a problem
       https://github.com/minmus-9/sisoap
Copyright (C) 2025  Mark Hays (github:minmus-9)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
```

The file LICENSE contains a copy of the full GPL text.

## References

Here are some lisp-related refs that *heavily* influenced this code:

- https://web.mit.edu/6.001/6.037/sicp.pdf (*especially Chapter 5*)
- https://buildyourownlisp.com
- https://www.hashcollision.org/hkn/python/pyscheme/
- https://norvig.com/lispy.html
- https://norvig.com/lispy2.html
- https://github.com/rain-1/single_cream
- https://github.com/Robert-van-Engelen/tinylisp
- https://dl.acm.org/doi/pdf/10.1145/317636.317779
- https://en.wikipedia.org/wiki/Continuation-passing_style
- https://blog.veitheller.de/Lets_Build_a_Quasiquoter.html
- https://paulgraham.com/rootsoflisp.html
- https://www-formal.stanford.edu/jmc/index.html
- https://www-formal.stanford.edu/jmc/recursive.pdf
- https://legacy.cs.indiana.edu/~dyb/papers/3imp.pdf
