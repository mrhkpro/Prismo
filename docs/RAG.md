# RAG Pipeline

## End-to-end flow

```text
User message
   │
   ├─► input validation
   │
   ├─► resolve provider + model settings
   │
   ├─► embedding(query)
   │
   ├─► cosine search over owner-scoped chunks
   │      ├─ similarity threshold
   │      └─ top-k limit
   │
   ├─► build bounded conversation history
   │
   ├─► assemble system prompt + retrieved context
   │
   └─► chat completion
          │
          └─► persist user/assistant turn + injection flag
```

Both the internal playground and the public widget use `services/rag_pipeline.py`, so retrieval and prompt assembly are shared.

## Ingestion

When a document is created or edited with content changes:

1. The owner is resolved from the authenticated user.
2. Existing chunks for that document are removed.
3. `text_split` creates overlapping text chunks using the project chunk size/overlap settings.
4. The selected embedding provider creates one vector per chunk.
5. Chunks are stored in `chunks` with `user_id`, `document_id`, text and JSON-encoded embedding.

A separate `POST /api/knowledge/documents/{id}/reindex` endpoint repeats the index build without changing the stored raw document content.

## Retrieval

`rag_store.search()` always scopes rows by `user_id`. Cosine similarity is calculated with NumPy. Results below `similarity_threshold` are excluded, then the highest remaining scores are limited to `top_k`.

Current defaults:

- `top_k`: 4
- `similarity_threshold`: 0.25
- chunk size: 700 characters
- chunk overlap: 80 characters

The dashboard exposes the similarity threshold so retrieval behavior can be tuned without changing code.

## Prompt construction

Retrieved text is wrapped in explicit context delimiters and described as retrieved, untrusted content rather than an instruction source. The user's system prompt remains the primary system instruction.

Conversation history is bounded to the latest 12 messages and a 12,000-character budget. This prevents an old conversation from growing the prompt without limit.

## Missing context

When no chunks meet the threshold, the context block says that no suitable knowledge entry was found. The model can still answer according to its configured system prompt; the default prompt instructs it not to invent a knowledge-base answer.

If the embedding request fails, the pipeline continues with an empty retrieval result and still attempts the chat completion. Provider/chat failures are surfaced through the centralized LLM error handling.

## Quality boundaries

This is an embedded educational/production-demo RAG implementation, not a distributed vector-search system. The vector store loads the owner's chunk vectors into memory for each search. This is intentionally simple and keeps the project free from a separate vector database service.

For larger datasets, the retrieval layer can be replaced behind the existing `rag_store` interface without changing the API contract.
