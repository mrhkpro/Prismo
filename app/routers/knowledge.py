from datetime import datetime

from sqlalchemy import func
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..security import get_current_user
from ..services import llm_client, rag_store, text_split

router = APIRouter(prefix="/api/knowledge", tags=["دانشنامه"])


def _doc_out(doc: models.Document, chunk_count: int | None = None) -> schemas.DocumentOut:
    return schemas.DocumentOut(
        id=doc.id,
        title=doc.title,
        chunk_count=len(doc.chunks) if chunk_count is None else chunk_count,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


def _index_document(db: Session, user: models.User, doc: models.Document) -> None:
    """متن سند را تکه‌تکه، امبد و در فروشگاه برداری ذخیره می‌کند."""
    provider = llm_client.resolve_provider(user.settings)
    pieces = text_split.split_text(doc.content)
    if not pieces:
        return
    embeddings = llm_client.embed_texts(pieces, provider)
    rag_store.add_chunks(db, user.id, doc.id, pieces, embeddings)


@router.get("/documents", response_model=list[schemas.DocumentOut])
def list_documents(
    current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)
):
    rows = (
        db.query(models.Document, func.count(models.Chunk.id))
        .outerjoin(models.Chunk, models.Chunk.document_id == models.Document.id)
        .filter(models.Document.user_id == current_user.id)
        .group_by(models.Document.id)
        .order_by(models.Document.created_at.desc())
        .all()
    )
    return [_doc_out(doc, int(chunk_count)) for doc, chunk_count in rows]


@router.post("/documents", response_model=schemas.DocumentOut, status_code=201)
def create_document(
    payload: schemas.DocumentCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    doc = models.Document(user_id=current_user.id, title=payload.title, content=payload.content)
    db.add(doc)
    db.flush()

    _index_document(db, current_user, doc)

    db.commit()
    db.refresh(doc)
    return _doc_out(doc)


@router.get("/documents/{doc_id}", response_model=schemas.DocumentDetailOut)
def get_document(
    doc_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    doc = (
        db.query(models.Document)
        .filter(models.Document.id == doc_id, models.Document.user_id == current_user.id)
        .first()
    )
    if not doc:
        raise HTTPException(status_code=404, detail="سند یافت نشد.")
    return schemas.DocumentDetailOut(
        id=doc.id, title=doc.title, content=doc.content,
        chunk_count=len(doc.chunks), created_at=doc.created_at, updated_at=doc.updated_at,
    )


@router.put("/documents/{doc_id}", response_model=schemas.DocumentOut)
def update_document(
    doc_id: int,
    payload: schemas.DocumentUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    doc = (
        db.query(models.Document)
        .filter(models.Document.id == doc_id, models.Document.user_id == current_user.id)
        .first()
    )
    if not doc:
        raise HTTPException(status_code=404, detail="سند یافت نشد.")

    content_changed = False
    if payload.title is not None:
        doc.title = payload.title
    if payload.content is not None and payload.content != doc.content:
        doc.content = payload.content
        content_changed = True

    doc.updated_at = datetime.utcnow()

    if content_changed:
        # چون متن تغییر کرده، باید تکه‌ها و بردارهای قبلی را دور ریخته و دوباره بسازیم
        rag_store.delete_document_chunks(db, doc.id)
        db.flush()
        _index_document(db, current_user, doc)

    db.commit()
    db.refresh(doc)
    return _doc_out(doc)


@router.post("/documents/{doc_id}/reindex", response_model=schemas.DocumentOut)
def reindex_document(
    doc_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """ایندکس یک سند را بدون تغییر محتوای خام آن دوباره می‌سازد."""
    doc = (
        db.query(models.Document)
        .filter(models.Document.id == doc_id, models.Document.user_id == current_user.id)
        .first()
    )
    if not doc:
        raise HTTPException(status_code=404, detail="سند یافت نشد.")

    rag_store.delete_document_chunks(db, doc.id)
    db.flush()
    _index_document(db, current_user, doc)
    db.commit()
    db.refresh(doc)
    return _doc_out(doc)


@router.delete("/documents/{doc_id}", status_code=204)
def delete_document(
    doc_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    doc = (
        db.query(models.Document)
        .filter(models.Document.id == doc_id, models.Document.user_id == current_user.id)
        .first()
    )
    if not doc:
        raise HTTPException(status_code=404, detail="سند یافت نشد.")
    db.delete(doc)  # cascade باعث حذف chunk های مرتبط هم می‌شود
    db.commit()


@router.delete("/documents", status_code=204)
def clear_knowledge_base(
    current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)
):
    db.query(models.Document).filter(models.Document.user_id == current_user.id).delete()
    rag_store.delete_all_user_chunks(db, current_user.id)
    db.commit()
