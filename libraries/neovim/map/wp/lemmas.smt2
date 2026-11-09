; Bit-vector checks of the two bodiless ghost lemma functions in map_int.c.
; Each block asserts the negation; z3 must answer unsat. 64-bit vectors hold the
; 32-bit values exactly (no wrap), so these are statements about integers.
; roundup_lemma: 16 <= x <= 2^31 ==> x <= ru(x) <= 2^31, ru(x) < 2x, ru(x) & (ru(x)-1) == 0
(push)
(declare-const x (_ BitVec 64))
(define-fun a0 () (_ BitVec 64) (bvsub x #x0000000000000001))
(define-fun a1 () (_ BitVec 64) (bvor a0 (bvlshr a0 #x0000000000000001)))
(define-fun a2 () (_ BitVec 64) (bvor a1 (bvlshr a1 #x0000000000000002)))
(define-fun a3 () (_ BitVec 64) (bvor a2 (bvlshr a2 #x0000000000000004)))
(define-fun a4 () (_ BitVec 64) (bvor a3 (bvlshr a3 #x0000000000000008)))
(define-fun a5 () (_ BitVec 64) (bvor a4 (bvlshr a4 #x0000000000000010)))
(define-fun r () (_ BitVec 64) (bvadd a5 #x0000000000000001))
(assert (bvule #x0000000000000010 x))
(assert (bvule x #x0000000080000000))
(assert (not (and (bvule x r) (bvule r #x0000000080000000) (bvult r (bvmul #x0000000000000002 x))
                  (= (bvand r (bvsub r #x0000000000000001)) #x0000000000000000))))
(check-sat)
(pop)
; mask_lemma: see lemmas_mask.smt2 (one check per power of two)
