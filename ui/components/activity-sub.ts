import { getValue } from 'firebase/remote-config';
import { html, css, LitElement } from 'lit';
import { customElement, property } from 'lit/decorators.js';

@customElement('activity-sub')
export class ActivitySub extends LitElement {
  private _cache: Map<string, any> = new Map();
  private _scopes: Map<string, HTMLElement> = new Map();
  private _root!: HTMLElement;

  @property()
  for = '';

  updated(props: Map<string, unknown>) {
    if (props.has('for')) {
      let old_root = this._root;
      if (this.for == '@parent') {
        this._root = this.parentElement!;
      } else if (this.for == '@root') {
        this._root = (this.getRootNode() as any).host || document.body;
      } else if (!this.for) {
        this._root = this;
      } else {
        this._root = document.getElementById(this.for)!;
      }
      if (!this._root) {
        this._root = this;
        throw new Error(`Could not find element for activity-sub: ${this.for}`);
      }
      this.refreshScopes();
      this.refreshListeners(old_root);
    }
  }

  refreshListeners(old_root: HTMLElement) {
    if (this._root === old_root) return;
    if (old_root) old_root.removeEventListener('item-update', this.onItemUpdate as any);
    this._root.addEventListener('item-update', this.onItemUpdate as any);
  }

  onItemUpdate = (e: ItemUpdateEvent) => {
    this.setItemValue(e.itemid, e.value);
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

export class ItemUpdateEvent extends Event {
  itemid: string;
  value: any;

  constructor(itemid: string, value: any) {
    super('item-update', { bubbles: true, composed: true });
    this.itemid = itemid;
    this.value = value;
  }
}

export function setPropValue(el: any, value: any) {
  if (typeof el.setValue === 'function') {
    return el.setValue(value);
  }
  let handler = tagRegistry.get(el.tagName.toLowerCase());
  if (handler) return handler(el, value);
  el.textContent = el.value = value || '';
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

export type PropSetter = (el: HTMLElement, value: any) => void;

export const tagRegistry: Map<string, PropSetter> = new Map();

export function registerPropSetter(tagNames: string[] | string, setter: PropSetter) {
  if (!Array.isArray(tagNames)) tagNames = [tagNames];
  for (let tagName of tagNames) {
    tagRegistry.set(tagName.toLowerCase(), setter);
  }
}

export function getPropSetter(tagName: string) {
  return tagRegistry.get(tagName.toLowerCase());
}

registerPropSetter(['a', 'area', 'link'], (el, value) => el.setAttribute('href', value || ''));
registerPropSetter(['time'], (el, value) => el.setAttribute('datetime', value || ''));
registerPropSetter(['meta'], (el, value) => el.setAttribute('content', value || ''));
registerPropSetter(['input', 'textarea', 'select', 'data', 'meter', 'output', 'progress', 'attr'], (el, value) => (el as any).value = value || '');
registerPropSetter(['img', 'audio', 'embed', 'iframe', 'img', 'source', 'track', 'video'], (el, value) => value === el.setAttribute('src', value || ''));
registerPropSetter(['object'], (el, value) => el.setAttribute('data', value || ''));

/// Tests /////
export function testStuff() {
  let sub = document.querySelector('activity-sub') as ActivitySub;
  let id = 'https://w3id.org/linkml/examples/personinfo';

  sub.setItemValue(id, { '@id': id, 'id': id, name: 'Mabel' });

  let h1 = document.querySelector('h1.headline');
  let input = document.querySelector('#name') as any;

  console.assert(h1?.textContent == 'Mabel', "%o", { h1 });
  console.assert(input.value == 'Mabel', "%o", { input });

  console.log('yep');
}

//@ts-ignore
window.test = testStuff;