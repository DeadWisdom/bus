import { LitElement } from 'lit';
import { property } from 'lit/decorators.js';

export interface PageMeta {
  title?: string;
  description?: string;
  noindex?: boolean;
}

export class Page extends LitElement {
  _unload?: CallableFunction;

  @property({ type: Boolean })
  pageIsActive: boolean = false;

  @property({ type: Object })
  pageParams: { [key: string]: string | undefined } = {};

  @property({ type: Object })
  pageMeta: PageMeta = {};

  createRenderRoot() {
    return this;
  }

  disconnectedCallback(): void {
    super.disconnectedCallback();
    if (this._unload) this._unload();
    this._unload = undefined;
  }

  load(): CallableFunction | (CallableFunction | undefined)[] | null | void {
    return null;
  }

  reload() {
    if (this._unload) this._unload();
    let unloader = this.load() as CallableFunction | undefined | (CallableFunction | undefined)[];
    if (unloader == null) this._unload = undefined;
    else if (Array.isArray(unloader))
      this._unload = () => (unloader as CallableFunction[]).forEach(fn => (fn ? fn() : null));
    else this._unload = unloader;
  }

  update(changedProperties: Map<PropertyKey, unknown>) {
    if (changedProperties.has('pageParams')) {
      this.reload();
    }
    super.update(changedProperties);
  }

  protected shouldUpdate(): boolean {
    // We will only ever update if page is active
    return this.pageIsActive;
  }
}
