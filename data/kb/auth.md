# Authentication & SSO Guide
## Overview
Our platform supports SAML 2.0, OAuth 2.0, and Okta/Azure AD integration.

## Troubleshooting Common Authentication Issues
- **Error 401 Unauthorized / Token Expired**: JWT tokens expire after 3600 seconds (1 hour). Clients must request a new token using the `/oauth/token` refresh endpoint.
- **SSO Lockout**: If SSO SAML assertion fails due to clock skew, verify your IdP NTP synchronization. If an admin is locked out, use the emergency recovery link sent to the primary security contact email.
- **MFA Reset**: Multi-Factor Authentication reset requires Account Admin confirmation or tier-2 security ticket escalation.