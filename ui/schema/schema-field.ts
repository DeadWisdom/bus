import { html, css, LitElement } from 'lit';
import { customElement, property } from 'lit/decorators.js';


@customElement('schema-field')
export class SchemaField extends LitElement {
  @property({ type: String })
  name: string = '';

  @property({ type: String })
  range: string = '';

  @property({ type: String })
  id: string = '';

  @property({ type: Boolean })
  multivalued: boolean = false;

  @property({ type: Boolean })
  identifier: boolean = false;

  static styles = css`
    :host {
      display: block;
      font-size: 1rem;
      --border-radius: 3px;
    }

    .tags {
      display: inline-flex;
      flex-direction: row;
      align-items: center;
      background-color: var(--color-primary-container);
      color: var(--color-on-primary-container);
      border-radius: var(--border-radius);
      padding: var(--space-half);
      gap: var(--space);
    }

    .name {
      font-weight: bold;
      margin-left: -4px;
    }

    .tag {
      border-radius: var(--border-radius);
      background-color: rgba(255, 255, 255, .1);
      padding: 2px 6px;
    }

    .description {
      padding: 0 6px 6px;
      font-size: .8em;
    }

    sl-icon {
      padding: 0 4px;
    }
  `;

  getTags() {
    let tags = [
      { name: 'range', value: this.range },
    ];
    if (this.multivalued) {
      tags.push({ name: 'multivalued', value: '[]' });
    }
    return tags;
  }


  render() {
    return html`
      <div class="tags">
        <sl-icon name=${this.identifier ? "key" : "dot"}></sl-icon>
        <div class="name">
          ${this.name}
        </div>
        ${this.renderTags()}
      </div>
    `;
  }

  renderTags() {
    return this.getTags().map(tag => html`
      <div class="tag" name="${tag.name}">${tag.value}</div>
    `);
  }
}