import { html } from "lit";

//@snippet
export const classElement = (id: string, type: string, url: string, icon: string, element: any) => html`
  <schema-item class="class element" itemscope itemid="${id}" itemtype="${type}">
  <a href="${url}">
    <sl-icon class="icon" name="icon" aria-hidden="true" library="default"></sl-icon>
    <span class="name" itemprop="name">${element.name}</span>
  </a>
  </schema-item>`;

