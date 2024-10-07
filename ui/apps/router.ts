import { type ReactiveController, type ReactiveControllerHost } from 'lit';

interface Route {
  name: string;
  path: string | URLPattern;
  render?: (params: { [key: string]: string | undefined }) => unknown;
}

export class Router implements ReactiveController {
  private readonly _host: ReactiveControllerHost & HTMLElement;

  _routes: Array<Route> = [];
  _activeParams?: { [key: string]: string | undefined };
  _activeRoute?: Route;
  baseURL?: string;;

  get params() {
    return this._activeParams;
  }

  get route() {
    return this._activeRoute;
  }

  get routes() {
    return this._routes;
  }

  constructor(
    host: ReactiveControllerHost & HTMLElement,
    routes: Array<Route>,
    baseURL?: string
  ) {
    (this._host = host).addController(this);
    this._routes = [...routes];
    this.baseURL = baseURL;
  }

  render() {
    if (this._activeRoute) {
      this._activeRoute.render?.(this._activeParams || {});
    }
  }

  findRoute(input: string | URLPatternInit = {}): Route | undefined {
    return this._routes.find((route) =>
      getPattern(route.path).test(input, this.baseURL)
    );
  }

  hasRoute(input: string | URLPatternInit = {}): boolean {
    return !!this.findRoute(input);
  }

  goto(input: string | URLPatternInit = {}) {
    const route = this.findRoute(input);
    if (route) {
      this._activeRoute = route;
      this._activeParams = getPattern(route.path).exec(input);
      this.render();
    } else {
      this._activeParams = {};
      this._activeRoute = undefined;
    }
  }
}

export interface URLPatternInit {
  baseURL?: string;
  username?: string;
  password?: string;
  protocol?: string;
  hostname?: string;
  port?: string;
  pathname?: string;
  search?: string;
  hash?: string;
}

const patternCache = new Map();
const getPattern = (path: string | URLPattern) => {
  if (path instanceof URLPattern) {
    return path;
  }
  let pattern = patternCache.get(path);
  if (pattern === undefined) {
    patternCache.set(path, (pattern = new URLPattern({ pathname: path })));
  }
  return pattern;
};



export class XRouter extends Routes {
  override hostConnected() {
    super.hostConnected();
    window.addEventListener('click', this._onClick);
    window.addEventListener('popstate', this._onPopState);
    this.goto(window.location.pathname);
  }

  override hostDisconnected() {
    super.hostDisconnected();
    window.removeEventListener('click', this._onClick);
    window.removeEventListener('popstate', this._onPopState);
  }

  private _onClick = (e: MouseEvent) => {
    const isNonNavigationClick = e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey;
    if (e.defaultPrevented || isNonNavigationClick) {
      return;
    }

    const anchor = e
      .composedPath()
      .find((n) => (n as HTMLElement).tagName === 'A') as
      | HTMLAnchorElement
      | undefined;
    if (
      anchor === undefined ||
      anchor.target !== '' ||
      anchor.hasAttribute('download') ||
      anchor.getAttribute('rel') === 'external'
    ) {
      return;
    }

    const href = anchor.href;
    if (href === '' || href.startsWith('mailto:')) {
      return;
    }

    const location = window.location;
    if (anchor.origin !== origin) {
      return;
    }

    // @ts-ignore
    window.c = this;

    e.preventDefault();
    const route = this._getRoute(anchor.pathname);
    if (route === undefined)
      return;

    if (href !== location.href) {
      window.history.pushState({}, '', href);
      this.goto(anchor.pathname);
    }
  };

  protected _onPopState = (_e: PopStateEvent) => {
    this.goto(window.location.pathname);
  };
}

/// URLPattern Polyfill
//@ts-ignore
if (!globalThis.URLPattern) {
  //@ts-ignore
  globalThis.URLPattern = import("urlpattern-polyfill").URLPattern;
}
