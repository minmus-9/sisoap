;; factorial.lisp - yup
;;
;; sisoap - python lisp: solution in search of a problem
;;       https://github.com/minmus-9/sisoap
;; Copyright (C) 2025  Mark Hays (github:minmus-9)
;; 
;; This program is free software: you can redistribute it and/or modify
;; it under the terms of the GNU General Public License as published by
;; the Free Software Foundation, either version 3 of the License, or
;; (at your option) any later version.
;; 
;; This program is distributed in the hope that it will be useful,
;; but WITHOUT ANY WARRANTY; without even the implied warranty of
;; MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
;; GNU General Public License for more details.
;; 
;; You should have received a copy of the GNU General Public License
;; along with this program.  If not, see <https://www.gnu.org/licenses/>.
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

;; classic recursive
(define (!1 n)
    (if
        (lt? n 2)
        1
        (mul n (!2 (sub n 1)))
    )
)

;; classic iterative
(define (!2 n)
    (define (iter n! k)
        (if
            (lt? k 2)
            n!
            (iter (mul n! k) (sub k 1))
        )
    )
    (iter 1 n)
)

;; cheating :-)
(define (!3 n)
     (math 'factorial n)
)

(define (!4 n)
    (if
        (define n! 1)
        ()
        ((lambda (c _ _)                ;; huh. gotta love it!
            (if (lt? n 2) n! (c c)))    ;; misleading formatting++
            (call/cc)
            (set! n! (mul n! n))
            (set! n (sub n 1))
        )
    )
)

(define (!5 n)
    (define n! 1)
    (define c (call/cc))
    (if
        (lt? n 2)
        n!
        (begin
            (set! n! (mul n n!))
            (set! n  (sub n 1))
            (c c)
        )
    )
)

(define (!6 n)
     (define n! 1)
     (define (f k) (set! n! (mul n! k)))
     (for f 2 (add n 1) 1)
     n!
)

(define (!7 n)
    (define cont ())
    (define n! 1)
    (define k (call/cc (lambda (cc) (set! cont cc) n)))
    (set! n! (mul n! k))
    (cond
        ((lt? n 1) 1)
        ((lt? k 2) n!)
        (#t (cont (sub k 1)))
    )
)

(define (!8 n)
    (fold-left mul 2 (range 3 (add n 1) 1))
)

(define (xrange start stop step)
    (define i (sub start step))
    (define (next)
        (if
            (>= i stop)
            ()
            (begin
                (set! i (add i step))
                i
            )
        )
    )
    next
)

(define (!9 n)
    (define (f r)
        (if
            (null? (begin (define k ((car r))) k))
            (cdr r)
            (f (cons (car r) (mul (cdr r) k)))
        )
    )
    (f (cons (xrange 2 n 1) 1))
)

(define (!10 n)
    (let* (
        (it (xrange 2 n 1))
        (c  ())
        (n! 1)
        (k  (call/cc (lambda (cc) (set! c cc) (it)))))
        (if
            (null? k)
            n!
            (begin (set! n! (mul n! k)) (c (it)))
        )
    )
)

(define (!11 n)
    (define c ())
    ((lambda (n! k)
        (set! n (sub k 1))
        (if (lt? k 2) n! (c (mul n! k))))
        (call/cc (lambda (cc) (set! c cc) 1))
        n
    )
)

(define (!12 n)
    (define c ())
    (define (f n!k)
        (if
            (lt? (cdr n!k) 2)
            (car n!k)
            (c
                (cons
                    (mul (car n!k) (cdr n!k))
                    (sub (cdr n!k) 1)
                )
            )
        )
    )
    (f
        (call/cc
            (lambda (cc) (set! c cc) (cons 1 n))
        )
    )
)

(define (!13 n)
    (define (f info)
        (if
            (lt? (cadr info) 2)
            (car info)
            ((caddr info)
                (list
                    (mul (car info) (cadr info))
                    (sub (cadr info) 1)
                    (caddr info)
                )
            )
        )
    )
    (f (call/cc (lambda (cc) (list 1 n cc))))
)

(define (!14 n)
    (define (f x)
        (set! n (sub n 1))
        (mul n x)
    )
    (iter-func f n (sub n 1))
)

(define (!15 n)
    (define (f nn!)
        (define n (car nn!))
        (define n! (cdr nn!))
        (cons
            (add n 1)
            (mul n n!)
        )
    )
    (cdr (iter-func f (cons 1 1) n))
)

(define (!16 n)
    (define n! 1)
    ((lambda (c & _)
        (if (lt? n 2) n! (c c)))
        (call/cc)
        (set! n! (mul n! n))
        (set! n  (sub n  1))
    )
)

(define (!17 n)
    (define l ())
    (define n! 1)
    (for
        (lambda (k) (set! l (cons k l)))
        2
        (add n 1)
        1
    )
    (while (lambda ()
        (if
            (null? l)
            ()
            (begin
                (set! n! (mul n! (car l)))
                (set! l (cdr l))
                #t
            )
        )
    ))
    n!
)

(define (!18 n)
    (cond
        ((lt? n 2) 1)
        ((lt? n 3) 2)
        ((lt? n 4) 6)
        ((lt? n 5) 24)
        (#t (mul n (!18 (sub n 1))))
    )
)

(define (!19 n)
    ((lambda (f) (f f 1 n))
        (lambda (f p k)
            (if (< k 2)
                p
                (f f (* p k) (- k 1))
            )
        )
    )
)

(define (!bench)
    (define reps 5)
    (define n 400)
    (print '- (timeit (lambda (_) ()) 100))
    (print '!1  (timeit (lambda (_) (!1 n)) reps))
    (print '!2  (timeit (lambda (_) (!2 n)) reps))
    (print '!3  (timeit (lambda (_) (!3 n)) reps))
    (print '!4  (timeit (lambda (_) (!4 n)) reps))
    (print '!5  (timeit (lambda (_) (!5 n)) reps))
    (print '!6  (timeit (lambda (_) (!6 n)) reps))
    (print '!7  (timeit (lambda (_) (!7 n)) reps))
    (print '!8  (timeit (lambda (_) (!8 n)) reps))
    (print '!9  (timeit (lambda (_) (!9 n)) reps))
    (print '!10 (timeit (lambda (_) (!10 n)) reps))
    (print '!11 (timeit (lambda (_) (!11 n)) reps))
    (print '!12 (timeit (lambda (_) (!12 n)) reps))
    (print '!13 (timeit (lambda (_) (!13 n)) reps))
    (print '!14 (timeit (lambda (_) (!14 n)) reps))
    (print '!15 (timeit (lambda (_) (!15 n)) reps))
    (print '!16 (timeit (lambda (_) (!16 n)) reps))
    (print '!17 (timeit (lambda (_) (!17 n)) reps))
    (print '!18 (timeit (lambda (_) (!18 n)) reps))
    (print '!19 (timeit (lambda (_) (!19 n)) reps))
)
(timeit (lambda (_) (!bench)) 1)
