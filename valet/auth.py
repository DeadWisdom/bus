from nanoid import generate as nanoid
from typing import Annotated
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import Depends, HTTPException, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.routing import APIRouter
from authlib.integrations.starlette_client import OAuth, OAuthError
from authlib.jose import jwt

from .bus.storage.elastic import ElasticStorage, Query
from .bus.objects import Profile, first
from .models import Object, Strings, Functional, References, Account
from .settings import Settings

Token = Annotated[HTTPAuthorizationCredentials, Depends(HTTPBearer(auto_error=False))]

def mint_token(account: Account):
    header = {'alg': 'HS256'}
    claims = {'sub': account.id, 'name': first(account.name)}
    return jwt.encode(header, claims, Settings().auth_private_key).decode()

def read_token(token: str):
    return jwt.decode(token, Settings().auth_private_key)

async def load_account(account_id: str | None):
    if account_id:
        return await storage.load(account_id, index='accounts')

async def get_maybe_account(request: Request, token: Token):
    if token:
        claims = read_token(token.credentials)
        account_id = claims['sub']
    else:
        account_id = request.session.get('account')
    return await load_account(account_id)
    
async def get_verified_account(request: Request, token: Token):
    account = await get_maybe_account(request, token)
    if not account:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return account

MaybeAccount = Annotated[Account, Depends(get_maybe_account)]
VerifiedAccount = Annotated[Account, Depends(get_verified_account)]

## Oauth Handler ##
oauth = OAuth()

CONF_URL = 'https://accounts.google.com/.well-known/openid-configuration'
oauth.register(
    name='google',
    server_metadata_url=CONF_URL,
    client_kwargs={
        'scope': 'openid email profile'
    },
    client_id=Settings().google_oauth_client,
    client_secret=Settings().google_oauth_secret
)

## Accounts ##
storage = ElasticStorage()

async def get_account(provider: str, token: dict):
    user_info = token.get('userinfo')
    sub = user_info.get('sub')
    key = f'{provider}/{sub}'
    results = await storage.search(Query(term={'oauth': key}), index='accounts')
    return results.first()

async def get_or_create_account(provider: str, token: dict):
    account = await get_account(provider, token)
    if not account:
        id = nanoid(size=8)
        user_info = token.get('userinfo')
        sub = user_info.get('sub')
        key = f'{provider}/{sub}'
        account = Account(id=f"/accounts/{id}",
                          oauth=key,
                          name=user_info.get('name'),
                          email=user_info.get('email'), 
                          image=user_info.get('picture'))
        print(account)
        await storage.store(account, index='accounts')
        return account
    return account

async def delete_account(account_id: str):
    await storage.delete(account_id, index='accounts', refresh=True)

## Endpoints ##
router = APIRouter()

@router.get("/google/login")
async def login_google(request: Request):
    redirect_uri = request.url_for('authorize_google')
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google")
async def authorize_google(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
    except OAuthError as error:
        print(error)
        return HTMLResponse(f'<h1>Error authenticating...</h1>')
    account = await get_or_create_account('google', token)
    request.session['account'] = account.id
    return RedirectResponse(url='/')


@router.get('/logout')
async def logout(request: Request):
    request.session.pop('account', None)
    return RedirectResponse(url='/')


example_response = \
{
  "access_token": "ya29.a0AXooCgsbd08UeN_p_oDcjlbeWAjpL0S58JxiGDvAAGWugoDjDnwsCG6bApbLxNCzsJmXV5681SbRjxdrhU6E3b7ex-7RKgm16PlZQgpZlDeS-Hw2NF1HMzpP2PjdjOYAm8OLTh1TKaqArpW-lz8PIvpQWdytrmXRky7AaCgYKAZ4SARMSFQHGX2MixVDNrCRA4_MMGzE3zSKeVw0171",
  "expires_in": 3599,
  "scope": "https://www.googleapis.com/auth/userinfo.profile openid https://www.googleapis.com/auth/userinfo.email",
  "token_type": "Bearer",
  "id_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6ImYyZTExOTg2MjgyZGU5M2YyN2IyNjRmZDJhNGRlMTkyOTkzZGNiOGMiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL2FjY291bnRzLmdvb2dsZS5jb20iLCJhenAiOiI2ODY5OTEwOTAzMDctbGhvaTJ2aDVhbzlwMDNsMjB0YWZoN2k1cm12ZmpuaHYuYXBwcy5nb29nbGV1c2VyY29udGVudC5jb20iLCJhdWQiOiI2ODY5OTEwOTAzMDctbGhvaTJ2aDVhbzlwMDNsMjB0YWZoN2k1cm12ZmpuaHYuYXBwcy5nb29nbGV1c2VyY29udGVudC5jb20iLCJzdWIiOiIxMDY0ODg1Nzc5MzA2NTM3MDEzNDkiLCJlbWFpbCI6ImRlYWR3aXNkb21AZ21haWwuY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsImF0X2hhc2giOiJfNDlkcEpEbWxIcTlCT2pMSnBLOUpBIiwibm9uY2UiOiJjMkZxd0pzQVdnWEU2YkF3YmdiYSIsIm5hbWUiOiJCcmFudGxleSBIYXJyaXMgKERlYWRXaXNkb20pIiwicGljdHVyZSI6Imh0dHBzOi8vbGgzLmdvb2dsZXVzZXJjb250ZW50LmNvbS9hL0FDZzhvY0tucUVKamJySTI3bWVHMzNoRGJxdXhqem5Ub2Q1Y1RPMWUwWWZhZ2FoWmZIWjkxMGQ2PXM5Ni1jIiwiZ2l2ZW5fbmFtZSI6IkJyYW50bGV5IiwiZmFtaWx5X25hbWUiOiJIYXJyaXMiLCJpYXQiOjE3MjIwOTgyMTEsImV4cCI6MTcyMjEwMTgxMX0.d44lp6oBwy522JyVQRz1QdCTcFnqh53s6pMDKUP_P1IUQvtlchzc5NXBOIdRujqp2lsHbD9qt-LgOonTYYTlBdXVzM-DurctrL-FRLKUZNlicEHQJAuGeS4W3LXMVVOPhW5X8MNBhSDpcOcOQvLeie6XvYSrAJgwElsJS6MM3jeD-u8vjUKVDi7RLbELOB3gaqaXk6cqFwBgSXiQ-ujCUUBxXVr3l2Hl50BjZJADRVZVPherV3qvS0bDX69jDuhWucsbZo-YzeUtyD206bWq_Jb69TUbIg-6s_QTFhFlD4zER7f5vccdWEXBePsuV3fbu1JWNKzxn7QQNpQwO3tbqg",
  "expires_at": 1722101811,
  "userinfo": {
    "iss": "https://accounts.google.com",
    "azp": "686991090307-lhoi2vh5ao9p03l20tafh7i5rmvfjnhv.apps.googleusercontent.com",
    "aud": "686991090307-lhoi2vh5ao9p03l20tafh7i5rmvfjnhv.apps.googleusercontent.com",
    "sub": "106488577930653701349",
    "email": "deadwisdom@gmail.com",
    "email_verified": True,
    "at_hash": "_49dpJDmlHq9BOjLJpK9JA",
    "nonce": "c2FqwJsAWgXE6bAwbgba",
    "name": "Brantley Harris (DeadWisdom)",
    "picture": "https://lh3.googleusercontent.com/a/ACg8ocKnqEJjbrI27meG33hDbquxjznTod5cTO1e0YfagahZfHZ910d6=s96-c",
    "given_name": "Brantley",
    "family_name": "Harris",
    "iat": 1722098211,
    "exp": 1722101811
  }
}