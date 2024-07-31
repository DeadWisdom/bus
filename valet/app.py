import base64, orjson
from typing import Annotated
from yarl import URL
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import ORJSONResponse, HTMLResponse
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel

from . import logging
from .bus import Activity, Object, Collection, gather_ids, first, Forbidden, stock, Worker
from .bus import Bus as _Bus
from .auth import router as auth, MaybeAccount, VerifiedAccount

def json64(obj):
    if obj is None:
        return ''
    if isinstance(obj, BaseModel):
        return base64.b64encode(obj.model_dump_json().encode()).decode()
    return base64.b64encode(orjson.dumps(obj)).decode()

def get_bus(account: MaybeAccount):
    return Bus(account.id if account else None)

def get_authenticated_bus(account: VerifiedAccount):
    return Bus(account.id)

Bus = Annotated[_Bus, Depends(get_bus)]
AuthenticatedBus = Annotated[_Bus, Depends(get_authenticated_bus)]


app = FastAPI(default_response_class=ORJSONResponse)

# Middleware
app.add_middleware(SessionMiddleware, secret_key="VYtmV0VeXE9cNW-T2iuec-tQsSHySkKvV1eMyzJUPBm")
app.add_middleware(GZipMiddleware, minimum_size=1000)

## Routers
app.include_router(auth, prefix="/auth")

## Templates & Static
app.mount("/ui", StaticFiles(directory="./build/ui"), name="ui")
templates = Jinja2Templates(directory="valet/templates")
templates.env.globals['json64'] = json64


## Stock Collections ##
stock['/'] = Collection(id='/', type='Collection', attributed_to="/accounts/TQSdRqi6", audience="public")
stock['/accounts'] = Collection(id='/accounts', type='Collection', attributed_to="/accounts/TQSdRqi6", audience="private")


def json_ld_response(obj: Object, media_type='application/ld+json; profile="https://www.w3.org/ns/activitystreams', status_code=200, **kwargs):
    content = obj.model_dump_json(by_alias=True, context={'@context': "https://www.w3.org/ns/activitystreams"})
    return HTMLResponse(content, media_type=media_type, status_code=status_code, **kwargs)


async def send_and_wait(bus: Bus, act: Activity):
    await bus.send(act)
    worker = Worker(raise_errors=True)
    act = await worker(act)
    return act.result

async def derefernce_or_404(bus: _Bus, url: str | URL) -> Object:
    url = URL(str(url))
    obj = await bus.dereference(url)
    if obj is None:
        raise HTTPException(status_code=404, detail="Object not found")
    return obj


class TemplateRender:
    request: Request
    account: MaybeAccount | None

    def __init__(self, request: Request, account: MaybeAccount):
        self.request = request
        self.account = account
    
    def render(self, name: str, context: dict = {}):
        context = dict(context)
        context.setdefault('account', self.account)
        return templates.TemplateResponse(request=self.request, name=name, context=context)

Templates = Annotated[TemplateRender, Depends(TemplateRender)]

## UI ##
@app.get("/")
async def index(template: Templates, response_class=HTMLResponse):
    return template.render("index.html")



## General ##
@app.put("/{_:path}")
async def put(_: str, object: Object, request: Request, bus: AuthenticatedBus):
    url = URL(str(request.url))
    
    if not await bus.can_write(url.parent):
        raise HTTPException(status_code=403, detail="Forbidden")
    
    object.id = str(url)
    result = await send_and_wait(bus, Activity(type='Create', object=object))
    
    collection = await bus.dereference(str(url.parent))
    if collection is not None:
        object = first(result)
        await send_and_wait(bus, Activity(type='Add', object=object, target=collection.id))

    return json_ld_response(object, status_code=201)
    

@app.get("/{_:path}")
async def get(_: str, request: Request, templates: Templates, bus: Bus) -> Object:
    object = await derefernce_or_404(bus, request.url)

    if ('Collection' in object.type):
        object = Collection.model_validate(object.model_dump())
        page = await bus.load_collection_page(object.id)
        object.items = page.items
        object.first = page.first
        object.next = page.next
        object.total_items = page.total_items
        template_name = 'collection.html'
    else:
        template_name = 'resource.html'
    
    accept_header = request.headers.get("Accept")
    if accept_header.startswith('text/html'):
        return templates.render(template_name, {'object': object})

    return json_ld_response(object)


## Exceptions ###
@app.exception_handler(Forbidden)
async def forbidden_exception_handler(request: Request, exc: Forbidden):
    return HTMLResponse(status_code=403, content="Forbidden")


