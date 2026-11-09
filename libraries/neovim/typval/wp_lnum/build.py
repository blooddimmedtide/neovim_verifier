"""tv_get_lnum_buf (upstream, wraps) and the fixed version with tv_number_to_lnum, for WP.
Usage: python3 -I build.py <tree> <out.c> upstream|fixed
Pieces are verbatim and sha256 pinned; tv_get_number_chk is used through its proved contract
(../wp/contracts.py, the same prelude)."""
import hashlib, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "wp"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "..", "tools"))
from extract_c import find
from contracts import PRELUDE, CHECKS
TV = "src/nvim/eval/typval.c"
SHA = {
    "upstream": {"tv_get_lnum_buf": "b4b89c95d6f5b86b612d94de21479270ec544c7a5f7dee55c80b092a49988e69"},
    "fixed": {"tv_number_to_lnum": "64c77c3334080f065767a457ec7103cf04feb288a43bc7bd591d064cca6b8f8c", "tv_get_lnum_buf": "e062aa02239bfd7afbe0206c54ce1f5359bdedf82026f3b7594e647fa835b00c"},
}
EXTRA = r'''
typedef int32_t linenr_T;
enum { MAXLNUM = 0x7fffffff, };  ///< Maximal (invalid) line number
// buf_T reduced to the one field read here (b_ml.ml_line_count).
typedef struct { linenr_T ml_line_count; } memline_T;
typedef struct { memline_T b_ml; } buf_T;
#define FUNC_ATTR_CONST
static linenr_T tv_number_to_lnum(const varnumber_T n);

/*@ requires num_pre((typval_T *)tv);
    requires buf == \null || \valid_read(buf);
    requires tv->v_type == VAR_STRING && tv->vval.v_string != \null ==> \valid_read(tv->vval.v_string + (0 .. 1));
    assigns vp_msgs;
    behavior dollar: assumes tv->v_type == VAR_STRING && tv->vval.v_string != \null
                     && tv->vval.v_string[0] == '$' && tv->vval.v_string[1] == 0 && buf != \null;
      ensures \result == buf->b_ml.ml_line_count;
    behavior number: assumes tv->v_type == VAR_NUMBER;
      // the line number is the Number itself when it fits, else clamped: never wraps
      ensures \result == (tv->vval.v_number > MAXLNUM ? MAXLNUM :
                          tv->vval.v_number < INT32_MIN ? INT32_MIN : tv->vval.v_number); */
linenr_T tv_get_lnum_buf(const typval_T *const tv, const buf_T *const buf);

/*@ assigns \nothing;
    ensures \result == (n > MAXLNUM ? MAXLNUM : n < INT32_MIN ? INT32_MIN : n); */
static linenr_T tv_number_to_lnum(const varnumber_T n);
'''
def main():
    tree, out, mode = sys.argv[1:4]
    for path, text in CHECKS + [("src/nvim/pos_defs.h", "typedef int32_t linenr_T;"),
                                ("src/nvim/pos_defs.h", "enum { MAXLNUM = 0x7fffffff, };  ///< Maximal (invalid) line number")]:
        if text not in open(f"{tree}/{path}").read().split("\n"):
            sys.exit(f"build: {path} no longer contains: {text}")
    lines = open(f"{tree}/{TV}").read().split("\n")
    parts = [PRELUDE, EXTRA]
    for name, want in SHA[mode].items():
        s, e = find(lines, name)
        piece = "\n".join(lines[s:e + 1]); h = hashlib.sha256(piece.encode()).hexdigest()
        if h != want:
            sys.exit(f"build: {name} differs from the pinned text: {h}")
        parts.append(f"// {TV}:{s + 1} (verbatim {mode}, sha256 {h})\n{piece}\n")
    # tv_get_number_chk itself is not included: only its contract (prototype in PRELUDE) is used.
    open(out, "w").write("\n".join(parts))
main()
