import { getValue } from 'firebase/remote-config';
import { html, css, LitElement } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import { e } from '../../build/ui/async-18cb95062305769f';

@customElement('activity-sub')
export class ActivitySub extends LitElement {
  private _cache: Map<string, any> = new Map();
  private _scopes: Map<string, HTMLElement> = new Map();
  private _root: HTMLElement | null = null;

  @property()
  for = '';

  updated(props: Map<string, unknown>) {
    if (props.has('for')) {
      if (this.for == '@parent') {
        this._root = this.parentElement;
      } else if (this.for == '@root') {
        this._root = (this.getRootNode() as any).host || document.body;
      } else if (!this.for) {
        this._root = this;
      } else {
        this._root = document.getElementById(this.for);
        if (!this._root) {
          throw new Error(`Could not find element with id ${this.for}`);
        }
      }
      this.refreshScopes();
    }
  }

  createRenderRoot() {
    //@ts-ignore
    window.sub = this;
    return this;
  }

  refreshScopes() {
    this._scopes.clear();

    let elements = itemScopeSelector(this._root!);
    for (let el of elements) {
      let id = el.getAttribute('itemid');
      if (id) {
        this._scopes.set(id, el);
        this._cache.set(id, getScopeValue(el));
      }
    }

    console.log("activity-sub scopes", this._scopes);
    console.log("activity-sub cache", this._cache);
  }

  getItemValue(id: string) {
    return this._cache.get(id);
  }

  setItemValue(id: string, value: any) {
    this._cache.set(id, value);
    let el = this._scopes.get(id);
    if (el) {
      setScopeValue(el, value);
    }
  }
}

export function getPropValue(el: any) {
  if (typeof el.getValue === 'function') {
    return el.getValue();
  }
  let handler = tagRegistry.get(el.tagName.toLowerCase());
  if (handler) return handler.getValue(el);
  return el.value || el.getAttribute('value') || el.textContent || undefined;
}

export function setPropValue(el: any, value: any) {
  if (typeof el.setValue === 'function') {
    return el.setValue(value);
  }
  let handler = tagRegistry.get(el.tagName.toLowerCase());
  if (handler) return handler.setValue(el, value);
  el.textContent = el.value = value || '';
}

export function getScopeValue(element: HTMLElement) {
  let value: Record<string, any> = {};
  let propEls = itemPropSelector(element);

  if (element.hasAttribute('itemid')) {
    value['@id'] = element.getAttribute('itemid');
  }

  if (element.hasAttribute('itemtype')) {
    value['@type'] = element.getAttribute('itemtype');
  }

  function setValue(k: string, v: any) {
    if (v === undefined || v === null) return;
    if (value[k] === undefined) {
      value[k] = v;
    } else if (value[k] instanceof Array) {
      if (v instanceof Array) {
        value[k].push(...v);
      } else {
        value[k].push(v);
      }
    } else {
      if (v instanceof Array) {
        value[k] = [value[k], ...v];
      } else {
        value[k] = [value[k], v];
      }
    }
  }

  for (let propEl of propEls) {
    setValue(propEl.getAttribute('itemprop')!, getPropValue(propEl));
  }

  return value;
}

export function setScopeValue(element: HTMLElement, value: Record<string, any>) {
  let propEls = itemPropSelector(element);

  if (value['@id']) {
    element.setAttribute('itemid', value['@id']);
  }

  if (value['@type']) {
    element.setAttribute('itemtype', value['@type']);
  }

  for (let propEl of propEls) {
    let prop = propEl.getAttribute('itemprop')!;
    setPropValue(propEl, value[prop]);
  }
}

function itemPropSelector(root: HTMLElement) {
  let results: HTMLElement[] = [];
  let walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, (node: Node) => {
    let el = node as HTMLElement;
    if (el.hasAttribute('itemprop') || el.hasAttribute('takeprop')) {
      results.push(el);
      if (el.hasAttribute('itemscope')) {
        return NodeFilter.FILTER_REJECT;
      }
    }
    return NodeFilter.FILTER_SKIP;
  });
  while (walker.nextNode()) { };
  return results;
}

function itemScopeSelector(root: HTMLElement) {
  let results: HTMLElement[] = [];
  let walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, (node: Node) => {
    let el = node as HTMLElement;
    if (el.hasAttribute('itemscope')) {
      results.push(el);
      return NodeFilter.FILTER_REJECT;
    }
    return NodeFilter.FILTER_SKIP;
  });
  while (walker.nextNode()) { };
  return results;
}

/// Tag Property Handlers
interface TagPopHandler {
  tagNames: string[];
  getValue: (el: HTMLElement) => any;
  setValue: (el: HTMLElement, value: any) => void;
}

export const tagRegistry: Map<string, TagPopHandler> = new Map();

export function registerTagPopHandler(handler: TagPopHandler) {
  let names = handler.tagNames.map(n => n.toLowerCase());
  handler.tagNames = names;
  for (let tagName of names) {
    tagRegistry.set(tagName.toLowerCase(), handler);
  }
}

export function getTagPropHandler(tagName: string) {
  return tagRegistry.get(tagName.toLowerCase());
}

registerTagPopHandler({
  tagNames: ['a', 'area', 'link'],
  getValue: (el) => el.getAttribute('href'),
  setValue: (el, value) => el.setAttribute('href', value),
});

registerTagPopHandler({
  tagNames: ['img'],
  getValue: (el) => el.getAttribute('src'),
  setValue: (el, value) => el.setAttribute('src', value),
});

registerTagPopHandler({
  tagNames: ['time'],
  getValue: (el) => el.getAttribute('datetime'),
  setValue: (el, value) => el.setAttribute('datetime', value),
});

registerTagPopHandler({
  tagNames: ['meta'],
  getValue: (el) => el.getAttribute('content'),
  setValue: (el, value) => el.setAttribute('content', value),
});

registerTagPopHandler({
  tagNames: ['input', 'textarea', 'select', 'data', 'meter', 'output', 'progress', 'attr'],
  getValue: (el) => (el as HTMLInputElement).value,
  setValue: (el, value) => (el as HTMLInputElement).value = value || '',
});

// TODO: These should be relative to the document...
registerTagPopHandler({
  tagNames: ['audio', 'embed', 'iframe', 'img', 'source', 'track', 'video'],
  getValue: (el) => el.getAttribute('src'),
  setValue: (el, value) => el.setAttribute('src', value),
});

registerTagPopHandler({
  tagNames: ['object'],
  getValue: (el) => el.getAttribute('data'),
  setValue: (el, value) => el.setAttribute('data', value),
});


/// Tests /////
export function testGettingSetting() {
  let sub = document.querySelector('activity-sub') as ActivitySub;
  let id = 'https://w3id.org/linkml/examples/personinfo';

  let value = sub.getItemValue(id);
  value.name = 'Mabel';
  sub.setItemValue(id, value);

  let h1 = document.querySelector('h1.headline');
  let input = document.querySelector('#name') as any;

  console.assert(h1?.textContent == 'Mabel', "%o", { h1 });
  console.assert(input.value == 'Mabel', "%o", { input });
}

//@ts-ignore
window.test = testGettingSetting;