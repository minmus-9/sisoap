#!/usr/bin/env python3
##
## sisoap - python lisp: solution in search of a problem
##       https://github.com/minmus-9/sisoap
## Copyright (C) 2025  Mark Hays (github:minmus-9)
##
## This program is free software: you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program.  If not, see <https://www.gnu.org/licenses/>.

"lisp.py -- lcore demo"

## {{{ prologue
## pylint: disable=invalid-name, too-many-lines
## XXX pylint: disable=missing-docstring

import sys

from lcore import (
    main as lmain,
    Context,
    EL,
    SENTINEL,
    Symbol,
    T,
    car,
    cdr,
    cons,
    create_continuation,
    create_lambda,
    eq,
    error,
    ffi,
    glbl,
    is_atom,
    k_leval,
    k_stringify,
    parse,
    set_car,
    set_cdr,
    spcl,
    symcheck,
)

## }}}
## {{{ helpers


def unary(ctx, f):
    try:
        x, a = ctx.argl
        if a is not EL:
            raise TypeError()
    except TypeError:
        raise SyntaxError("expected one arg") from None
    ctx.val = f(x)
    return ctx.cont


def binary(ctx, f):
    a = ctx.argl
    try:
        x, a = a
        y, a = a
        if a is not EL:
            raise TypeError()
    except TypeError:
        raise SyntaxError("expected two args") from None
    ctx.val = f(x, y)
    return ctx.cont


## }}}
## {{{ special forms


@spcl("begin")
@spcl("do")
def op_begin(ctx):
    args = ctx.argl
    if args is EL:
        ctx.val = EL
        return ctx.cont
    try:
        ctx.exp, args = args
    except TypeError:
        raise SyntaxError("expected list") from None
    if args is not EL:
        ctx.s = [args, [ctx.env, [ctx.cont, ctx.s]]]
        ctx.cont = op_begin_next
    ## if args was EL, we merely burned up a jump
    return k_leval


def op_begin_next(ctx):
    args, s = ctx.s
    try:
        ctx.exp, args = args
    except TypeError:
        raise SyntaxError("expected list") from None
    if args is EL:
        ## i didn't understand this until watching top(1) run as
        ## my tail-recursive code chewed up ram
        ##
        ## i *thought* begin/do wanted to be a special form because
        ## the order of arg evaluation is up to the implementation.
        ## since lcore explicitly evaluates args left to right, i
        ## figured it didn't really matter. but no, not even close.
        ##
        ## THIS is why it's important that begin/do be a special
        ## form: the stack is now unwound as we evaluate the
        ## last arg so we get a tail call opporuntity. if you
        ## do the moral equivalent of
        ##          (define (do & args) (last args))
        ## it'll work fine, but you don't get tco, just recursion.
        ##
        ## which you can see with top(1) :D
        ctx.env, s = s
        ctx.cont, ctx.s = s
    else:
        ctx.env = s[0]
        ctx.s = [args, s]
        ctx.cont = op_begin_next
    return k_leval


@spcl("cond")
def op_cond(ctx):
    ctx.s = [ctx.env, [ctx.cont, ctx.s]]
    return op_cond_setup(ctx, ctx.argl)


def op_cond_setup(ctx, args):
    if args is EL:
        ctx.env, s = ctx.s
        ctx.cont, ctx.s = s
        ctx.val = EL
        return ctx.cont

    ctx.env = ctx.s[0]

    pc, args = args
    try:
        ctx.exp, c = pc
        if c.__class__ is not list:
            raise TypeError()
    except TypeError:
        raise SyntaxError("expected list, got {pc!r}") from None
    if c[1] is EL:
        c = c[0]
    else:
        c = [ctx.symbol("begin"), c]
    ctx.s = [args, [c, ctx.s]]
    ctx.cont = op_cond_next
    return k_leval


def op_cond_next(ctx):
    args, s = ctx.s
    ctx.exp, s = s
    if ctx.val is EL:
        ctx.s = s
        return op_cond_setup(ctx, args)
    ctx.env, s = s
    ctx.cont, ctx.s = s
    return k_leval


@spcl("define")
def op_define(ctx):
    try:
        sym, body = ctx.argl
        if body is EL:
            raise TypeError()
    except TypeError:
        raise SyntaxError("define takes at least 2 args") from None

    if sym.__class__ is list:
        sym, params = sym
        if sym.__class__ is not Symbol:
            raise SyntaxError("expected symbol")
        if body[1] is EL:
            body = body[0]
        else:
            body = [ctx.symbol("begin"), body]
        ctx.env[sym] = create_lambda(params, body, ctx.env)
        ctx.val = EL
        return ctx.cont

    if body[1] is not EL:
        raise SyntaxError("body must be a single value")
    if sym.__class__ is not Symbol:
        raise SyntaxError("expected symbol")
    ctx.s = [sym, [ctx.env, [ctx.cont, ctx.s]]]
    ctx.exp = body[0]
    ctx.cont = k_op_define
    return k_leval


def k_op_define(ctx):
    sym, s = ctx.s
    ctx.env, s = s
    ctx.cont, ctx.s = s
    ctx.env[sym] = ctx.val
    ctx.val = EL
    return ctx.cont


## optimized (if)

@spcl("if")
def op_if(ctx):
    try:
        ctx.exp, rest = ctx.argl
        c, rest = rest
        a, rest = rest
        if rest is not EL:
            raise TypeError()
    except TypeError:
        raise SyntaxError("expected three args")
    ctx.s = [(c, a), [ctx.env, [ctx.cont, ctx.s]]]
    ctx.cont = k_op_if
    return k_leval


def k_op_if(ctx):
    ca, s = ctx.s
    ctx.env, s = s
    ctx.cont, ctx.s = s
    ctx.exp = ca[1] if ctx.val is EL else ca[0]
    return k_leval


@spcl("lambda")
def op_lambda(ctx):
    try:
        params, body = ctx.argl
        if body.__class__ is not list:
            raise TypeError()
    except TypeError:
        raise SyntaxError("expected at least 2 args") from None
    if cdr(body) is EL:
        body = car(body)
    else:
        body = cons(ctx.symbol("begin"), body)
    ctx.val = create_lambda(params, body, ctx.env)
    return ctx.cont


@spcl("quote")
def op_quote(ctx):
    ctx.val = ctx.unpack1()
    return ctx.cont


@spcl("set!")
def op_setbang(ctx):
    sym, value = ctx.unpack2()
    ctx.push(symcheck(sym))
    ctx.push_ce()
    ctx.cont = k_op_setbang
    ctx.exp = value
    return k_leval


def k_op_setbang(ctx):
    ctx.pop_ce()
    sym = ctx.pop()
    e = ctx.env
    while e is not SENTINEL:
        if sym in e:
            e[sym] = ctx.val
            ctx.val = EL
            return ctx.cont
        e = e[SENTINEL]
    raise NameError(str(sym))


@spcl("set!")
def op_setbang(ctx):
    try:
        sym, a = ctx.argl
        value, a = a
        if a is not EL:
            raise TypeError()
    except TypeError:
        raise SyntaxError("expected two args") from None
    if sym.__class__ is not Symbol:
        raise SyntaxError("expected symbol")
    ctx.s = [ctx.env, [ctx.cont, [sym, ctx.s]]]
    ctx.cont = k_op_setbang
    ctx.exp = value
    return k_leval


def k_op_setbang(ctx):
    ctx.env, s = ctx.s
    ctx.cont, s = s
    sym, ctx.s = s
    e = ctx.env
    while e is not SENTINEL:
        if sym in e:
            e[sym] = ctx.val
            ctx.val = EL
            return ctx.cont
        e = e[SENTINEL]
    raise NameError(str(sym))


@spcl("special")
def op_special(ctx):
    try:
        sym, body = ctx.argl
        if body is EL:
            raise TypeError()
    except TypeError:
        raise SyntaxError("define takes at leats 2 args") from None

    if sym.__class__ is list:
        sym, params = sym
        if cdr(body) is EL:
            body = car(body)
        else:
            body = cons(ctx.symbol("begin"), body)
        lam = create_lambda(params, body, ctx.env)
        lam.special = True
        ctx.env[symcheck(sym)] = lam
        ctx.val = EL
        return ctx.cont

    if cdr(body) is not EL:
        raise SyntaxError("body must be a single value")
    ctx.push_ce()
    ctx.push(symcheck(sym))
    ctx.exp = car(body)
    ctx.cont = k_op_special
    return k_leval


def k_op_special(ctx):
    sym = ctx.pop()
    ctx.pop_ce()
    proc = ctx.val
    if not callable(proc):
        raise SyntaxError("expected proc")
    proc.special = True
    ctx.env[sym] = proc
    ctx.val = EL
    return ctx.cont


@spcl("trap")
def op_trap(ctx):
    x = ctx.unpack1()
    ok = T
    ctx.push_ce()
    try:
        res = ctx.leval(x, ctx.env)
    except:  ## pylint: disable=bare-except
        ok = EL
        t, v = sys.exc_info()[:2]
        res = f"{t.__name__}: {str(v)}"
    ctx.pop_ce()
    ctx.val = cons(ok, cons(res, EL))
    return ctx.cont


## }}}
## {{{ quasiquote


@spcl("quasiquote")
def op_quasiquote(ctx):
    ctx.exp = ctx.unpack1()
    return qq_


def qq_(ctx):
    form = ctx.exp
    if form.__class__ is not list:
        ctx.val = form
        return ctx.cont
    app = form[0]
    if eq(app, ctx.symbol("quasiquote")):
        ## XXX proper nesting?
        ctx.argl = form[1]
        return op_quasiquote
    if eq(app, ctx.symbol("unquote")):
        ctx.argl = form
        _, ctx.exp = ctx.unpack2()
        return k_leval
    if eq(app, ctx.symbol("unquote-splicing")):
        _, __ = ctx.unpack2()
        raise SyntaxError("cannot use unquote-splicing here")
    ctx.push_ce()
    ctx.push(SENTINEL)
    return k_qq_setup(ctx, form)


def k_qq_setup(ctx, form):
    elt, form = form
    if not (form.__class__ is list or form is EL):
        raise TypeError(f"expected list, got {form!r}")
    ctx.push(form)
    ctx.push_ce()
    if elt.__class__ is list and elt[0] is ctx.symbol("unquote-splicing"):
        ctx.argl = elt
        _, ctx.exp = ctx.unpack2()
        ctx.cont = k_qq_spliced
        return k_leval
    ctx.cont = k_qq_next
    ctx.exp = elt
    return qq_


def k_qq_spliced(ctx):
    ctx.pop_ce()
    form = ctx.pop()
    value = ctx.val
    if value is EL:
        if form is EL:
            return k_qq_finish
        return k_qq_setup(ctx, form)
    while value is not EL:
        if value.__class__ is not list:
            raise TypeError(f"expected list, got {value!r}")
        elt, value = value
        if value is EL:
            ctx.val = elt
            ctx.push(form)
            ctx.push_ce()
            return k_qq_next
        ctx.push(elt)
    raise RuntimeError("bugs in the taters")


def k_qq_next(ctx):
    ctx.pop_ce()
    form = ctx.pop()
    ctx.push(ctx.val)
    if form is EL:
        return k_qq_finish
    return k_qq_setup(ctx, form)


def k_qq_finish(ctx):
    ret = EL
    while True:
        x = ctx.pop()
        if x is SENTINEL:
            break
        ret = [x, ret]
    ctx.pop_ce()
    ctx.val = ret
    return ctx.cont


## }}}
## {{{ primitives


@glbl("apply")
def op_apply(ctx):
    proc, ctx.argl = ctx.unpack2()
    try:
        _ = proc.__call__
    except AttributeError:
        raise SyntaxError(f"expected proc, got {proc!r}") from None
    return proc


@glbl("atom?")
def op_atom(ctx):
    ## you could change op_atom_f to a lambda and save a global
    ## lookup. i like being able to look at a profile and tell
    ## what's going on without having to reference the code, even
    ## with a small performance penalty
    return unary(ctx, op_atom_f)


def op_atom_f(x):
    return T if is_atom(x) else EL


@glbl("call/cc")
@glbl("call-with-current-continuation")
def op_callcc(ctx):
    ## add a little sugar for speed: if called without arguments,
    ## just return a continuation; i.e.,
    ##      (define c (call/cc))
    ## is equivalent to the idiom
    ##      (define c (call/cc (lambda (cc) cc)))
    ## but 20% faster
    args = ctx.argl
    if args is EL:
        ctx.val = create_continuation(ctx)
        return ctx.cont
    ## ok, do it the "hard way"
    try:
        proc, a = args
        if a is not EL:
            raise TypeError()
    except TypeError:
        raise SyntaxError("expected one arg") from None
    try:
        _ = proc.__call__
    except AttributeError:
        raise SyntaxError(f"expected callable, got {proc!r}") from None
    ctx.argl = cons(create_continuation(ctx), EL)
    return proc


@glbl("car")
def op_car(ctx):
    return unary(ctx, car)


@glbl("cdr")
def op_cdr(ctx):
    return unary(ctx, cdr)


@glbl("cons")
def op_cons(ctx):
    return binary(ctx, cons)


@glbl("/")
@glbl("div")
def op_div(ctx):
    return binary(ctx, op_div_f)


def op_div_f(x, y):
    if isinstance(x, int) and isinstance(y, int):
        return x // y
    return x / y


@glbl("eq?")
def op_eq(ctx):
    return binary(ctx, op_eq_f)


def op_eq_f(x, y):
    return T if eq(x, y) else EL


@glbl("equal?")
def op_equal(ctx):
    return binary(ctx, op_equal_f)


def op_equal_f(x, y):
    return T if x == y else EL


@glbl("error")
def op_error(ctx):
    raise error(ctx.unpack1())


@glbl("eval")
def op_eval(ctx):
    try:
        x = ctx.unpack1()
        n_up = 0
    except SyntaxError:
        x, n_up = ctx.unpack2()
    if x.__class__ is str:
        l = []
        parse(ctx, x, l.append)
        x = l[-1] if l else EL
    e = ctx.env
    for _ in range(n_up):
        e = e[SENTINEL]
        if e is SENTINEL:
            raise SyntaxError("no frame available")
    ctx.exp = x
    ctx.env = e
    return k_leval


@glbl("exit")
def op_exit(ctx):
    x = ctx.unpack1()
    if isinstance(x, int):
        raise SystemExit(x)
    ctx.exp = x
    ctx.cont = k_op_exit
    return k_stringify


def k_op_exit(ctx):
    raise SystemExit(ctx.val)


@glbl("lt?")
@glbl("<")
def op_lt(ctx):
    return binary(ctx, op_lt_f)


def op_lt_f(x, y):
    return T if x < y else EL


@glbl("mul")
@glbl("*")
def op_mul(ctx):
    return binary(ctx, op_mul_f)


def op_mul_f(x, y):
    return x * y


@glbl("nand")
def op_nand(ctx):
    return binary(ctx, op_nand_f)


def op_nand_f(x, y):
    if not (isinstance(x, int) and isinstance(y, int)):
        raise TypeError(f"expected integers, got {x!r} and {y!r}")
    return ~(x & y)


@glbl("null?")
def op_null(ctx):
    x = ctx.unpack1()
    ctx.val = T if x is EL else EL
    return ctx.cont


@glbl("obj>string")
def op_stringify(ctx):
    ctx.exp = ctx.unpack1()
    return k_stringify


@glbl("print")
def op_print(ctx):
    args = ctx.argl

    if args is EL:
        print()
        ctx.val = EL
        return ctx.cont

    arg, args = args

    ctx.push(ctx.cont)
    ctx.push(args)
    ctx.exp = arg
    ctx.cont = k_op_print
    return k_stringify


def k_op_print(ctx):
    args = ctx.pop()

    if args is EL:
        print(ctx.val)
        ctx.val = EL
        return ctx.pop()

    print(ctx.val, end=" ")

    arg, args = args

    ctx.push(args)
    ctx.exp = arg
    ctx.cont = k_op_print
    return k_stringify


@glbl("range")  ## this is a prim because ffi is too slow for large lists
def op_range(ctx):
    start, stop, step = ctx.unpack3()
    ret = EL
    for i in reversed(range(start, stop, step)):
        ret = cons(i, ret)
    ctx.val = ret
    return ctx.cont


@glbl("set-car!")
def op_setcar(ctx):
    return binary(ctx, set_car)


@glbl("set-cdr!")
def op_setcdr(ctx):
    return binary(ctx, set_cdr)


@glbl("sub")
@glbl("-")
def op_sub(ctx):
    try:
        x, a = ctx.argl
        if a is EL:
            x, y = 0, x
        else:
            y, a = a
            if a is not EL:
                raise TypeError()
    except TypeError:
        raise SyntaxError("expected one or two args") from None
    ctx.val = x - y
    return ctx.cont


@glbl("type")
def op_type(ctx):
    def f(x):
        ## pylint: disable=too-many-return-statements
        if x is EL:
            return ctx.symbol("()")
        if x is T:
            return ctx.symbol("#t")
        if isinstance(x, list):
            return ctx.symbol("pair")
        if isinstance(x, Symbol):
            return ctx.symbol("symbol")
        if isinstance(x, int):
            return ctx.symbol("integer")
        if isinstance(x, float):
            return ctx.symbol("float")
        if isinstance(x, str):
            return ctx.symbol("string")
        if getattr(x, "lambda_", None):
            return ctx.symbol("lambda")
        if getattr(x, "continuation", False):
            return ctx.symbol("continuation")
        if callable(x):
            return ctx.symbol("primitive")
        return ctx.symbol("opaque")

    return unary(ctx, f)


@glbl("while")
def op_while(ctx):
    try:
        x, a = ctx.argl
        if a is not EL:
            raise TypeError()
    except TypeError:
        raise SyntaxError("expected one arg") from None
    if not callable(x):
        raise TypeError(f"expected callable, got {x!r}")

    ctx.s = [ctx.env, [x, [ctx.cont, ctx.s]]]
    ctx.argl = EL
    ctx.cont = k_op_while
    return x


def k_op_while(ctx):
    ctx.env, s = ctx.s
    x = s[0]

    if ctx.val is EL:
        s = s[1]
        cont, ctx.s = s
        return cont
    ctx.s = [ctx.env, s]
    ctx.argl = EL
    ctx.cont = k_op_while
    return x


## }}}
## {{{ ffi


def module_ffi(args, module):
    if not args:
        raise TypeError("at least one arg required")
    sym = symcheck(args.pop(0))
    func = getattr(module, str(sym), SENTINEL)
    if func is SENTINEL:
        raise ValueError(f"function {sym!r} does not exist")
    return func(*args)


@ffi("math")
def op_ffi_math(args):
    import math  ## pylint: disable=import-outside-toplevel

    return module_ffi(args, math)


@ffi("random")
def op_ffi_random(args):
    import random  ## pylint: disable=import-outside-toplevel

    return module_ffi(args, random)


@ffi("shuffle")
def op_ffi_shuffle(args):
    import random  ## pylint: disable=import-outside-toplevel

    (l,) = args
    random.shuffle(l)
    return l


@ffi("time")
def op_ffi_time(args):
    import time  ## pylint: disable=import-outside-toplevel

    def f(args):
        return [tuple(arg) if isinstance(arg, list) else arg for arg in args]

    return module_ffi(f(args), time)


## }}}
## {{{ lisp runtime


RUNTIME = r"""
;; {{{ basics

;; to accompany quasiquote
(define (unquote x) (error "cannot unquote here"))
(define (unquote-splicing x) (error "cannot unquote-splicing here"))

;; used everywhere
(define (pair? x) (if (eq? (type x) 'pair) #t ()))
(define (list & args) args)

;; ditto
(define (cadr l) (car (cdr l)))
(define (caddr l) (car (cdr (cdr l))))
(define (cadddr l) (car (cdr (cdr (cdr l)))))
(define (caddddr l) (car (cdr (cdr (cdr (cdr l))))))

;; }}}
;; {{{ foreach
;; call f for each element of lst, returns ()

(define (foreach f lst)
    (if
        (null? lst)
        ()
        (begin
            (f (car lst))
            (foreach f (cdr lst))
        )
    )
)

;; }}}
;; {{{ last

(define (last lst)
    (if
        (null? (cdr lst))
        (car lst)
        (last (cdr lst))
    )
)

;; }}}
;; {{{ bitwise ops

;; bitwise ops from nand
(define (bnot x)   (nand x x))
(define (band x y) (bnot (nand x y)))
(define (bor  x y) (nand (bnot x) (bnot y)))
(define (bxor x y) (band (nand x y) (bor x y)))

;; }}}
;; {{{ arithmetic

(define (+ x y) (- x (- y)))
(define add +)

;; oh, mod
(define (% n d) (- n (* d (/ n d))))

;; absolute value
(define (abs x)
    (if
        (< x 0)
        (- x)
        x
    )
)

;; copysign
(define (copysign x y)
    (if
        (< y 0)
        (- (abs x))
        (abs x)
    )
)

;; unsigned shifts
(define (lshift x n)
    (cond
        ((equal? n 0)   x)
        ((equal? n 1)   (+ x x))
        (#t             (lshift x (lshift x 1) (- n 1)))
    )
)

(define (rshift x n)
    (cond
        ((equal? n 0)   x)
        ((equal? n 1)   (/ x 2))
        (#t             (rshift x (rshift x 1) (- n 1)))
    )
)

;; }}}
;; {{{ comparison predicates

(define (<= x y) (if (< x y) #t (if (equal? x y) #t ())))
(define (>= x y) (not (< x y)))
(define (>  x y) (< y x))
(define (!= x y) (not (equal? x y)))

;; }}}
;; {{{ and or not

(special (and & __special_and_args__)
    ((lambda (c)
        (cond
            ((null? __special_and_args__) ())
            ((null? (cdr __special_and_args__))
                (eval (car __special_and_args__)))
            ((eval (car __special_and_args__)) (begin
                (set! __special_and_args__ (cdr __special_and_args__))
                (c c)
            ))
            (#t ())
        )
    ) (call/cc) )
)

(special (or & __special_or_args__)
    ((lambda (c)
        (cond
            ((null? __special_or_args__) ())
            ((eval (car __special_or_args__)) #t)
            (#t (begin
                (set! __special_or_args__ (cdr __special_or_args__))
                (c c)
            ))
        )
    ) (call/cc) )
)

(define not null?)

;; }}}
;; {{{ assert

(special (assert __special_assert_sexpr__)
    (if
        (eval __special_assert_sexpr__)
        ()
        (error (obj>string __special_assert_sexpr__))
    )
)

;; }}}
;; {{{ reverse

(define (reverse l)
    (define (rev x y)
        (if
            (null? x)
            y
            (rev (cdr x) (cons (car x) y))
        )
    )
    (rev l ())
)

;; }}}
;; {{{ iter and enumerate

(define (iter lst fin)
    (define item ())
    (define (next)
        (if
            (null? lst)
            fin
            (begin
                    (set! item (car lst))
                    (set! lst (cdr lst))
                    item
            )
        )
    )
    next
)

(define (enumerate lst fin)
    (define index 0)
    (define item fin)
    (define (next)
        (if
            (null? lst)
            fin
            (begin
                    (set! item (list index (car lst)))
                    (set! index (+ index 1))
                    (set! lst (cdr lst))
                    item
            )
        )
    )
    next
)

;; }}}
;; {{{ length

(define (length l)
    (define n 0)
    (define c (call/cc))
    (if
        (null? l)
        n
        (begin
            (set! n (+ n 1))
            (set! l (cdr l))
            (c c)
        )
    )
)

;; }}}
;; {{{ fold, transpose, map
;; sicp p.158-165 with interface tweaks
(define (fold-left f initial sequence)
    (define r initial)
    (foreach (lambda (elt) (set! r (f elt r))) sequence)
    r
)

(define reduce fold-left)  ;; python nomenclature

(define (fold-right f initial sequence)
      (fold-left f initial (reverse sequence)))

(define accumulate fold-right)  ;; sicp nomenclature

;(fold-left  cons () (list 1 4 9))  ;; (9 4 1)    (cons 9 (cons 4 (cons 1 ())))
;(fold-right cons () (list 1 4 9))  ;; (1 4 9)    (cons 1 (cons 4 (cons 9 ())))

(define (map1 f lst)
    (define (g elt r) (cons (f elt) r))
    (fold-right g () lst)
)

(define (accumulate-n f initial sequences)
    (define r ())
    (define c (call/cc))
    (if
        (null? (car sequences))
        (reverse r)
        (begin
            (set! r (cons (accumulate f initial (map1 car sequences)) r))
            (set! sequences (map1 cdr sequences))
            (c c)
        )
    )
)

(define (transpose lists) (accumulate-n cons () lists))

(define (map f & lists)
    (define (g tuple) (apply f tuple))
    (map1 g (transpose lists))
)

;; }}}
;; {{{ join

(define (join x y)
    (if
        (null? x)
        y
        (begin
            (define ht (join$start (car x)))
            (join$1 (cdr x) ht)
            (set-cdr! (cdr ht) y)
            (car ht)
        )
    )
)

(define (join$start x)
    (define n (cons x ()))
    (cons n n)
)

(define (join$1 x ht)
    (if
        (null? x)
        (car ht)
        (begin
            (define n (cons (car x) ()))
            (set-cdr! (cdr ht) n)
            (set-cdr! ht n)
            (join$1 (cdr x) ht)
        )
    )
)

;; }}}
;; {{{ let

(special (let __special_let_vdefs__ __special_let_body__)
    (eval (let$ __special_let_vdefs__ __special_let_body__) 1))

(define (let$ vdefs body)
    (define vdecls (transpose vdefs))
    (define vars (car vdecls))
    (define vals (cadr vdecls))
    `((lambda (,@vars) ,body) ,@vals)
)

;; }}}
;; {{{ let*

(special (let* __special_lets_vdefs__ __special_lets_body__)
    (eval (let*$ __special_lets_vdefs__ __special_lets_body__) 1))

(define (let*$ vdefs body)
    (if
        (null? vdefs)
        body
        (begin
            (define kv (car vdefs))
            (set! vdefs (cdr vdefs))
            (define k (car kv))
            (define v (cadr kv))
          `((lambda (,k) ,(let*$ vdefs body)) ,v)
        )
    )
)

;; }}}
;; {{{ letrec
;; i saw this (define x ()) ... (set! x value) on stackoverflow somewhere

(special (letrec __special_letrec_decls__ __special_letrec_body__)
    (eval (letrec$ __special_letrec_decls__ __special_letrec_body__) 1))

(define (letrec$ decls & body)
    (define names (map1 car decls))
    (define values (map1 cadr decls))
    (define (declare var) `(define ,var ()))
    (define (initialize var-value) `(set! ,(car var-value) ,(cadr var-value)))
    (define (declare-all) (map1 declare names))
    (define (initialize-all) (map1 initialize decls))
    `((lambda () (begin ,@(declare-all) ,@(initialize-all) ,@body)))
)

;; }}}
;; {{{ associative table

(define (table compare)
    (define items ())
    (define (dispatch m & args)
        (cond
            ((eq? m 'known) (not (null? (table$find items key compare))))
            ((eq? m 'del) (set! items (table$delete items (car args) compare)))
            ((eq? m 'get) (begin
                (let* (
                    (key (car args))
                    (node (table$find items key compare)))
                    (if
                        (null? node)
                        ()
                        (cadr node)
                    )
                )
            ))
            ((eq? m 'iter) (begin
                (let ((lst items))
                    (lambda ()
                        (if
                            (null? lst)
                            ()
                            (begin
                                (define ret (car lst))
                                (set! lst (cdr lst))
                                ret
                            )
                        )
                    )
                )
            ))
            ((eq? m 'len) (length items))
            ((eq? m 'raw) items)
            ((eq? m 'set) (begin
                (let* (
                    (key (car args))
                    (value (cadr args))
                    (node (table$find items key compare)))
                    (if
                        (null? node)
                        (begin
                            (let* (
                                (node (cons key (cons value ()))))
                                (set! items (cons node items)))
                        )
                        (set-car! (cdr node) value)
                    )
                )
            ))
            (#t (error "unknown method"))
        )
    )
    dispatch
)

(define (table$find items key compare)
    (cond
      ((null? items) ())
      ((compare (car (car items)) key) (car items))
      (#t (table$find (cdr items) key compare))
    )
)

(define (table$delete items key compare)
    (define prev ())
    (define (helper assoc key)
        (cond
            ((null? assoc) items)
            ((compare (car (car assoc)) key) (begin
                (cond
                    ((null? prev) (cdr assoc))
                    (#t (begin (set-cdr! prev (cdr assoc)) items))
                )
            ))
            (#t (begin
                (set! prev assoc)
                (helper (cdr assoc) key)
            ))
        )
    )
    (helper items key)
)

;; }}}
;; {{{ looping: loop, for

;; call f in a loop forever
(define (loop f)
    (define c (call/cc))
    (f)
    (c c)
)

;; call f a given number of times as (f counter)
(define (for f start stop step)
    (if
        (< step 1)
        (error "step must be positive")
        (for$ f start stop step)
    )
)

(define (for$ f start stop step)
    (if
        (< start stop)
        (begin
            (f start)
            (for$ f (- start (- 0 step)) stop step)
        )
        ()
    )
)

;; }}}
;; {{{ iterate (compose with itself) a function

(define (iter-func f x0 n)
    (define c (call/cc))
    (if
        (lt? n 1)
        x0
        (begin
            (set! x0 (f x0))
            (set! n (sub n 1))
            (c c)
        )
    )
)

;; }}}
;; {{{ benchmarking

(define (timeit f n)
    (define t0 (time 'time))
    (for f 0 n 1)
    (define t1 (time 'time))
    (define dt (sub t1 t0))
    (if (lt? dt 1e-7) (set! dt 1e-7) ())
    (if (lt? n 1) (set! n 1) ())
    (list n dt (mul 1e6 (div dt n)) (div n dt))
)

;; }}}
;; {{{ gcd

(define (gcd x y)
    (cond
        ((lt? x y) (gcd y x))
        ((equal? x 0) 1)
        (#t
            (define c (call/cc))
            (if
                (equal? y 0)
                x
                (begin
                    (define r (mod x y))
                    (set! x y)
                    (set! y r)
                    (c c)
                )
            )
        )
    )
)

;; }}}

;; EOF
"""


## }}}


def main():
    ctx = Context()
    parse(ctx, RUNTIME, ctx.leval)
    return lmain(ctx)


if __name__ == "__main__":
    main()


## EOF
