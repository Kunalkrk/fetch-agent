"""Fetch agent package.

Ensures SSL_CERT_FILE points at certifi's CA bundle before any network
client (aiohttp/Slack, googleapiclient, anthropic) is constructed. Without
this, some Python installs (notably python.org builds on macOS) fail
outbound HTTPS calls with CERTIFICATE_VERIFY_FAILED because they don't
pick up a system CA bundle by default.
"""

import os

import certifi

os.environ.setdefault("SSL_CERT_FILE", certifi.where())
