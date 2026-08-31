# Security Policy

- Never commit case briefs, API keys, credentials, or live competition outputs.
- Use a private deployment for non-public case material.
- Production requires `CASEFLOW_API_KEY` and database migrations.
- Rotate any credential accidentally written to logs or Git history.
- Report security issues privately to the repository owner.

The built-in API key is a deployment boundary for a single team, not a replacement
for enterprise SSO, tenant isolation, or a managed secrets platform.
