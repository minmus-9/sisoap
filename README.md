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
abominations like `(while)` and do things iteratively. Which
sort of defeats the purpose of the whole exercise. But it was
enough to get started reading SICP and I was hooked. On to
CPS!

It took a while to get used to CPS. After about 20 independent
rewrites of various approaches to the problem, the code is in
its present fully trampolined form with some amount of
tail-call optimization (TCO); I'm still not sure if there's
more work to do there. Anyway, consider this code as a digital
pensieve of how trampolines and CPS work.

Meanwhile, SICP melted my brain. *Everyone* should consider
reading this book at least once. The code in this repo is a
from-scratch implementation of the material in Chapter 5, but
written in Python instead of Scheme. It's been a joyful
experience to watch it unfold!

## Running the Code

Use
```
./lisp.py -
```
to run the REPL and
```
./lisp.py examples/factorial.lisp
```
to run code from a file.

## The Files

The evaluator lives in 2 files: `lcore.py` and `lisp.py`. The runtime
engine lives in `lcore.py` and is where the real action happens in
terms of trampolines, CPS, etc. The file `lisp.py` implements all of
the special forms, primitives, LISP-Python Foreign Function
Interface (FFI), etc. on top of `lcore.py` and includes a LISP runtime
embedded as a Python string so that you end up with something that is
pretty functional and can run (after obvious translations) the code
in SICP.

## Code Overview

Aside from the CPS thing, the code in `lisp.py` is fairly
straightforward: each operator receives an `lcore.Context` instance
that contains the interpreter's execution state (registers, stack,
symbol table, and global environment) and returns a continuation. In
the python realm, a continuation is just a python function that is
called from `Context.trampoline()`. The trampoline is really a means
of implementing `goto` for languages that don't have `goto`.

The code in `lcore.py` is fairly optimized and is filled with
unidiomatic and somewhat bizarre constructs including gems like
```
try:
    _ = proc.__call__
    [do something with callable proc]
except AttributeError:
    pass
```
instead of
```
if callable(proc):
    [do something with callable proc]
```
and
```
if x.__class__ is list:
    [do someting]
```
instead of
```
if isinstance(x, list):
    [do something]
```

What's happening here is the elimination of Python function/method
calls *at all costs*; in particular, at the cost of readability :D
Function calls are so expensive that eliminating them can give you
a 100% speedup (Python 3.10.12 on Pop-OS! 22.04 LTS).

Pairs are represented as 2-lists so `cons(x, y)` is `[x, y]`. This,
or its equivalent, is about the only thing that works with the
mutators `set-car!` and `set-cdr!`. In particular, using regular
Python lists as LISP lists breaks when you get to `set-cdr!`.

The runtime stack is also implented as a LISP linked list of pairs.
This is almost twice as fast as using the `list.append()` and
`lisp.pop()` methods (pronounced *function calls*). You get the
idea.

The `Context` class provides `.push()` and `.pop()` methods but
doesn't use them internally. The `leval()` family of functions
inlines all of the stack operations for speed; this code needs all
the help it can get, speed-wise. You'll see things like
```
ctx.s = [x, ctx.s]  ## push(x)
```
and
```
ret, ctx.s = ctx.s
return ret  ## pop()
```
all over the place in `lcore.py`.

The code in `lisp.py` is a bit more traditional and idiomatic. It
uses `.push()`, `.pop()`, `car()`, `cdr()`, and so on to enhance
clarity and let you focus on *what* is going on instead of *how*
it's happening. The `unary()` and `binary()` helper functions are
optimized because they're used so much.

As a final note, passing circular data structures into the core
will definitely cause infinite loops. Fixing this would have a
grave performance impact and so this hasn't been done.

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
