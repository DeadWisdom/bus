import { html, css, LitElement } from 'lit';
import { customElement, property } from 'lit/decorators.js';
import { Task } from '@lit/task';
import { first } from '../bus/objects';

@customElement('schema-set')
export class SchemaSet extends LitElement {
  @property({ type: String })
  url: string = '';

  static styles = css`
    :host {
      display: flex;
      flex-direction: column;
      gap: var(--space);
      align-items: flex-start;
      --space: 10px;
      --space-half: 5px;
    }

    .element {
      display: flex;
      flex-direction: row;
      align-items: center;
      background-color: var(--color-surface-container-highest);
      color: var(--color-on-surface);
      border-radius: var(--border-radius);
      padding: var(--space-half) var(--space);
      gap: var(--space);
      font-size: 1.2rem;
      text-decoration: none;
    }

    .element sl-icon {
      padding: 4px 4px 0px;
      margin: 0 -4px;
    }

    .tag {
      font-weight: bold;
      font-size: .7em;
      border-radius: var(--border-radius);
      background-color: var(--color-surface);
      color: var(--color-tertiary);
      padding: 2px 6px;
    }

    .range {
      font-weight: bold;
      background-color: var(--color-container);
      color: var(--color-primary);
      font-size: 1em;
      margin: 0;
    }

    .group {
      text-transform: uppercase;
      font-size: .7em;
      margin: var(--space) 0 0;
      font-weight: 500;
    }

    .slot[deprecated]  {
      background-color: var(--color-surface-container-highest);
    }
    
    .slot .name {
      font-weight: bold;
    }

    .slot .name:hover, .slot .range:hover {
      text-decoration: underline;
      cursor: pointer;
    }

    .slot:hover sl-icon {
      color: var(--color-primary);
    }

    .slot .tag:hover {
      border: 1px solid var(--color-primary);
      padding: 1px 5px;
      cursor: pointer;
    }

    .slot:hover {
      background-color: var(--color-primary-container);
    }

    .class {
      background-color: var(--color-primary);
      color: var(--color-on-primary);
    }

    .class .name {
      font-weight: normal;
    }

    .class[mixin] {
      background-color: var(--color-tertiary);
    }

    .element[deprecated] .name {
      text-decoration: line-through;
      opacity: .7;
    }

    .enum {
      background-color: var(--color-inverse-surface);
      color: var(--color-inverse-on-surface);
      padding: var(--space-half) var(--space);
    }

    .tag.value {
      background-color: var(--color-primary);
      color: var(--color-on-primary);
    }
  `;

  _contentTask = new Task(this, {
    task: async ([url], { signal }) => {
      const response = await fetch(url, { signal, headers: { 'Accept': 'application/json' } });
      if (!response.ok) { throw new Error(response.status.toString()); }
      // @ts-ignore
      return response.json() as Schema;
    },
    args: () => [this.url]
  });

  render() {
    return this._contentTask.render({
      pending: () => html`<slot></slot>`,
      complete: (schema) => this.renderElements(schema),
      error: (e) => html`<p>Error: ${e}</p>`
    });
  }

  renderElements(schema: SchemaElement) {
    console.log(schema);
    return html`
      ${this.renderClasses(schema)} 
      ${this.renderSlots(schema)} 
      ${this.renderEnums(schema)} 
    `;
  }

  renderSlots(schema: SchemaElement) {
    if (!schema.slots) return;
    return html`
      <h2 class="group">Cannonical Fields (Slots)</h2>
      ${this.sortedElements(Object.values(schema.slots)).map(e => this.renderSlot(e, schema.defaultRange))}
    `;
  }

  renderClasses(schema: SchemaElement) {
    if (!schema.classes) return;
    let entities = Object.values(schema.classes).filter(e => !e.mixin && !e.abstract);
    let mixins = Object.values(schema.classes).filter(e => e.mixin || e.abstract);

    return html`
      <h2 class="group">Classes</h2>
      ${this.sortedElements(Object.values(entities)).map(e => this.renderClass(e))}
      
      <h3 class="group">Mixins</h2>
      ${this.sortedElements(Object.values(mixins)).map(e => this.renderClass(e))}
    `;
  }

  renderEnums(schema: SchemaElement) {
    if (!schema.enums) return;
    return html`
      <h2 class="group">Enums</h2>
      ${this.sortedElements(Object.values(schema.enums)).map(e => this.renderEnum(e))}
    `;
  }

  sortedElements(slots: Element[]) {
    return slots.sort((a, b) => ranker(a) - ranker(b));
  }

  renderSlot(slot: SlotElement, defaultRange?: string) {
    let defaultIcon = 'dash';

    let parts = [
      html`<span class="name">${slot.name}</span>`,
      html`<span class="range">${slot.range || defaultRange}</span>`
    ];

    if (slot.multivalued) {
      defaultIcon = 'list';
      parts.push(html`<span class="multivalued tag">MUL</span>`);
    }

    if (slot.identifier) {
      defaultIcon = 'key';
      parts.push(html`<span class="identifier tag">ID</span>`);
    }

    if (slot.required) {
      parts.push(html`<span class="required tag">*</span>`);
    }

    if (slot.recommended) {
      parts.push(html`<span class="recommended tag">R</span>`);
    }

    if (slot.minimumValue !== undefined) {
      parts.push(html`<span class="minimum-value tag">&gt;=${slot.minimumValue}</span>`);
    }

    if (slot.maximumValue !== undefined) {
      parts.push(html`<span class="maximum-value tag">&lt;=${slot.maximumValue}</span>`);
    }

    if (slot.pattern !== undefined) {
      parts.push(html`<span class="pattern tag">${slot.pattern}</span>`);
    }

    if (slot.deprecated) {
      parts.push(html`<span class="deprecated tag">X</span>`);
    }

    return html`
      <div class="slot element" ?multivalued=${slot.multivalued} ?identifier=${slot.identifier} ?deprecated=${slot.deprecated}>
        ${this.renderIcon(slot, defaultIcon)}
        ${parts}
      </div>
    `;
  }

  renderClass(cls: ClassElement) {
    let defaultIcon = 'card-heading';

    let parts = [
      html`<span class="name">${cls.name}</span>`,
    ];

    if (cls.deprecated) {
      parts.push(html`<span class="deprecated tag">X</span>`);
    }

    if (cls.mixin || cls.abstract) {
      defaultIcon = 'card-text';
    }

    return html`
      <a href="/ns/personinfo/${cls.name}" class="class element" ?deprecated=${cls.deprecated} ?mixin=${cls.mixin || cls.abstract}>
        ${this.renderIcon(cls, defaultIcon)}
        ${parts}
      </a>
    `;
  }

  renderEnum(e: EnumElement) {
    let parts = [
      html`<span class="name">${e.name}</span>`,
    ];

    let permissibleValues = Object.values(e.permissibleValues || {});
    let firstValues = permissibleValues.slice(0, 3);
    firstValues.forEach((pv) => {
      parts.push(html`<span class="value tag">${pv.text}</span>`);
    });

    if (firstValues.length < permissibleValues.length) {
      parts.push(html`<span class="value tag">...</span>`);
    }

    return html`
      <div class="enum element" ?deprecated=${e.deprecated}>
        ${parts}
      </div>
    `;
  }

  renderIcon(el: Element, fallback?: string) {
    let icon = el.annotations?.icon?.value || fallback;
    if (icon)
      return html`
        <sl-icon class="icon" name="${icon}"></sl-icon>
      `;
  }
}

function ranker(el: Element) {
  if (el.mixin) return 999;
  if (el.abstract) return 9999;
  if (el.deprecated) return 99999;
  return el.rank || 0;
}

export interface PermissibleValue {
  text?: string;
}

export interface Annotation {
  tag: string;
  value: string;
}

export interface Prefix {
  prefixPrefix: string;
  prefixReference: string;
}

export interface Element {
  isA?: string;
  annotations?: Record<string, Annotation>;
  name?: string;
  title?: string;
  description?: string;
  deprecated?: string;
  rank?: number;
  keywords?: string[];
  abstract?: boolean;
  mixin?: boolean;
  mixins?: string[];
  idPrefixes?: string[];
  idPrefixesAreClosed?: boolean;

  mappings?: string[];
  exactMappings?: string[];
  relatedMappings?: string[];
  closeMappings?: string[];
  narrowMappings?: string[];
  broadMappings?: string[];
}

export interface TypeDefinition extends Element {
  typeof?: TypeDefinition;
  base?: string;
}

export interface SlotElement extends Element {
  required?: boolean;
  recommended?: boolean;
  multivalued?: boolean;
  identifier?: boolean;
  range?: string;
  maximumValue?: number;
  minimumValue?: number;
  pattern?: string;
  slotUri?: string;
  inlinedAsList?: boolean;
  inlined?: boolean;
}

export interface ClassElement extends Element {
  attributes?: Record<string, SlotElement>;
  slots?: string[];
  classUri?: string;
  treeRoot?: boolean;
}

export interface EnumElement extends Element {
  enumUri?: string;
  permissibleValues?: Record<string, PermissibleValue>;
}

export interface SchemaElement extends Element {
  id: string;
  license?: string;
  version?: string;
  imports?: string[];
  prefixes?: Prefix[];
  defaultRange?: string;
  slots?: Record<string, SlotElement>;
  classes?: Record<string, ClassElement>;
  enums?: Record<string, EnumElement>;
}