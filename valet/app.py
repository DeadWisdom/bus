from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import HTMLResponse, ORJSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from yarl import URL

from .auth import MaybeAccount, VerifiedAccount
from .auth import router as auth
from .bus import Activity
from .bus import Bus as _Bus
from .bus import Collection, Forbidden, Object, Worker, first, stock
from .schemas import (ClassDefinition, EnumDefinition, SchemaDefinition,
                      SlotDefinition, schemas)
from .templates import Templates

def get_definition_template(obj):
    if isinstance(obj, SchemaDefinition):
        return 'parts/schema.html'
    if isinstance(obj, ClassDefinition):
        return 'parts/class.html'
    if isinstance(obj, SlotDefinition):
        return 'parts/slot.html'
    if isinstance(obj, EnumDefinition):
        return 'parts/enum.html'
    else:
        raise ValueError("Object type not recognized")

def wants_html(request: Request):
    accept_header = request.headers.get("Accept")
    return accept_header.startswith('text/html')


### Dependencies
def get_bus(account: MaybeAccount):
    return _Bus(account.id if account else None)

def get_authenticated_bus(account: VerifiedAccount):
    return _Bus(account.id)


Bus = Annotated[_Bus, Depends(get_bus)]
AuthenticatedBus = Annotated[_Bus, Depends(get_authenticated_bus)]
HTMLAccept = Annotated[bool, Depends(wants_html)]

app = FastAPI(default_response_class=ORJSONResponse)

# Middleware
app.add_middleware(SessionMiddleware, secret_key="VYtmV0VeXE9cNW-T2iuec-tQsSHySkKvV1eMyzJUPBm")
app.add_middleware(GZipMiddleware, minimum_size=1000)

## Routers
app.include_router(auth, prefix="/auth")

## Templates & Static
def load_snippet(filename, name):
    with open(f'ui/snippets/{filename}.ts') as f:
        return f.read()


app.mount("/ui", StaticFiles(directory="./build/ui"), name="ui")

## Stock Collections ##
stock['/'] = Collection(id='/', type='Collection', attributed_to="/accounts/TQSdRqi6", audience="public")
stock['/accounts'] = Collection(id='/accounts', type=['Collection', 'Accounts'], attributed_to="/accounts/TQSdRqi6", audience="private")


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


## UI ##
@app.get("/")
async def index(template: Templates, response_class=HTMLResponse):
    return template.render("index.html")


@app.get("/ns")
async def namespace(bus: Bus, template: Templates):
    items = [
        Object(id=f'/ns/bus', type='Schema', name="Activity Bus", summary="The schema that drives this system"),
        Object(id=f'/ns/activitystrems', type='Schema', name="Activity Streams 2.0", summary="From the Activity Vocabulary", url="https://www.w3.org/TR/activitystreams-vocabulary"),
        Object(id=f'/ns/linkml', type='Schema', name="LinkML Model", summary="Metamodels of the Linked Data Modeling Language framework ", url="https://w3id.org/linkml/"),
        Object(id=f'/ns/schema_org', type='Schema', name="Schema.org", summary="A treasure trove of community made schemas from Schema.org", url="https://schema.org"),
    ]
    attributed_to = await bus.dereference('/accounts/TQSdRqi6')
    collection = Collection(
        id='/ns', 
        name="Schemas",
        summary="All system schemas",
        type='Collection', 
        attributed_to=attributed_to, 
        audience="public",
        items=items)
    return template.render("collection.html", context={'collection': collection, 'schemas': schemas})


@app.get("/ns/{name}")
async def namespace_detail(name: str, bus: Bus, template: Templates, request: Request, html: HTMLAccept):
    view = schemas.get(name)
    if view is None:
        raise HTTPException(status_code=404, detail="Schema not found")
    if html:
        return template.render("schema.html", context={'view': view, 'schema': view.schema, 'element': None, 'uri': f'/ns/{name}'})
    return items(view.schema)


@app.get("/ns/{schema_name}/{element_name}")
async def element_detail(schema_name: str, element_name: str, bus: Bus, template: Templates, request: Request, html: HTMLAccept):
    view = schemas.get(schema_name)
    if view is None:
        raise HTTPException(status_code=404, detail="Schema not found")
    element = view.get_element(element_name)
    if element is None:
        raise HTTPException(status_code=404, detail="Schema not found")
    if html:
        return template.render("schema.html", context={'view': view, 'schema': view.schema, 'element': element, 'template': get_definition_template(element), 'uri': f'/ns/{schema_name}/{element_name}'})
    return items(element)

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
    
    context = {}
    if ('Collection' in object.type):
        object = Collection.model_validate(object.model_dump())
        page = await bus.load_collection_page(object.id)
        object.items = page.items
        object.first = page.first
        object.next = page.next
        object.total_items = page.total_items
        template_name = 'collection.html'
        context['collection'] = object
    else:
        template_name = 'resource.html'
        context['object'] = object
    
    if wants_html(request):
        return templates.render(template_name, context=context)

    return json_ld_response(object)


## Exceptions ###
@app.exception_handler(Forbidden)
async def forbidden_exception_handler(request: Request, exc: Forbidden):
    return HTMLResponse(status_code=403, content="Forbidden")

