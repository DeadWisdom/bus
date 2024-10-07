import { html, css, LitElement, type PropertyValueMap } from 'lit';
import { customElement, property } from 'lit/decorators.js';

import '@shoelace-style/shoelace/dist/components/avatar/avatar.js';
import type { SlDrawer } from '@shoelace-style/shoelace';
import { first, type ActivityObject } from '../bus/objects';

@customElement('activity-auth')
export class ActivityAuth extends LitElement {
  @property({ type: Boolean })
  authenticated?: boolean = false;

  @property({ type: Object })
  account?: ActivityObject;

  static styles = css`
    :host {
    }

    sl-avatar {
      cursor: pointer;
      --size: 36px;
    }

    .stack {
      display: flex;
      flex-direction: column;
      gap: 1em;
    }

    .stack > * {
      margin: 0;
    }

    form sl-button {
      margin-top: 1em;
      align-self: flex-end;
    }

    *:not(:defined) {
      display: none;
    } 

    sl-drawer {
      font-size: var(--sl-font-size-small);
    }

    sl-drawer img {
      width: 100px;
      sizing: contain;
      border-radius: 5px;
    }
  `;

  connectedCallback(): void {
    super.connectedCallback();
    if (this.authenticated) {
      let raw = sessionStorage.getItem('account');
      if (raw) this.onAccountInfo(JSON.parse(raw));
      else fetch('/auth/account').then(r => r.json()).then(this.onAccountInfo);
    }
  }

  onAccountInfo = (account: ActivityObject) => {
    console.log('authenticated', account);
    this.account = account;
    this.authenticated = true;
    sessionStorage.setItem('account', JSON.stringify(account));
  }

  onLogout = () => {
    fetch('/auth/logout', { method: 'GET' });
    this.account = undefined;
    this.authenticated = false;
  }

  showDrawer = () => {
    let drawer = this.shadowRoot!.querySelector('sl-drawer') as SlDrawer;
    drawer.show();
  }

  hideDrawer = () => {
    let drawer = this.shadowRoot!.querySelector('sl-drawer') as SlDrawer;
    drawer.hide();
  }

  render() {
    return html`
      ${this.renderDrawer()}
      ${this.renderAvatar()}
    `
  }

  renderAvatar() {
    if (!this.account) return this.renderAnonAvatar();

    return html`<sl-avatar label=${first(this.account.summary)} image=${first(this.account.image)} @click=${this.showDrawer}></sl-avatar>`;
  }

  renderAnonAvatar() {
    return html`<sl-avatar label="Logged Out" @click=${this.showDrawer}></sl-avatar>`;
  }

  renderDrawer() {
    if (!this.account) return this.renderAnonDrawer();

    return html`<sl-drawer label=${first(this.account.summary)}>
      <div class="stack">
        <img src=${first(this.account.image)}></img>
        <p>Email: ${first(this.account.email)}</p>

        <sl-button type="primary" size="small" @click=${this.onLogout}>Logout</sl-button>
      </div>
    </sl-dawer>`;
  }

  renderAnonDrawer() {
    return html`<sl-drawer label="Who Dis?">
      <sl-button href="/auth/google/login" variant="primary" rel="noreferrer noopener external">Login with Google</sl-button>
    </sl-dawer>`;
  }
}