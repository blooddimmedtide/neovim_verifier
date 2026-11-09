# marktree.c `marktree_getp_aux` doc comment gives the wrong result range (doc only)

The comment says the result is "the position it should be inserted, which ranges from 0 to x->n
_inclusively_". The code returns -1 for an empty node and, without a match, the index of the last
key before `k` (range -1 .. x->n - 1). The callers (`marktree_putp_aux`, `marktree_move`, `marktree_itr_get_ext`, `marktree_itr_get_overlap`)
use the code's meaning (they insert at result + 1 and descend into `ptr[result + 1]`), so the code is
right and the comment is wrong. The WP contract states the code's meaning, proved for every sorted node.
No code fix needed; a doc fix could be sent upstream with the meta_has issue.
