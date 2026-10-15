# Prismo v2.8.13

## Conversation memory fast path
- Before provider selection or RAG calls, Prismo checks the current conversation for a previously answered version of the same question.
- Recall works for test-lab chats and public-widget chats because both use the shared RAG pipeline.
- Recall is limited to the same conversation, excludes flagged questions, and inspects a bounded recent history.
- High-confidence Persian/English rephrasing variations and short fact follow-ups such as “اسمش چی بود؟” are recognized without an embedding or LLM call; different attributes about the same entity are not conflated.
- No frontend, model settings, saved models, authentication, or database schema was changed.

