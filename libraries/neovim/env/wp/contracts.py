# ACSL contracts written from the doc comments in env.c, not from the code.
# Caller preconditions are listed in ../PLAN.md.
CONTRACTS = {
"env_name_valid": ("static bool env_name_valid(const char *name)", r"""requires \valid_read(name);
    assigns \nothing;
    ensures \result <==> name[0] != 0;"""),

"vim_env_iter": ("const void *vim_env_iter(const char delim,", r"""requires delim != 0;
    requires is_str((char *)val);
    requires iter == \null || is_str((char *)iter);
    requires \valid(dir) && \valid(len) && \separated(dir, len);
    assigns *dir, *len;
    ensures *dir == (iter == \null ? val : (char *)iter);
    ensures \forall integer j; 0 <= j < *len ==> (*dir)[j] != delim && (*dir)[j] != 0;
    ensures \result == \null ==> (*dir)[*len] == 0;
    ensures \result != \null ==> (*dir)[*len] == delim && (char *)\result == *dir + *len + 1;"""),

"vim_env_iter_rev": ("const void *vim_env_iter_rev(const char delim,", r"""requires \exists integer n; str_len((char *)val, n)
      && (iter == \null || ((char *)val - 1 <= (char *)iter && (char *)iter <= (char *)val + n - 1));
    requires \valid(dir) && \valid(len) && \separated(dir, len);
    assigns *dir, *len;
    ensures \forall integer n; str_len((char *)val, n) ==> \let e = (iter == \null ? (char *)val + n - 1 : (char *)iter);
      \result == \null ==> *dir == val && *len == e - val + 1
        && \forall integer j; 0 <= j < *len ==> val[j] != delim;
    ensures \forall integer n; str_len((char *)val, n) ==> \let e = (iter == \null ? (char *)val + n - 1 : (char *)iter);
      \result != \null ==> val < *dir && *dir <= e + 1 && (*dir)[-1] == delim
        && (char *)\result == *dir - 2 && *len == e - *dir + 1
        && \forall integer j; 0 <= j < *len ==> (*dir)[j] != delim;"""),
}
PINS = {
"env_name_valid": "288e35ac47c945d7150e77fec21f67473c6bc4e5d21b1c56143c08583554dad5",
"vim_env_iter": "a77dc5f52ef24422649b18a24ab266c0eb9492788c7a6b93d78429b2ac2c51b7",
"vim_env_iter_rev": "0ecdd5f178f3fec1df3813ff470b1e770021b0f465c0f9135fc9efdf06fd2613",
}
