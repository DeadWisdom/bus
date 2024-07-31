from typing import Mapping
from valet.bus import Collection, Object, Strings, References, Node, Functional

class Type(Object):
    type: str = 'Type'
    inherits: References


class Socket(Object):
    type: str = 'Socket'
    supports: References    # A list of types that this socket supports


class Example(Object):
    type: str = 'Example'
    
    input: Mapping[str, Node]   # A list of inputs
    output: Mapping[str, Node]  # A list of outputs


class Function(Object):
    type: str = 'Function'
    
    guard: Strings
    depends: References
    input: list[Socket]   # A list of socket that this function takes as input
    output: list[Socket]  # A list of socket that this function produces as output
    example: References   # A list of examples that demonstrate how this function works 
    builtin: Functional[bool] = False


class Resource(Object):
    type: str = 'Resource'
    handler: Function


root = Collection(items=[ 
    Collection(name="auth", items=[
        Resource(name='logout', handlers=[
            Function(
              id="/functions/auth/logout",
              name='/',
              guard="post",
              depends="save_session",
              input=[Socket(name='request', supports="fastapi.Request")], 
              output=[Socket(name='response', supports="fastapi.Response")]
            ),
        ]),
        Resource(name='google', handlers=[
            Function(
              id="/functions/auth/google/login",
              name='/login', 
              guard="get", 
              depends="oauth.google.authorize_redirect",
              input=[Socket(name='request', supports="fastapi.Request")], 
              output=[Socket(name='response', supports="fastapi.Response")]
            ),
            Function(
              id="/functions/auth/google/callback",
              name='/', 
              guard="get", 
              depends=["oauth.google.authorize_access_token", "create_account", "save_session"],
              input=[Socket(name='request', supports="fastapi.Request")],
              output=[Socket(name='response', supports="fastapi.Response")]
            )
        ])
    ])
])
