export type strings = string | string[] | undefined | null;

export interface ActivityObject {
  id?: string;
  name: strings;
  summary: strings;
  image: strings;
  email: strings;
}

export function first(strings: strings): string | undefined {
  if (Array.isArray(strings)) return strings[0];
  return strings || undefined;
}