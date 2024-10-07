import { Router } from '@lit-labs/router';
import { html, css, LitElement } from 'lit';
import { customElement, property } from 'lit/decorators.js';

@customElement('app-layout')
export class AppLayout extends LitElement {
  static styles = css`
    :host {
    }
  `;

  render() {
    return html`
      <slot></slot>
    `
  }
}
