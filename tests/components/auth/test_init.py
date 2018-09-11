"""Integration tests for the auth component."""
from datetime import timedelta
from unittest.mock import patch

from homeassistant import const
from homeassistant.auth import auth_manager_from_config
from homeassistant.auth.models import Credentials
from homeassistant.components.auth import RESULT_TYPE_USER
from homeassistant.setup import async_setup_component
from homeassistant.util.dt import utcnow
from homeassistant.components import auth

from . import async_setup_auth

from tests.common import CLIENT_ID, CLIENT_REDIRECT_URI, MockUser, \
    ensure_auth_manager_loaded


async def test_login_new_user_and_trying_refresh_token(hass, aiohttp_client):
    """Test logging in with new user and refreshing tokens."""
    client = await async_setup_auth(hass, aiohttp_client, setup_api=True)
    resp = await client.post('/auth/login_flow', json={
        'client_id': CLIENT_ID,
        'handler': ['insecure_example', None],
        'redirect_uri': CLIENT_REDIRECT_URI,
    })
    assert resp.status == 200
    step = await resp.json()

    resp = await client.post(
        '/auth/login_flow/{}'.format(step['flow_id']), json={
            'client_id': CLIENT_ID,
            'username': 'test-user',
            'password': 'test-pass',
        })

    assert resp.status == 200
    step = await resp.json()
    code = step['result']

    # Exchange code for tokens
    resp = await client.post('/auth/token', data={
        'client_id': CLIENT_ID,
        'grant_type': 'authorization_code',
        'code': code
    })

    assert resp.status == 200
    tokens = await resp.json()

    assert (
        await hass.auth.async_validate_access_token(tokens['access_token'])
        is not None
    )

    # Use refresh token to get more tokens.
    resp = await client.post('/auth/token', data={
            'client_id': CLIENT_ID,
            'grant_type': 'refresh_token',
            'refresh_token': tokens['refresh_token']
        })

    assert resp.status == 200
    tokens = await resp.json()
    assert 'refresh_token' not in tokens
    assert (
        await hass.auth.async_validate_access_token(tokens['access_token'])
        is not None
    )

    # Test using access token to hit API.
    resp = await client.get('/api/')
    assert resp.status == 401

    resp = await client.get('/api/', headers={
        'authorization': 'Bearer {}'.format(tokens['access_token'])
    })
    assert resp.status == 200


def test_auth_code_store_expiration():
    """Test that the auth code store will not return expired tokens."""
    store, retrieve = auth._create_auth_code_store()
    client_id = 'bla'
    user = MockUser(id='mock_user')
    now = utcnow()

    with patch('homeassistant.util.dt.utcnow', return_value=now):
        code = store(client_id, user)

    with patch('homeassistant.util.dt.utcnow',
               return_value=now + timedelta(minutes=10)):
        assert retrieve(client_id, RESULT_TYPE_USER, code) is None

    with patch('homeassistant.util.dt.utcnow', return_value=now):
        code = store(client_id, user)

    with patch('homeassistant.util.dt.utcnow',
               return_value=now + timedelta(minutes=9, seconds=59)):
        assert retrieve(client_id, RESULT_TYPE_USER, code) == user


async def test_ws_current_user(hass, hass_ws_client, hass_access_token):
    """Test the current user command with homeassistant creds."""
    assert await async_setup_component(hass, 'auth', {
        'http': {
            'api_password': 'bla'
        }
    })

    refresh_token = await hass.auth.async_validate_access_token(
        hass_access_token)
    user = refresh_token.user
    credential = Credentials(auth_provider_type='homeassistant',
                             auth_provider_id=None,
                             data={}, id='test-id')
    user.credentials.append(credential)
    assert len(user.credentials) == 1

    with patch('homeassistant.auth.AuthManager.active', return_value=True):
        client = await hass_ws_client(hass, hass_access_token)

    await client.send_json({
        'id': 5,
        'type': auth.WS_TYPE_CURRENT_USER,
    })

    result = await client.receive_json()
    assert result['success'], result

    user_dict = result['result']

    assert user_dict['name'] == user.name
    assert user_dict['id'] == user.id
    assert user_dict['is_owner'] == user.is_owner
    assert len(user_dict['credentials']) == 1

    hass_cred = user_dict['credentials'][0]
    assert hass_cred['auth_provider_type'] == 'homeassistant'
    assert hass_cred['auth_provider_id'] is None
    assert 'data' not in hass_cred


async def test_cors_on_token(hass, aiohttp_client):
    """Test logging in with new user and refreshing tokens."""
    client = await async_setup_auth(hass, aiohttp_client)

    resp = await client.options('/auth/token', headers={
        'origin': 'http://example.com',
        'Access-Control-Request-Method': 'POST',
    })
    assert resp.headers['Access-Control-Allow-Origin'] == 'http://example.com'
    assert resp.headers['Access-Control-Allow-Methods'] == 'POST'

    resp = await client.post('/auth/token', headers={
        'origin': 'http://example.com'
    })
    assert resp.headers['Access-Control-Allow-Origin'] == 'http://example.com'


async def test_refresh_token_system_generated(hass, aiohttp_client):
    """Test that we can get access tokens for system generated user."""
    client = await async_setup_auth(hass, aiohttp_client)
    user = await hass.auth.async_create_system_user('Test System')
    refresh_token = await hass.auth.async_create_refresh_token(user, None)

    resp = await client.post('/auth/token', data={
        'client_id': 'https://this-is-not-allowed-for-system-users.com/',
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token.token,
    })

    assert resp.status == 400
    result = await resp.json()
    assert result['error'] == 'invalid_request'

    resp = await client.post('/auth/token', data={
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token.token,
    })

    assert resp.status == 200
    tokens = await resp.json()
    assert (
        await hass.auth.async_validate_access_token(tokens['access_token'])
        is not None
    )


async def test_refresh_token_different_client_id(hass, aiohttp_client):
    """Test that we verify client ID."""
    client = await async_setup_auth(hass, aiohttp_client)
    user = await hass.auth.async_create_user('Test User')
    refresh_token = await hass.auth.async_create_refresh_token(user, CLIENT_ID)

    # No client ID
    resp = await client.post('/auth/token', data={
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token.token,
    })

    assert resp.status == 400
    result = await resp.json()
    assert result['error'] == 'invalid_request'

    # Different client ID
    resp = await client.post('/auth/token', data={
        'client_id': 'http://example-different.com',
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token.token,
    })

    assert resp.status == 400
    result = await resp.json()
    assert result['error'] == 'invalid_request'

    # Correct
    resp = await client.post('/auth/token', data={
        'client_id': CLIENT_ID,
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token.token,
    })

    assert resp.status == 200
    tokens = await resp.json()
    assert (
        await hass.auth.async_validate_access_token(tokens['access_token'])
        is not None
    )


async def test_revoking_refresh_token(hass, aiohttp_client):
    """Test that we can revoke refresh tokens."""
    client = await async_setup_auth(hass, aiohttp_client)
    user = await hass.auth.async_create_user('Test User')
    refresh_token = await hass.auth.async_create_refresh_token(user, CLIENT_ID)

    # Test that we can create an access token
    resp = await client.post('/auth/token', data={
        'client_id': CLIENT_ID,
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token.token,
    })

    assert resp.status == 200
    tokens = await resp.json()
    assert (
        await hass.auth.async_validate_access_token(tokens['access_token'])
        is not None
    )

    # Revoke refresh token
    resp = await client.post('/auth/token', data={
        'token': refresh_token.token,
        'action': 'revoke',
    })
    assert resp.status == 200

    # Old access token should be no longer valid
    assert (
        await hass.auth.async_validate_access_token(tokens['access_token'])
        is None
    )

    # Test that we no longer can create an access token
    resp = await client.post('/auth/token', data={
        'client_id': CLIENT_ID,
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token.token,
    })

    assert resp.status == 400


async def test_ws_long_lived_access_token(hass, hass_ws_client):
    """Test generate long-lived access token."""
    hass.auth = await auth_manager_from_config(
        hass, provider_configs=[{
            'type': 'insecure_example',
            'users': [{
                'username': 'test-user',
                'password': 'test-pass',
                'name': 'Test Name',
            }]
        }], module_configs=[])
    ensure_auth_manager_loaded(hass.auth)
    assert await async_setup_component(hass, 'auth', {'http': {}})
    assert await async_setup_component(hass, 'api', {'http': {}})

    user = MockUser(id='mock-user').add_to_hass(hass)
    cred = await hass.auth.auth_providers[0].async_get_or_create_credentials(
        {'username': 'test-user'})
    await hass.auth.async_link_user(user, cred)

    ws_client = await hass_ws_client(hass, hass.auth.async_create_access_token(
        await hass.auth.async_create_refresh_token(user, CLIENT_ID)))

    # verify create long-lived access token
    await ws_client.send_json({
        'id': 5,
        'type': auth.WS_TYPE_LONG_LIVED_ACCESS_TOKEN,
        'client_name': 'GPS Logger',
        'lifespan': 365,
    })

    result = await ws_client.receive_json()
    assert result['success'], result

    long_lived_access_token = result['result']
    assert long_lived_access_token is not None

    refresh_token = await hass.auth.async_validate_access_token(
        long_lived_access_token)
    assert refresh_token.client_id is None
    assert refresh_token.client_name == 'GPS Logger'
    assert refresh_token.client_icon is None

    # verify long-lived access token can be used as bearer token
    api_client = ws_client.client
    resp = await api_client.get(const.URL_API)
    assert resp.status == 401

    resp = await api_client.get(const.URL_API, headers={
        'Authorization': 'Bearer {}'.format(long_lived_access_token)
    })
    assert resp.status == 200
