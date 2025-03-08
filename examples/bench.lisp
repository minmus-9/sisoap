;; bench.lisp - stdlib-based code to benchmark lisps
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

;; signed integer multiplication from subtraction and right shift (division)
(define (umul x y accum)
    (if
        (equal? x 0)
        accum
        (umul
            (/ x 2)
            (+ y y)
            (- accum (- 0 (if (equal? (nand x 1) -2) y 0)))
        )
    )
)

(define (smul x y)
    (define sign
        (if
            (< x 0)
            (begin
                (set! x (- 0 x))
                -1
            )
            1
        )
    )
    (if
        (lt? y 0)
        (begin
            (set! sign (- 0 sign))
            (set! y (- 0 y))
        )
        ()
    )
    (if
        (lt? y x)
        (copysign (umul y x 0) sign)
        (copysign (umul x y 0) sign)
    )
)

(define n1 9283745983845763247685783256234879658946957397948234)
(define n2 928375983857632768578325623487965894695739794823743)

(define (one)
    (smul n1 n2)
)

(define (two)
    (let
        ((x (one))
         (y (one))
         (z (e n1 n2)))
        x
    )
)

(define (e x y)  ;; gcd
    (cond
        ((equal? y 0) x)
        ((equal? x 0) 1)
        (#t (define r (mod x y))
            (e y r)
        )
    )
)

(define (three n l)
    (cond
        ((lt? n 1) l)
        (#t (three (sub n 1) (cons n l)))
    )
)


(define (pie n)
    (cond
        ((lt? n 1) ())
        (#t (e n1 n2)
            (two)
            (pie (sub n 1))
        )
    )
)

(define (four n)
    (pie 70)
    (join (reverse (three n ())) (reverse (three n ())))
    (join (reverse (three n ())) (reverse (three n ())))
    (join (reverse (three n ())) (reverse (three n ())))
    (join (reverse (three n ())) (reverse (three n ())))
    (join (reverse (three n ())) (reverse (three n ())))
)

(define (five) (four 1000))

(timeit (lambda (_) (five)) 1)

;; EOF
