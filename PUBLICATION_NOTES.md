# Development source boundaries

The backend uses authenticated generation/job routes and ownership-checked media.
Webhook/Zapier/TrendJack prototypes are not mounted; no configuration flag enables
their unsafe routes. Legacy unauthenticated server.py is excluded from publication.
Bulk paid dispatch returns 503 until persistent quota reservation is implemented.
Bulk inspection/cancellation requires authentication and ownership.

Generation requires provider credentials supplied locally and separately licensed
media/voice/font assets. No secret, database, binary voice engine or asset is shipped.
No end-to-end video-generation capability has been verified. Direct HTML video
elements must be replaced with an authenticated fetch/blob client before UI playback
works with the protected media route. Prototype provider modules and engine variants
remain development source, not claims of working integrated functionality.

The earlier bulk-result allegation was corrected: generate_video returns Path and
the caller constructs its own result dict. No Path.get bug exists in current source.

Public signup is disabled by default. Explicit local administrator bootstrap is the
supported initial-account flow. Main HTTP bodies count actual received bytes and are
bounded to 32 KB; trusted hosts are loopback. Single-video routes use authentication
and persist generation rows counted against daily quotas; administrator accounts
explicitly bypass quotas as the operator. This is a loopback development prototype,
not a public hosting configuration. Multi-worker atomic quota enforcement, production
job queues, authenticated browser playback and rendering integration remain future
work. Backend-only dependencies can be installed separately using requirements-backend.txt.
