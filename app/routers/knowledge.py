from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from sqlalchemy import func
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from .. import config, models, schemas
from ..database import get_db
from ..security import get_current_user
from ..services import llm_client, rag_store, text_split, streaming, user_settings_compat

router = APIRouter(prefix="/api/knowledge", tags=["دانشنامه"])


def _doc_out(doc: models.Document, chunk_count: int | None = None) -> schemas.DocumentOut:
    return schemas.DocumentOut(
        id=doc.id,
        title=doc.title,
        chunk_count=len(doc.chunks) if chunk_count is None else chunk_count,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


def _embed_batch(pieces: list[str], start: int, provider: llm_client.ProviderConfig, batch_size: int):
    batch = pieces[start:start + batch_size]
    return start, llm_client.embed_texts(batch, provider)


def _embed_chunks_fast(pieces: list[str], provider: llm_client.ProviderConfig):
    """Embedding سریع‌تر با batch بزرگ‌تر و چند درخواست هم‌زمان."""
    if not pieces:
        return []

    batch_size = config.EMBEDDING_BATCH_SIZE
    concurrency = min(config.EMBEDDING_CONCURRENCY, max(1, (len(pieces) + batch_size - 1) // batch_size))
    results = [None] * len(pieces)

    if concurrency == 1:
        return llm_client.embed_texts(pieces, provider)

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = [
            pool.submit(_embed_batch, pieces, start, provider, batch_size)
            for start in range(0, len(pieces), batch_size)
        ]
        for future in as_completed(futures):
            start, embeddings = future.result()
            results[start:start + len(embeddings)] = embeddings

    return results


def _index_document(db: Session, user: models.User, doc: models.Document) -> None:
    """ایندکس سریع سند با embedding هم‌زمان و ثبت bulk در دیتابیس."""
    provider = llm_client.resolve_provider(user_settings_compat.get(db, user.id))
    pieces = text_split.split_text(doc.content)
    if not pieces:
        return
    embeddings = _embed_chunks_fast(pieces, provider)
    rag_store.add_chunks_bulk(db, user.id, doc.id, pieces, embeddings)


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


@router.post("/documents/stream")
def create_document_stream(
    payload: schemas.DocumentCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """افزودن سند با درصد واقعیِ chunkهای کامل‌شده و بدون مرحله‌بندی مصنوعی."""
    doc = models.Document(user_id=current_user.id, title=payload.title, content=payload.content)
    db.add(doc)
    db.commit()
    doc_id = doc.id
    user_id = current_user.id
    bind = db.get_bind()

    def event_stream():
        try:
            with Session(bind=bind, autoflush=False) as work_db:
                user = work_db.get(models.User, user_id)
                doc = work_db.get(models.Document, doc_id)
                if not user or not doc:
                    yield streaming.sse("error", {"message": "سند یافت نشد."})
                    return

                pieces = text_split.split_text(doc.content)
                if not pieces:
                    raise ValueError("محتوای سند خالی است.")

                total = len(pieces)
                provider = llm_client.resolve_provider(user_settings_compat.get(work_db, user.id))
                yield streaming.sse(
                    "meta",
                    {
                        "progress": 0,
                        "message": f"در حال آماده‌سازی {total} بخش از سند…",
                        "completed": 0,
                        "total": total,
                    },
                )

                batch_size = config.EMBEDDING_BATCH_SIZE
                concurrency = min(
                    config.EMBEDDING_CONCURRENCY,
                    max(1, (total + batch_size - 1) // batch_size),
                )
                completed = 0

                if concurrency == 1:
                    batches = [
                        _embed_batch(pieces, start, provider, batch_size)
                        for start in range(0, total, batch_size)
                    ]
                    for start, embeddings in batches:
                        rag_store.add_chunks_bulk(work_db, user.id, doc.id, pieces[start:start + len(embeddings)], embeddings, start_index=start)
                        completed += len(embeddings)
                        percent = min(99, int((completed / total) * 100))
                        yield streaming.sse(
                            "meta",
                            {
                                "progress": percent,
                                "message": _index_progress_message(percent, completed, total),
                                "completed": completed,
                                "total": total,
                            },
                        )
                else:
                    with ThreadPoolExecutor(max_workers=concurrency) as pool:
                        futures = {
                            pool.submit(_embed_batch, pieces, start, provider, batch_size): start
                            for start in range(0, total, batch_size)
                        }
                        for future in as_completed(futures):
                            start = futures[future]
                            batch_start, embeddings = future.result()
                            if batch_start != start:
                                start = batch_start
                            batch_texts = pieces[start:start + len(embeddings)]
                            rag_store.add_chunks_bulk(
                                work_db,
                                user.id,
                                doc.id,
                                batch_texts,
                                embeddings,
                                start_index=start,
                            )
                            completed += len(embeddings)
                            percent = min(99, int((completed / total) * 100))
                            yield streaming.sse(
                                "meta",
                                {
                                    "progress": percent,
                                    "message": _index_progress_message(percent, completed, total),
                                    "completed": completed,
                                    "total": total,
                                },
                            )

                # تا قبل از commit درصد 100 نشان داده نمی‌شود؛ بنابراین عدد همیشه
                # بازتاب‌دهنده‌ی بخش‌هایی است که واقعاً وارد transaction شده‌اند.
                work_db.commit()
                yield streaming.sse(
                    "meta",
                    {
                        "progress": 100,
                        "message": "همه بخش‌های سند با موفقیت ذخیره شد؛ دانشنامه آماده است ✓",
                        "completed": total,
                        "total": total,
                    },
                )
                yield streaming.sse("done", {})
        except llm_client.LLMError as exc:
            with Session(bind=bind, autoflush=False) as cleanup_db:
                cleanup_db.query(models.Document).filter(models.Document.id == doc_id).delete()
                cleanup_db.commit()
            yield streaming.sse("error", {"message": str(exc)})
        except Exception as exc:  # noqa: BLE001
            with Session(bind=bind, autoflush=False) as cleanup_db:
                cleanup_db.query(models.Document).filter(models.Document.id == doc_id).delete()
                cleanup_db.commit()
            yield streaming.sse("error", {"message": str(exc) or "ایندکس سند ناموفق بود."})

    return StreamingResponse(event_stream(), media_type="text/event-stream", headers=streaming.SSE_HEADERS)


def _index_progress_message(percent: int, completed: int, total: int) -> str:
    """پیام کوتاه بر اساس درصد واقعی؛ هیچ stage مصنوعی در UI ندارد."""
    if percent <= 0:
        text = "در حال آماده‌سازی سند و ساخت اولین بخش‌ها…"
    elif percent < 15:
        text = "اولین بخش‌های سند آماده می‌شوند؛ داریم جست‌وجوی معنایی را می‌سازیم…"
    elif percent < 30:
        text = "داریم محتوای سند را به وکتورهای قابل جست‌وجو تبدیل و ذخیره می‌کنیم…"
    elif percent < 45:
        text = "بخش‌های سند یکی‌یکی آماده‌اند؛ دانشنامه دارد سریع پر می‌شود…"
    elif percent < 60:
        text = "تقریباً نیمه‌ی مسیر را رد کرده‌ایم؛ اطلاعات آماده‌ی استفاده در چت است…"
    elif percent < 75:
        text = "بیشتر مسیر انجام شده؛ پاسخ‌های آینده می‌توانند از این اطلاعات استفاده کنند…"
    elif percent < 90:
        text = "خیلی خوب پیش رفتیم؛ فقط بخش‌های باقی‌مانده‌ی سند در حال پردازش‌اند…"
    elif percent < 98:
        text = "تقریباً تمام شد؛ داریم آخرین بخش‌های سند را ثبت می‌کنیم…"
    elif percent < 100:
        text = "آخرین بخش‌ها آماده شدند؛ یک لحظه برای ثبت نهایی…"
    else:
        text = "همه بخش‌های سند با موفقیت آماده شد ✓"
    return f"{text}  ·  {completed} از {total} بخش"


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
    # اول تکه‌ها (فرزند) و بعد اسناد (والد) حذف می‌شوند تا اگر دیتابیس کلید خارجی را سخت‌گیرانه
    # بررسی کند یا ON DELETE CASCADE نداشته باشد، پاک‌سازی کل دانشنامه شکست نخورد.
    rag_store.delete_all_user_chunks(db, current_user.id)
    db.query(models.Document).filter(models.Document.user_id == current_user.id).delete()
    db.commit()
