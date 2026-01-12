from .textify import normalize_query

def retrieve_service(
    *,
    user_query: str,
    top_k: int,
    level: str,
    subject: str,
    diff_min: int,
    diff_max: int,
    allow_sensitive: bool,
    index,
    docs,
    embed_query,
    min_score: float = 0.55,
    candidate_k: int = 80,
):
    q = normalize_query(user_query)
    q_vec = embed_query(q)
    D, I = index.search(q_vec, candidate_k)

    out = []
    for score, idx in zip(D[0], I[0]):
        meta = docs[int(idx)]["metadata"]

        if meta["level"] != level:
            continue
        if meta["subject"] != subject:
            continue
        if not (diff_min <= meta["difficulty"] <= diff_max):
            continue
        if (not allow_sensitive) and meta["sensitive"]:
            continue
        if float(score) < min_score:
            continue

        out.append({"score": float(score), "metadata": meta})
        if len(out) >= top_k:
            break

    return out
