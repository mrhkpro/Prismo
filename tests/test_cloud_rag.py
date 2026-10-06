from types import SimpleNamespace
import unittest
from unittest.mock import patch

from pgvector.sqlalchemy import VECTOR
from sqlalchemy import column
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Query, Session

from app import config, models
from app.exceptions import AppError
from app.services import llm_client, rag_pipeline, rag_store


class CloudEmbeddingTests(unittest.TestCase):
    def setUp(self):
        self.provider = llm_client.ProviderConfig(
            base_url="https://example.invalid/v1",
            api_key="test-key",
            chat_model="test-chat",
            embedding_model="test-embedding",
            is_default=True,
        )

    def embed(self, response_items, texts):
        client = SimpleNamespace(
            embeddings=SimpleNamespace(
                create=lambda **kwargs: SimpleNamespace(data=response_items)
            )
        )
        with patch.object(llm_client, "_client", return_value=client), patch.object(config, "EMBEDDING_DIMENSIONS", 2):
            return llm_client.embed_texts(texts, self.provider)

    def test_embeddings_follow_input_order(self):
        items = [
            SimpleNamespace(index=1, embedding=[0.0, 1.0]),
            SimpleNamespace(index=0, embedding=[1.0, 0.0]),
        ]
        self.assertEqual(self.embed(items, ["first", "second"]), [[1.0, 0.0], [0.0, 1.0]])

    def test_incomplete_response_is_rejected(self):
        items = [SimpleNamespace(index=0, embedding=[1.0, 0.0])]
        with self.assertRaises(llm_client.LLMError):
            self.embed(items, ["first", "second"])

    def test_duplicate_response_indices_are_rejected(self):
        items = [SimpleNamespace(index=0, embedding=[1.0, 0.0])] * 2
        with self.assertRaises(llm_client.LLMError):
            self.embed(items, ["first", "second"])

    def test_wrong_dimensions_are_rejected(self):
        items = [SimpleNamespace(index=0, embedding=[1.0])]
        with self.assertRaisesRegex(llm_client.LLMError, "Received=1, Expected=2"):
            self.embed(items, ["first"])

    def test_provider_errors_have_a_controlled_api_status(self):
        self.assertTrue(issubclass(llm_client.LLMError, AppError))
        self.assertEqual(llm_client.LLMError.status_code, 502)


class CloudRetrievalTests(unittest.TestCase):
    def test_pgvector_query_filters_owner_and_orders_by_cosine_distance(self):
        captured = {}
        strong_chunk = SimpleNamespace(text="strong")
        weak_chunk = SimpleNamespace(text="weak")

        def query_results(query):
            captured["statement"] = query.statement.compile(dialect=postgresql.dialect())
            return [(strong_chunk, 0.1), (weak_chunk, 0.9)]

        with Session() as database:
            with patch.object(config, "IS_POSTGRES", True), patch.object(
                models.Chunk, "embedding", column("embedding", VECTOR(2))
            ), patch.object(Query, "all", autospec=True, side_effect=query_results):
                matches = rag_store.search(database, 42, [1.0, 0.0], top_k=2, similarity_threshold=0.5)

        statement = str(captured["statement"])
        self.assertIn("WHERE chunks.user_id =", statement)
        self.assertIn("<=>", statement)
        self.assertIn("ORDER BY", statement)
        self.assertIn("LIMIT", statement)
        self.assertIn(42, captured["statement"].params.values())
        self.assertEqual(len(matches), 1)
        self.assertIs(matches[0][0], strong_chunk)
        self.assertAlmostEqual(matches[0][1], 0.9)


class CloudRAGPipelineTests(unittest.TestCase):
    def setUp(self):
        self.owner = SimpleNamespace(
            id=42,
            settings=SimpleNamespace(chat_model="test-chat", top_k=4, similarity_threshold=0.25, system_prompt="Only use context", temperature=0.7),
        )
        self.session = SimpleNamespace(messages=[])

    def test_embedding_failure_does_not_turn_into_ungrounded_chat(self):
        with patch.object(llm_client, "resolve_provider"), patch.object(
            llm_client, "embed_text", side_effect=llm_client.LLMError("Embedding unavailable")
        ), patch.object(llm_client, "chat_completion") as chat:
            with self.assertRaises(llm_client.LLMError):
                rag_pipeline.run_rag_chat(None, self.owner, self.session, "Question")
        chat.assert_not_called()

    def test_empty_retrieval_returns_a_fixed_no_information_reply(self):
        with patch.object(llm_client, "resolve_provider"), patch.object(
            llm_client, "embed_text", return_value=[1.0, 0.0]
        ), patch.object(rag_store, "search", return_value=[]), patch.object(llm_client, "chat_completion") as chat:
            reply, sources = rag_pipeline.run_rag_chat(None, self.owner, self.session, "Question")
        self.assertEqual(sources, [])
        self.assertIn("اطلاعاتی", reply)
        chat.assert_not_called()

    def test_retrieved_context_reaches_the_chat_model(self):
        matches = [(SimpleNamespace(text="Known opening hours"), 0.9)]
        with patch.object(llm_client, "resolve_provider"), patch.object(
            llm_client, "embed_text", return_value=[1.0, 0.0]
        ), patch.object(rag_store, "search", return_value=matches) as search, patch.object(
            llm_client, "chat_completion", return_value="Answer"
        ) as chat:
            reply, sources = rag_pipeline.run_rag_chat(None, self.owner, self.session, "Question")
        self.assertEqual(reply, "Answer")
        self.assertEqual(sources, matches)
        self.assertEqual(search.call_args.args[1], self.owner.id)
        self.assertIn("Known opening hours", chat.call_args.args[0][0]["content"])


if __name__ == "__main__":
    unittest.main()
