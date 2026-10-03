# v2.2.3 - Hosted provider relay

- Add optional OpenAI-compatible relay support for the default AI provider.
- Keep direct provider routing as the fallback when no relay is configured.
- Route both embeddings and chat through the same relay configuration.
- Add relay service with Dockerfile and environment template.
- Add actionable guidance for hosted connection timeouts.
- Add contract tests for relay selection and direct fallback.
