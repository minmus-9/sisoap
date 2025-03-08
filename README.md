# Python LISP: Solution In Search Of A Problem

A couple of years ago I heard about the book "Structure and
Interpretation of Computer Programs" (SICP, available at
https://web.mit.edu/6.001/6.037/sicp.pdf). I decided to give
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
my implementation language, and soon had a simple recursive
implementation up and running. Turns out that you can't do too
much with a pure-recursive Python LISP unless you introduce
abominations like `(while)` and do things iteratively. Which
sort of defeats the purpose of the whole exercise. But it was
enough to get started reading SICP and I was hooked. On to
CPS!

It took a while to get used to CPS. After about 10,000
from-scratch rewrites of various approaches to the problem,
the code is in its present fully trampolined form with some
amount of tail-call optimization (TCO); I'm still not sure
if there's more work to do there. Homework: write 10,000
versions of LISP. The first (easy) one is a pure-recursive
implementation where leval() calls itself. Second, introduce
CPS. Third, go register-based. Fourth... Well I'm not there
yet.

Anyway, consider this code as a digital pensieve of how
trampolines and CPS work. Hopefully it'll be of interest
and help others *get* CPS. Aside from that, as a practical
library, this code is a SISOAP. If you think of something
useful to do with it, please let me know!

SICP really expanded my mind. You might consider reading
this book at least once. The code in this repo is an
implementation of part of the material in Chapter 5
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
to run code from a file. Finally,
```
./lisp.py file1 file2 ... fileN -
```
loads the specified files and then enters the REPL.

## The Language

The core language is pretty much complete I think:

|Special Form|Description|
|--------------------------|-----------------------------|
|`(begin e1 e2 ...)`|evaluate the expressions in order and return the last one|
|`(cond ((p c) ...)`|return `(eval c)` for the `(eval p)` that returns true|
|`(define sym body)`|bind `body` to `sym` in the current environment|
|`(define (sym args) body)`|bind `(lambda (args) body)` to `sym` in the current environment|
|`(do ...)`|same as `begin`|
|`(if p c a)`|return `(eval c)` if `(eval p)` returns true else `(eval a)`|
|`(lambda args body)`|create a function|
|`(quasiquote x)`|aka \`, begin quasiquoted form|
|`(quote obj)`|aka `'`, returns obj unevaluated|
|`(set! sym value)`|redefine the innermost definition of `sym`|
|`(special sym proc)`|define a special form|
|`(special (sym args) body)`|define a special form as `(lambda (args) body)`|
|`(trap obj)`|returns a list containing a success-flag and a result or error message|
|`(unquote x)`|aka `,` unquote x|
|`(unquote-splicing x)`|aka `,@` unquote and splice in x|

|Primitive|Description (see the source)|
|--------------------------|------------------------------|
|`()`|the empty list aka false|
|`#t`|true singleton|
|`(apply proc args)`|call `proc` with `args`|
|`(atom? obj)`|return true if obj is an atom: `()` `#t` or symbol|
|`(call/cc (lambda (cc) body))`|also `call-with-current-continuation`|
|`(call/cc)`|fast version of `(call/cc (lambda (cc) cc))`|
|`(car list)`|head of list|
|`(cdr list)`|tail of list|
|`(cons obj1 obj2)`|create a pair or prepend to list `obj2`|
|`(div n1 n2)`|`n1 / n2`|
|`(/ n1 n2)`|same as `div`|
|`(eq? x y)`|return true if 2 atoms are the same|
|`(equal? n1 n2)`|return true if n1 and n2 are equal|
|`(error obj)`|raise `lcore.error` with `obj`|
|`(eval obj)`|evaluate `obj`|
|`(eval obj n_up)`|evaluate `obj` up `n_up` namespaces|
|`(exit obj)`|raise `SystemExit` with the given `obj`|
|`(lt? n1 n2)`|return true if `n1 < n2`|
|`(< n1 n2)`|same as `lt?`|
|`(mul n1 n2)`|return `n1 * n2`|
|`(nand n1 n2)`|return `~(n1 & n2)`|
|`(null? x)`|return #t if x is ()|
|`(print ...)`|print a list of objects space-separated followed by a newline|
|`(range start stop step)`|same as the python function, *much* faster than FFI|
|`(set-car! list value)`|set the head of a list|
|`(set-cdr! list list`)|set the tail of a list to another list|
|`(sub n1 n2)`|`n1 - n2`|
|`(- n1 n2)`|same as `sub`|
|`(type obj)`|return a symbol representing the type of `obj`|
|`(while func)`|abomination to call `(func)` until it returns false|

You'll note that `+` is not in the list. It is implemented in the standard
library in terms of subtraction. `nand` is used to create all of the other
basic bitwise ops. There's no predefined I/O either since it isn't clear
what is wanted there, but see the next section.

## FFI

Rather than adding everything under the sun as a built-in (I'm thinking of
the large number of functions in the `math` module, specifically), I chose
to create a Foreign Function Interface (FFI) to Python to ease incorporating
additional things into this LISP-ish doodad. With this interface, Python gets
to work with native Python lists instead of LISP lists; values are converted
back and forth automatically.

The net result is that the `math` module interface looks like
```
(math symbol args...)
```
so `sin(x)` can be obtained with
```
(math 'sin x)
```
where `(math)` is something close to (sans error checking):
```
@ffi("math")
def op_ffi_math(args):
    import math
    sym = args.pop(0)
    return getattr(math, str(sym))(*args)
```
which gets you the whole `math` module at once. See the "ffi" section of
`lisp.py` for the whole scoop. There are interfaces to `math`, `random`,
and `time` so far, along with some odds and ends like `(range)` and
`(shuffle)` that require separate treatment.

## The Files

The evaluator lives in 2 files: `lcore.py` and `lisp.py`. The runtime
engine lives in `lcore.py` and is where the real action happens in
terms of trampolines, CPS, etc. The file `lisp.py` implements all of
the special forms, primitives, LISP-Python Foreign Function
Interface (FFI), etc. on top of `lcore.py` and includes a LISP runtime
embedded as a Python string so that you end up with something that is
pretty functional and can run (after obvious translations) the code
in SICP, stuff from The Goog, books, and so forth.

Please pardon my LISP coding style. I'm new to LISP and haven't quite
hit a groove yet.

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
    [do something]
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

The runtime stack is also implemented as a LISP linked list of pairs.
This is almost twice as fast as using the `list.append()` and
`lisp.pop()` methods (pronounced *function calls*). You get the
idea. This choice make continuations *cheap*. If you use a regular
list for the stack, you have to slice the whole thing to create a
continuation.

The `Context` class provides `.push()` and `.pop()` methods but
`lcore.py` doesn't use them internally. The `leval()` family of
functions inlines all of the stack operations for speed; this code
needs all the help it can get, speed-wise. You'll see things like
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
optimized a bit because they're used so much.

As a final note, passing circular data structures into the core
will definitely cause infinite loops. Fixing this would have a
grave performance impact and so it hasn't been implemented.
The Python GC is the LISP GC and any LISP circular references
will eventually get cleaned up.

## License

This code is licensed under the GPLv3:

```
SISOAP - python lisp: solution in search of a problem
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
