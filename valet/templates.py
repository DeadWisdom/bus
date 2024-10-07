import base64
import orjson
import re
import os
from jinja2 import Template
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from dataclasses import is_dataclass, asdict
from inflection import camelize
from typing import Annotated

from fastapi import Depends, Request
from fastapi.templating import Jinja2Templates

from .auth import MaybeAccount
from .bus import first

from .bus import first
from .settings import Settings


### Globals ###
def simple_dict(items):
    return {camelize(key, False): value for key, value in items if value is not None and value != [] and value != {}}

def json_pretty(obj):
    return orjson.dumps(items(obj), option=orjson.OPT_INDENT_2).decode()

def items(obj):
    return asdict(obj, dict_factory=simple_dict)

def get_icon(obj, default=''):
    if not obj:
        return default
    annotations = getattr(obj, 'annotations', {})
    icon = annotations.get('icon', None)
    if icon:
        return icon.value
    return default

def json64(obj):
    if obj is None:
        return ''
    if isinstance(obj, BaseModel):
        return base64.b64encode(obj.model_dump_json().encode()).decode()
    if is_dataclass(obj):
        items = asdict(obj, dict_factory=simple_dict)
        return base64.b64encode(orjson.dumps(items)).decode()
    return base64.b64encode(orjson.dumps(obj)).decode()


### Snippets ###
re_snippet = re.compile(r'@snippet.*?(?P<name>\w+)\s*=\s*\((?P<args>.*?)\).*?html`(?P<src>.*?)`', re.MULTILINE | re.DOTALL | re.IGNORECASE)
re_expressions = re.compile(r'\${(.*?)}', re.MULTILINE | re.IGNORECASE)

class Snippet:
    _cache = {}
    name: str
    src: str
    args: list[str]
    template: Template

    def __init__(self, name: str, src: str, args: str | list[str]):
        self.name = name
        self.args = self._scan_args(args)
        self.src = src
        self.template = templates.env.from_string(self._transpile(src))

    def render(self, *args, **kwargs):
        return self.template.render(*args, **kwargs)

    @classmethod
    def load(cls, name):
        if not Settings().disable_caching and name in cls._cache:
            return cls._cache[name]
        cls._reload_templates()
        return cls._cache[name]
    
    @classmethod
    def _reload_templates(cls, base_path='ui/snippets'):
        cls._cache.clear()
        for filename in os.listdir(base_path):
            if not filename.endswith('.ts'):
                continue
            with open(os.path.join(base_path, filename)) as f:
                src = f.read()
            for s in cls._scan_snippets(src):
                cls._cache[s.name] = s
    
    @classmethod
    def _scan_args(cls, args: str | list[str]):
        if isinstance(args, list):
            entries = args
        else:
            entries = args.split(',')
        results = []
        for entry in entries:
            name, _, _ = entry.partition(':')
            results.append(name.strip())
        return results

    @classmethod
    def _scan_snippets(cls, src):
        return [cls(**m.groupdict()) for m in re_snippet.finditer(src)]
    
    @classmethod
    def _transpile(self, src):
        return re_expressions.sub(r'{{\1}}', src)

def render_snippet(__snippet_name, *args, **kwargs):
    snippet = Snippet.load(__snippet_name)
    return snippet.render(*args, **kwargs)


### Dependency ###
class TemplateRender:
    request: Request
    account: MaybeAccount | None

    def __init__(self, request: Request, account: MaybeAccount):
        self.request = request
        self.account = account
    
    def render(self, name: str, context: dict = {}, **kwargs):
        context = dict(context)
        context.setdefault('account', self.account)
        headers = kwargs.pop('headers', {})
        headers.setdefault('Vary', 'Accept')
        return templates.TemplateResponse(request=self.request, name=name, context=context, headers=headers, **kwargs)
    
Templates = Annotated[TemplateRender, Depends(TemplateRender)]


### Environment ###
templates = Jinja2Templates(directory="valet/templates")
templates.env.globals.update({
    'json64': json64,
    'json_pretty': json_pretty,
    'first': first,
    'dir': dir,
    'items': items,
    'get_icon': get_icon,
    'render_snippet': render_snippet
})
