# GPT Action setup

Deploy the API to a public HTTPS URL first, then set these environment variables on the host:

```bash
APP_ENV=production
PUBLIC_BASE_URL=https://your-api.example.com
ACTION_API_KEY=<new random secret>
SEC_USER_AGENT=NoomNugaom/0.1 contact@example.com
```

In the GPT editor, create a new Action and either:

1. import `https://your-api.example.com/openapi.json`, or
2. paste `docs/gpt-action.openapi.yaml` after replacing its server URL.

Set authentication to **API Key**, use custom header `X-API-Key`, and paste the same `ACTION_API_KEY` value. Do not expose this value in GPT instructions or frontend code. Test all three operations in Preview before sharing the GPT.

Suggested GPT instruction:

> For every stock analysis, call `getStockChatContext` first. Cite its source and timestamp, identify delayed/end-of-day data, and never invent market or financial figures. Treat results as educational, not investment advice.

For public sharing, add a privacy-policy URL before publishing the GPT.
