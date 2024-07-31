import { html, css, LitElement } from 'lit';
import { customElement, property } from 'lit/decorators.js';

@customElement('activity-card')
export class ActivityCard extends LitElement {
  static styles = css`
    :host {
      display: flex;
      flex-direction: row;
      max-width: 600px;
      background-color: var(--color-surface-container);
      color: var(--color-on-surface-container);
      padding: var(--space);
      font-size: 1rem;
      height: 64px;
      align-items: center;
      min-width: 300px;
    }

    .container {
      display: flex;
      flex-direction: column;
      gap: var(--space);
      margin: var(--space);
    }

    .headline {
      font-size: 1.3rem;
      line-height: 1.1;
      display: block;
      color: currentColor;
      text-decoration: none;
      outline: none;
    }

    .supporting-text {
    }

    :host([href]:hover) {
      outline: var(--color-on-surface) solid 2px;
      cursor: pointer;
    }

    :host(:focus-within) {
      outline: var(--color-primary) solid 2px;
      outline-offset: 2px;
      box-shadow: inset var(--color-on-surface) 0 0 0 1px;
    }

    :host([href]:hover) {
      outline: var(--color-on-surface) solid 2px;
      cursor: pointer;
    }
  `;

  @property()
  headline = '';

  @property()
  href = '';

  @property()
  variant = "default";

  connectedCallback(): void {
    super.connectedCallback();
    this.addEventListener('click', this.onClick);
  }

  onClick = (e: MouseEvent) => {
    console.log(e);
    if (!this.href) return;
    if (window.getSelection()?.toString()) return;

    e.preventDefault();

    (this.shadowRoot!.querySelector('a.headline') as HTMLElement).click();
  }

  renderHeadline() {
    let value = this.headline || html`<slot name="headline"></slot>`;
    if (this.href) {
      return html`<a class="headline" href="${this.href}" part="headline" @click=${(e: MouseEvent) => e.stopPropagation()}>${value}</a>`;
    } else {
      return html`<div class="headline" part="headline">${value}</div>`;
    }
  }

  render() {
    return html`
      <div class="start" part="start">
        <slot name="start"></slot>
      </div>
      <div class="container" part="container">
        ${this.renderHeadline()}
        <div class="supporting-text" part="supporting-text">
          <slot name="supporting-text"></slot>
        </div>
      </div>
    </div>
    `;
  }
}