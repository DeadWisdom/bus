from valet.bus import Collection, Object, Strings

class Function(Object):
    type: str = 'Function'
    trigger: Strings


class Endpoint(Object):
    type: str = 'Endpoint'


class AuthProvider(Collection):
    type: list[str] = ['AuthProvider', 'Collection']
    name: str = 'google'
    items: list[Object] = [
        
    ]

class AuthCollection(Collection):
    pass


class Root(Collection):
    type: list[str] = ['Collection', 'Root']
    items: list[Object] = [
        AuthCollection(name="auth")
    ]

