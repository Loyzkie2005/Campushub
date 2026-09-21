"""
Content-based product recommendations using scikit-learn TF-IDF + cosine similarity.
Uses user interaction history when available; falls back to catalog-wide similarity.
"""

from __future__ import annotations

from collections import Counter

from django.db.models import Count

from api.models import Product, ProductInteraction


def _product_text(product: Product) -> str:
    return " ".join(
        filter(
            None,
            [
                product.name,
                product.category,
                product.description,
            ],
        )
    ).lower()


def _content_similarity_matrix(products: list[Product]):
    """Build TF-IDF cosine similarity matrix for approved products."""
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
    except ImportError:
        return None, None

    if len(products) < 2:
        return None, None

    corpus = [_product_text(p) for p in products]
    vectorizer = TfidfVectorizer(stop_words="english", min_df=1)
    matrix = vectorizer.fit_transform(corpus)
    similarity = cosine_similarity(matrix)
    return similarity, products


def get_recommended_products(
    *,
    user_id: int | None = None,
    limit: int = 8,
    seed_product_id: int | None = None,
) -> list[Product]:
    """
    Return ML-ranked product recommendations.
    - With user history: similar to products the user viewed/clicked.
    - With seed_product_id: similar to that product (detail-page recommendations).
    - Otherwise: diverse popular items from interaction counts.
    """
    approved = list(
        Product.objects.filter(
            approval_status=Product.STATUS_APPROVED,
            is_archived=False,
        ).select_related("seller")
    )
    if not approved:
        return []

    product_by_id = {p.id: p for p in approved}
    similarity, ordered = _content_similarity_matrix(approved)

    # Seed from explicit product (e.g. product detail screen)
    if seed_product_id and seed_product_id in product_by_id:
        return _similar_from_seed(
            seed_product_id,
            product_by_id,
            similarity,
            ordered,
            limit,
        )

    # Seed from user interaction history
    if user_id:
        history_ids = list(
            ProductInteraction.objects.filter(user_id=user_id)
            .values("product_id")
            .annotate(c=Count("id"))
            .order_by("-c")
            .values_list("product_id", flat=True)[:5]
        )
        if history_ids:
            scores: Counter[int] = Counter()
            for pid in history_ids:
                if pid not in product_by_id:
                    continue
                for rec_id, score in _similarity_scores(
                    pid, product_by_id, similarity, ordered
                ):
                    if rec_id not in history_ids:
                        scores[rec_id] += score
            if scores:
                ranked = [product_by_id[i] for i, _ in scores.most_common(limit)]
                return ranked

    # Fallback: products with most interactions, then TF-IDF diversity
    popular_ids = list(
        ProductInteraction.objects.values("product_id")
        .annotate(c=Count("id"))
        .order_by("-c")
        .values_list("product_id", flat=True)[:limit]
    )
    popular = [product_by_id[i] for i in popular_ids if i in product_by_id]
    if len(popular) >= limit:
        return popular[:limit]

    # Fill remaining slots with highest stock / newest approved products
    seen = {p.id for p in popular}
    for product in approved:
        if product.id in seen:
            continue
        popular.append(product)
        seen.add(product.id)
        if len(popular) >= limit:
            break
    return popular[:limit]


def _similarity_scores(seed_id, product_by_id, similarity, ordered):
    if similarity is None or ordered is None:
        return []
    try:
        idx = next(i for i, p in enumerate(ordered) if p.id == seed_id)
    except StopIteration:
        return []
    row = similarity[idx]
    scored = []
    for i, score in enumerate(row):
        pid = ordered[i].id
        if pid != seed_id and pid in product_by_id and score > 0:
            scored.append((pid, float(score)))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored


def _similar_from_seed(seed_id, product_by_id, similarity, ordered, limit):
    scored = _similarity_scores(seed_id, product_by_id, similarity, ordered)
    result = []
    for pid, _ in scored:
        result.append(product_by_id[pid])
        if len(result) >= limit:
            return result
    # Not enough similar items — append catalog
    seen = {seed_id, *(p.id for p in result)}
    for product in ordered or []:
        if product.id not in seen:
            result.append(product)
            seen.add(product.id)
        if len(result) >= limit:
            break
    return result[:limit]
