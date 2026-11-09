"""Append status.tsv rows for typval functions in proved.tsv (status candidate). Idempotent.
Usage: python3 -I typval/status_rows.py  (run from libraries/neovim)"""
rows = [l.rstrip("\n").split("\t", 1) for l in open("typval/proved.tsv") if l.strip() and not l.startswith("#")]
have = {tuple(l.split("\t")[:2]) for l in open("status.tsv")}
hdr = {"tv_list_len", "tv_list_uidx", "tv_list_locked", "tv_blob_len", "tv_blob_get", "tv_blob_set", "tv_blob_set_ret"}
fixed = {"tv_get_lnum_buf"}
with open("status.tsv", "a") as f:
    for name, ev in rows:
        path = "src/nvim/eval/typval.h" if name in hdr else "src/nvim/eval/typval.c"
        if (path, name) in have:
            continue
        st = "fixed-candidate" if name in fixed else "candidate"
        f.write(f"{path}\t{name}\t{st}\ttypval/{ev}\tsee typval/CLAIM.md; no adversarial review yet; waiting on owner spec sign-off\n")
