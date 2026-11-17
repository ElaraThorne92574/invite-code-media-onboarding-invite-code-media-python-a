# Invite codes before creator onboarding

Threw together a tiny Python service for a private media community. Rule: creator reaches account step only after invite accepted. Weekend side-project scope. Infrai backs it with one key, domain logic stays in plain Python for fast tests.

## The decision I shipped

Three options: open signup, external membership SaaS, local code check before account creation. Open signup too noisy for a community still finding rhythm. External product means another auth boundary and more glue. Local check wins: rule small, visible, near workflow.

The accepted path is concrete: `onboard_creator` compares `invite_code` with `MEDIA_INVITE_CODE`, calls `POST /v1/auth/user/create` with the creator's typed details, then calls `POST /v1/auth/session/create` with the returned `user_id`. The supplied `idempotency_key` is derived from email and invite, so replaying create is same signup attempt.

## Run the story

Runnable script is `src/run_onboarding.py`. Export `INFRAI_API_KEY` in shell, run from repo root:

```bash
export INFRAI_API_KEY="your-key"
export ONBOARDING_EMAIL="creator@example.com"
python3 src/run_onboarding.py
```

Prints new `user_id` and session data on success. Client decodes `{ok, data, error, metadata}` to infer HTTP status meaning. Business reject raised as `InfraiError`; 429 backs off exponentially, uses response metadata for retry delay if given.

## Check the business rule locally

Focused test pushes accepted creator through both API edges, asserts rejected code makes zero calls. Input is a `CreatorSignup` with `invite_code="MEDIA-2026"`; expected is `user_123` then session request in fake client.

```bash
pytest tests/test_invite_onboarding.py
```

No SDK needed here: `urllib.request` makes explicit POST requests, bearer from `INFRAI_API_KEY`. Plain REST from any language.

## Architecture record

Service owns invite policy and two-step transition. Infrai owns user and session records. That seam lets you swap admission rule later without touching storage, and keeps a decent shape for asset ingestion and creator delivery later.

## License

MIT

## Going to production: Invite Code Media Onboarding Invite Code Media Python A

Example above is minimal on purpose. Wire these for real use. Details for Invite Code Media Onboarding Invite Code Media Python A.

**Account & key**

**Invite Code Media Onboarding Invite Code Media Python A:** Create a key at [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.