import { html, css, LitElement } from 'lit';
import { customElement, property } from 'lit/decorators.js';

@customElement('activity-card')
export class ActivityCard extends LitElement {
  static styles = css`
    :host {
      display: flex;
      flex-direction: row;
      max-width: var(--width-content, 600px);
      background-color: var(--color-surface-container);
      color: var(--color-on-surface-container);
      padding: 0 var(--space);
      font-size: 1rem;
      height: 64px;
      align-items: center;
      min-width: 300px;
      border-radius: var(--border-radius);
    }

    :host([tight]) {
      --space: 4px;
      height: 42px;
      font-size: .8rem;
    }

    .container {
      display: flex;
      flex-direction: column;
      margin: var(--space);
      flex-grow: 1;
      flex-shrink: 1;
      overflow: hidden;
    }

    .headline {
      font-size: 1.3em;
      line-height: 1.2;
      display: block;
      color: currentColor;
      text-decoration: none;
      outline: none;
    }

    .supporting-text {
      white-space: nowrap;
      font-size: .8em;
    }

    :host(:hover) {
      background-color: var(--color-secondary-container);
      cursor: pointer;
    }

    :host(:focus-within) {
      outline: var(--color-primary) solid 2px;
      outline-offset: 2px;
      box-shadow: inset var(--color-on-surface) 0 0 0 1px;
    }

    .start, .end {
      padding: 0 var(--space);
      padding-top: 3px;
      flex-shrink: 0;
    }

    .end {
      font-size: .8rem;
    }
  `;

  @property()
  headline = '';

  @property()
  href = '';

  @property()
  variant = "default";

  @property({ type: Boolean, reflect: true })
  tight: boolean = false

  connectedCallback(): void {
    super.connectedCallback();
    this.addEventListener('click', this.onClick);
  }

  onClick = (e: MouseEvent) => {
    if (!this.href) return;
    if (window.getSelection()?.toString()) return;

    e.preventDefault();

    (this.shadowRoot!.querySelector('a.headline') as HTMLElement).click();
  }

  onSlotChange = (e: Event) => {
    let slot = this.shadowRoot!.querySelector("slot[name='start']") as HTMLSlotElement;
    if (!slot) return;
    let nodes = slot.assignedNodes();
    if (nodes.length > 0) {
      this.classList.add('has-start');
    } else {
      this.classList.remove('has-start');
    }
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
      <div class="start" part="start" @slotchange=${this.onSlotChange}>
        <slot name="start"></slot>
      </div>
      <div class="container" part="container">
        ${this.renderHeadline()}
        <div class="supporting-text" part="supporting-text">
          <slot name="supporting-text"></slot>
        </div>
      </div>
      <div class="end" part="start" @slotchange=${this.onSlotChange}>
        <slot name="end"></slot>
      </div>
    </div>
    `;
  }
}