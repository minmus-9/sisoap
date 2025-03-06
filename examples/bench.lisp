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
(define (smul-ref x y)
    (define (umul x y z)
        (cond
            ((equal? y 1) x) ;; y could have been -1 on entry to smul
            ((equal? 0 x) z)
            ((equal? 0 (band x 0x1)) (umul (div x 2) (add y y) z))
            (#t (umul (div x 2) (add y y) (add z y)))
        )
    )
    (cond
        ((equal? x 0) 0)
        ((equal? y 0) 0)
        ((lt? x 0) (neg (smul (neg x) y)))
        ((equal? x 1) y)
        ((equal? y 1) x)
        (#t (copysign (umul x (abs y) 0) y))
    )
)

;(define smul smul-ref)  ;; comment this for custom

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
    (pie 2) (pie 2) (pie 2) (pie 2) (pie 2) (pie 2) (pie 2) (pie 2) (pie 2) (pie 2)
    (join (reverse (three n ())) (reverse (three n ())))
    (join (reverse (three n ())) (reverse (three n ())))
    (join (reverse (three n ())) (reverse (three n ())))
    (join (reverse (three n ())) (reverse (three n ())))
    (join (reverse (three n ())) (reverse (three n ())))
)

(define (five) (four 80))

((lambda () (do (five) ())))

;; EOF
