"""
Vector store for RAG.

Local development:
    SQLite + JSON + NumPy

Production:
    PostgreSQL/Supabase + pgvector
"""

import json
from typing import List, Tuple

import numpy as np
from sqlalchemy import insert
from sqlalchemy.orm import Session

from .. import config, models


# ============================================================
# ADD CHUNKS
# ============================================================

def add_chunks(
    db: Session,
    user_id: int,
    document_id: int,
    texts: List[str],
    embeddings: List[List[float]],
) -> List[models.Chunk]:
    """ثبت تکه‌ها؛ برای سازگاری، همان ORM objects قبلی را برمی‌گرداند."""
    rows = []
    for idx, (text, embedding) in enumerate(zip(texts, embeddings)):
        stored_embedding = embedding if config.IS_POSTGRES else json.dumps(embedding)
        row = models.Chunk(
            document_id=document_id,
            user_id=user_id,
            chunk_index=idx,
            text=text,
            embedding=stored_embedding,
        )
        db.add(row)
        rows.append(row)
    db.flush()
    return rows


def add_chunks_bulk(
    db: Session,
    user_id: int,
    document_id: int,
    texts: List[str],
    embeddings: List[List[float]],
    start_index: int = 0,
) -> int:
    """ثبت سریع batchها با یک INSERT executemany به‌جای ساخت ORM object برای هر chunk."""
    if not texts:
        return 0

    rows = []
    for offset, (text, embedding) in enumerate(zip(texts, embeddings)):
        stored_embedding = embedding if config.IS_POSTGRES else json.dumps(embedding)
        rows.append({
            "document_id": document_id,
            "user_id": user_id,
            "chunk_index": start_index + offset,
            "text": text,
            "embedding": stored_embedding,
        })

    db.execute(insert(models.Chunk), rows)
    return len(rows)


# ============================================================
# DELETE DOCUMENT CHUNKS
# ============================================================

def delete_document_chunks(
    db: Session,
    document_id: int,
) -> None:

    (
        db.query(models.Chunk)
        .filter(
            models.Chunk.document_id == document_id
        )
        .delete()
    )


# ============================================================
# DELETE USER CHUNKS
# ============================================================

def delete_all_user_chunks(
    db: Session,
    user_id: int,
) -> None:

    (
        db.query(models.Chunk)
        .filter(
            models.Chunk.user_id == user_id
        )
        .delete()
    )


# ============================================================
# SQLITE COSINE SIMILARITY
# ============================================================

def _cosine_similarity(
    a: np.ndarray,
    b: np.ndarray,
) -> np.ndarray:

    a_norm = (
        a
        / (
            np.linalg.norm(
                a,
                axis=1,
                keepdims=True,
            )
            + 1e-10
        )
    )

    b_norm = (
        b
        / (
            np.linalg.norm(b)
            + 1e-10
        )
    )

    return a_norm @ b_norm


# ============================================================
# SEARCH
# ============================================================

def search(
    db: Session,
    user_id: int,
    query_embedding: List[float],
    top_k: int = 4,
    similarity_threshold: float = 0.0,
) -> List[Tuple[models.Chunk, float]]:

    threshold = max(
        0.0,
        min(
            1.0,
            similarity_threshold,
        ),
    )

    # ========================================================
    # POSTGRESQL / SUPABASE PGVECTOR
    # ========================================================

    if config.IS_POSTGRES:

        distance = (
            models.Chunk.embedding.cosine_distance(
                query_embedding
            )
        )

        rows = (
            db.query(
                models.Chunk,
                distance.label("distance"),
            )
            .filter(
                models.Chunk.user_id == user_id
            )
            .order_by(
                distance.asc()
            )
            .limit(top_k)
            .all()
        )

        results = []

        for chunk, distance_value in rows:

            distance_float = float(
                distance_value
            )

            similarity = (
                1.0
                - distance_float
            )

            if similarity >= threshold:

                results.append(
                    (
                        chunk,
                        similarity,
                    )
                )

        return results

    # ========================================================
    # SQLITE / NUMPY FALLBACK
    # ========================================================

    chunks = (
        db.query(models.Chunk)
        .filter(
            models.Chunk.user_id == user_id
        )
        .all()
    )

    if not chunks:
        return []

    matrix = np.array(
        [
            json.loads(chunk.embedding)
            for chunk in chunks
        ],
        dtype="float32",
    )

    query_vec = np.array(
        query_embedding,
        dtype="float32",
    )

    scores = _cosine_similarity(
        matrix,
        query_vec,
    )

    eligible = np.flatnonzero(
        scores >= threshold
    )

    order = eligible[
        np.argsort(
            -scores[eligible]
        )
    ][:top_k]

    return [
        (
            chunks[index],
            float(scores[index]),
        )
        for index in order
    ]