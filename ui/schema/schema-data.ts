import { html, css, LitElement } from 'lit';
import { customElement, property } from 'lit/decorators.js';


@customElement('schema-data')
export class SchemaData extends LitElement {
  @property({ type: String })
  name: string = '';

  @property({ type: String })
  uri: string = '';

  static styles = css`
    :host {
    }
  `;

  render() {
    return html`
      <slot name="label"></slot>
      <slot></slot>
    `;
  }
}