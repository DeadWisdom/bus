from typing import Mapping
from valet.bus import Collection, Object, Strings, References, Functional, Values


class Socket(Object):
    type: str = 'Socket'
    supports: References    # A list of types that this socket supports


class Test(Object):
    type: str = 'Test'
    
    input: Functional[Mapping[str, References]]   # A mapping of socket-name -> input
    output: Functional[Mapping[str, References]]  # A mapping of socket-name -> expected output


class Function(Object):
    type: str = 'Function'
    
    guard: Strings
    depends: References
    expected: References
    input: Values[Socket]   # A list of socket that this function takes as input
    output: Values[Socket]  # A list of socket that this function produces as output
    builtin: Functional[bool] = False


class Extension(Object):
    type: str = 'Extension'


class Type(Object):
    type: str = 'Type'
    context: References             # The extension that this type uses
    extends: References
    properties: References          # A list of properties that this type has

    template: Functional[str]
    methods: Functional[dict[str, References]]
    example: References


class Property(Object):
    type: str = "Property"
    range: References
    functional: Functional[bool] = False




#root = Collection(items=[ 
#    Collection(name="auth", items=[
#        Resource(name='logout', handlers=[
#            Function(
#              id="/functions/auth/logout",
#              name='/',
#              guard="post",
#              depends="save_session",
#              input=[Socket(name='request', supports="fastapi.Request")], 
#              output=[Socket(name='response', supports="fastapi.Response")]
#            ),
#        ]),
#        Resource(name='google', handlers=[
#            Function(
#              id="/functions/auth/google/login",
#              name='/login', 
#              guard="get", 
#              depends="oauth.google.authorize_redirect",
#              input=[Socket(name='request', supports="fastapi.Request")], 
#              output=[Socket(name='response', supports="fastapi.Response")]
#            ),
#            Function(
#              id="/functions/auth/google/callback",
#              name='/', 
#              guard="get", 
#              depends=["oauth.google.authorize_access_token", "create_account", "save_session"],
#              input=[Socket(name='request', supports="fastapi.Request")],
#              output=[Socket(name='response', supports="fastapi.Response")]
#            )
#        ])
#    ])
#])
