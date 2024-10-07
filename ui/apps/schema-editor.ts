import { Router } from './router';
import { html, css, LitElement } from 'lit';
import { customElement, property } from 'lit/decorators.js';

@customElement('schema-editor')
export class SchemaEditor extends LitElement {
  static styles = css`
    :host {
    }
  `;

  private _router = new Router(this, [
    { path: '/ns/:schema' },
    { path: '/ns/:schema/:element' },
    { path: '/ns/*' }
  ]);

  @property({ type: Object })
  schema?: any;

  @property({ type: Object })
  element?: any;

  createRenderRoot() {
    return this;
  }

  renderHeader() {
    return html`
    <header>
        <activity-search>
          <form action="." method="get">
            <input autocomplete="off" autocapitalize="off" type="search" placeholder="Search elements"> <button
              aria-label="Submit" type="submit"><svg xmlns="http://www.w3.org/2000/svg" height="24px"
                viewBox="0 -960 960 960" width="24px" fill="#5f6368">
                <path
                  d="M784-120 532-372q-30 24-69 38t-83 14q-109 0-184.5-75.5T120-580q0-109 75.5-184.5T380-840q109 0 184.5 75.5T640-580q0 44-14 83t-38 69l252 252-56 56ZM380-400q75 0 127.5-52.5T560-580q0-75-52.5-127.5T380-760q-75 0-127.5 52.5T200-580q0 75 52.5 127.5T380-400Z" />
              </svg></button>
          </form>
        </activity-search>
        <div class="spacer"></div>
        <activity-auth {% if account %}authenticated{% endif %}></activity-auth>
      </header>
    `;
  }

  renderMain() {
    return html`
      <main>
        <section class="stack">
          <h1 class="headline">${this.schema?.name || 'unknown'}</h1>
          <div class="row"><sl-badge variant="success">schema</sl-badge> <sl-badge variant="neutral">draft</sl-badge>
          </div>
        </section>
      </main>
    `;
  }

  render() {
    return html`
    <app-layout>
      <nav></nav>
      <div part="pane" class="pane">
        ${this.renderHeader()}
        ${this.renderMain()}
      </div>

      <div part="pane" class="pane"">
        <header></header>
        <h2>Element</h2>
      </div>
    </div>`;
  }
}
