# Security Policy

## Sandbox Environment Notice
PayPilot AI ACCESS is developed and operated strictly as a hackathon demonstration using the **PayPal Sandbox environment**.
- No real monetary transactions are ever processed.
- No real credit card or buyer credential data is handled or stored.
- Sandbox buyer logins are strictly throwaway test accounts with simulated funds.

## API Keys and Secret Management
- Real API credentials (such as Channel3 API keys, Gemini API keys, and PayPal Client Secrets) are loaded solely from environment variables on the server.
- No API keys or secrets may ever be committed to this repository, logged in system traces, or transmitted to the client frontend.
- Pre-commit scanning and static checks enforce that secret strings are blocked from git tracking.

## Reporting a Vulnerability or Secret Exposure
If you discover a security vulnerability or suspect an accidental credential disclosure:
1. Please do **not** open a public issue.
2. Immediately contact the maintainer directly at the project owner contact email (Prince Kumar / `princebuilds`).
3. Disclosed test credentials will be revoked and rotated immediately.
