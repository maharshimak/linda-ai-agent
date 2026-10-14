# Linda cinematic video source

A local development backend and frontend source for an AI-assisted cinematic video
workflow. The implemented backend provides account/login routes, authenticated
single-video job creation/status and owner-checked generated-media access. Engine
modules contain scripting, audio, asset and editing code; real rendering has not
been verified in this preparation run.

Webhook, Zapier and TrendJack prototypes and the unauthenticated legacy server are
excluded. Bulk dispatch is disabled until persistent quota reservation exists.
Browser playback still needs authenticated fetch/blob integration. This source
publication does not claim deployment readiness or a working complete video pipeline.

## Local backend setup

Create an isolated Python environment and install `requirements-backend.txt`.
Provide a locally generated JWT_SECRET_KEY of at least 32 characters and a locally
supplied OPENAI_API_KEY when generation is deliberately requested. No secret is
included. Optional initial ADMIN_BOOTSTRAP_EMAIL and ADMIN_BOOTSTRAP_PASSWORD must
both be supplied explicitly; the password must have at least 12 characters.
Public signup defaults off. Start `uvicorn backend.main:app --host 127.0.0.1`.
Keep this prototype on loopback; it has no production multi-worker queue/quota design.
For rendering, separately review/install `requirements.txt` and obtain licensed
voice, font and music assets. No database, media or voice binary is included.

## Verification and limits

Ten offline security/ownership checks passed with synthetic fixtures and HTTP
transport disabled. They verify route boundaries and JWT handling, not complete
startup, live databases, rendering, providers or frontend builds. See
`PUBLICATION_NOTES.md` and the tests for preserved development limitations.

Copyright 2026 maharshimak. All rights reserved. Third-party dependency licenses
remain applicable; no broad reuse permission is implied by public availability.
