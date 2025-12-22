# Algoritmeregister Integration

This module provides integration with the Dutch Algoritmeregister (Algorithm Register) for publishing algorithm information.

## Overview

The integration uses OAuth2 Resource Owner Password Credentials (ROPC) flow to authenticate users and publish algorithms to the Algoritmeregister API.

### Architecture

```
AMT Application
    ↓ (username/password)
Keycloak (alg-reg realm)
    ↓ (access token)
AMT Application
    ↓ (API call with token)
Algoritmeregister API
    ↓ (validates token & permissions)
Published Algorithm
```

## Configuration

### Environment Variables

Set these in your `.env` file or environment:

```bash
ALGORITMEREGISTER_API_URL=http://localhost:8000/aanleverapi/v1_0
ALGORITMEREGISTER_TOKEN_URL=http://keycloak.kind/realms/algreg/protocol/openid-connect/token
ALGORITMEREGISTER_CLIENT_ID=authentication-client
```

These are already configured in `amt/core/config.py` with local development defaults.

## Keycloak Setup (Local Development)

### 1. Create Realm

1. Access Keycloak Admin Console: `http://keycloak.kind/admin`
2. Click **Create realm**
3. Realm name: `algreg` (or `alg-reg`)
4. Click **Create**

### 2. Create Client

Navigate to **Clients** → **Create client**:

#### General Settings

- **Client type**: `OpenID Connect`
- **Client ID**: `authentication-client`
- Click **Next**

#### Capability Config

- **Client authentication**: `OFF` (public client)
- **Authorization**: `OFF`
- **Authentication flow**:
    - ☐ Standard flow (uncheck)
    - ☑️ **Direct access grants** (MUST be enabled for password grant)
    - ☐ Implicit flow (uncheck)
    - ☐ Service accounts roles (uncheck)
- Click **Next**

#### Login Settings

- **Root URL**: (leave empty)
- **Valid redirect URIs**: `*` (for local testing only!)
- **Web origins**: `*` (for local testing only!)
- Click **Save**

### 3. Create Test Users

Navigate to **Users** → **Create new user**:

#### User Details

- **Username**: `test@example.com`
- **Email**: `test@example.com`
- **Email verified**: `ON` ⚠️ **Important!**
- **Enabled**: `ON`
- Click **Create**

#### Set Password

1. Go to **Credentials** tab
2. Click **Set password**
3. **Password**: `testpassword` (or your choice)
4. **Temporary**: `OFF` ⚠️ **Important!**
5. Click **Save**

#### Remove Required Actions

1. Go to **Details** tab
2. **Required user actions**: Make sure the list is empty
3. If not, remove all actions
4. Click **Save**

### 4. Test Authentication

Test the token endpoint with curl:

```bash
curl -X POST http://keycloak.kind/realms/algreg/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=authentication-client" \
  -d "username=test@example.com" \
  -d "password=testpassword" \
  -d "grant_type=password" \
  -d "totp="
```

Expected response:

```json
{
    "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in": 300,
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_expires_in": 1800
}
```

## Usage

### Publishing an Algorithm

The `publish_algorithm()` function handles the complete flow:

```python
from amt.algoritmeregister.publisher import publish_algorithm
from amt.models.algorithm import Algorithm

# Publish algorithm
result = await publish_algorithm(
    algorithm=algorithm_instance,
    username="user@example.com",
    password="user_password",
    organisation_id="gm0244"  # CBS gemeente code
)

# Check result
if result["success"]:
    print(f"Published with LARS code: {result['lars_code']}")
else:
    print(f"Error: {result['error']}")
```

### Token Retrieval (Internal)

The authentication is handled automatically by `publish_algorithm()`, but you can also retrieve tokens directly:

```python
from amt.algoritmeregister.auth import get_access_token

# Get access token
token = await get_access_token(
    username="user@example.com",
    password="user_password"
)
```

## OAuth2 Flow Details

### Grant Type: Password (ROPC)

This implementation uses the **Resource Owner Password Credentials** flow:

1. **User provides credentials** to AMT application
2. **AMT exchanges credentials** for access token at Keycloak
3. **AMT uses token** to authenticate API requests to Algoritmeregister
4. **Algoritmeregister validates token** and extracts user permissions

### Token Request

```http
POST /realms/algreg/protocol/openid-connect/token
Content-Type: application/x-www-form-urlencoded

grant_type=password
&client_id=authentication-client
&username=user@example.com
&password=user_password
&totp=
```

### Token Response

The access token is a JWT containing:

- User identity (sub, email, preferred_username)
- Roles and permissions (realm_access, resource_access)
- Token metadata (iss, exp, iat)

The Algoritmeregister API validates this token and checks if the user has permission to publish to the specified organization.

## Security Considerations

### Production Setup

⚠️ **Important**: The local development setup uses relaxed security settings. For production:

1. **Use HTTPS** for all endpoints
2. **Restrict redirect URIs** to actual application URLs
3. **Enable email verification** for new users
4. **Configure proper CORS** settings
5. **Store credentials securely** (never in code)
6. **Use short token expiration** times
7. **Implement token refresh** logic

### Credential Storage

❌ **Never commit credentials to git**

```python
# Bad - hardcoded in code
username = "test@example.com"
password = "testpassword"

# Good - from user input or secure storage
username = request.form.get("username")
password = request.form.get("password")

# Or from encrypted environment/secret manager
username = get_secret("ALGORITMEREGISTER_USERNAME")
password = get_secret("ALGORITMEREGISTER_PASSWORD")
```

## API Endpoints

### Base URL

```
http://localhost:8000/aanleverapi/v1_0
```

### Key Endpoints

- `POST /organizations/{organisation_id}/algorithms` - Create new algorithm
- `PUT /organizations/{organisation_id}/algorithms/{algorithm_id}` - Update algorithm
- `PUT /organizations/{organisation_id}/algorithms/{algorithm_id}/release` - Release for publication
- `DELETE /organizations/{organisation_id}/published-algorithms/{algorithm_id}/retract` - Retract published algorithm

See [OpenAPI specification](openapi/v1_0/specs/openapi.json) for complete API documentation.

## Organization IDs

Organization IDs use CBS gemeentecodes (municipality codes):

- Format: `gm` + 4-digit code
- Example: `gm0244` (Maastricht)
- Find codes: https://www.cbs.nl/nl-nl/onze-diensten/methoden/classificaties/overig/gemeentelijke-indelingen-per-jaar

## Troubleshooting

### "invalid_grant: Account is not fully set up"

**Cause**: User has required actions pending in Keycloak

**Solution**:

1. Go to Keycloak Admin → Users → {user}
2. Details tab → Remove all "Required user actions"
3. Ensure "Email verified" is ON
4. Save changes

### "invalid_grant: Invalid user credentials"

**Cause**: Wrong username or password

**Solution**:

1. Verify credentials are correct
2. Check user is enabled in Keycloak
3. Try resetting password in Credentials tab

### "ALGORITMEREGISTER_TOKEN_URL is not configured"

**Cause**: Missing configuration

**Solution**: Set environment variable or update `amt/core/config.py`:

```python
ALGORITMEREGISTER_TOKEN_URL = "http://keycloak.kind/realms/algreg/protocol/openid-connect/token"
```

### SSL Certificate Errors

**Cause**: Self-signed certificates in local development

**Solution**: For local testing only, you can disable SSL verification:

```python
async with httpx.AsyncClient(verify=False) as client:
    ...
```

⚠️ Never disable SSL verification in production!

## Files

- `auth.py` - OAuth2 token retrieval
- `publisher.py` - Algorithm publishing logic
- `mapper.py` - Data model mapping
- `openapi/v1_0/` - Generated OpenAPI client
- `openapi/v1_0/specs/openapi.json` - API specification

## Testing

Run tests:

```bash
python -m pytest tests/algoritmeregister/ -v
```

All tests use mocked HTTP clients and don't require a running Keycloak instance.

## References

- [Algoritmeregister Documentation](https://algoritmes.overheid.nl)
- [Keycloak Documentation](https://www.keycloak.org/documentation)
- [OAuth 2.0 Resource Owner Password Credentials](https://datatracker.ietf.org/doc/html/rfc6749#section-4.3)
- [OpenID Connect](https://openid.net/connect/)
