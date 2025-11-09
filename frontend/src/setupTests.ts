// jest-dom adds custom jest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toHaveTextContent(/react/i)
// learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom';

// Polyfill for Node.js environment
import { TextEncoder, TextDecoder } from 'util';

// Make TextEncoder and TextDecoder available globally
global.TextEncoder = TextEncoder;
global.TextDecoder = TextDecoder as any;

// Polyfill for streams
import { ReadableStream, TransformStream, WritableStream } from 'web-streams-polyfill';
global.ReadableStream = ReadableStream;
global.TransformStream = TransformStream;
global.WritableStream = WritableStream;

// Polyfill BroadcastChannel for jest/jsdom environment
// This is required for components that use BroadcastChannel API
// See: https://github.com/pubkey/broadcast-channel
import { BroadcastChannel as BroadcastChannelPolyfill } from 'broadcast-channel';
if (!global.BroadcastChannel) {
  global.BroadcastChannel = BroadcastChannelPolyfill as any;
}

// Polyfill fetch and Response for Node.js environment
import { fetch } from 'whatwg-fetch';

// Mock fetch if needed
if (!global.fetch) {
  global.fetch = fetch;
}

// Mock Response object
if (!global.Response) {
  global.Response = Response;
}

// Mock Request object
if (!global.Request) {
  global.Request = Request;
}

// Mock AbortController
if (!global.AbortController) {
  global.AbortController = AbortController;
}

// Mock AbortSignal
if (!global.AbortSignal) {
  global.AbortSignal = AbortSignal;
}

// Mock Blob
if (!global.Blob) {
  global.Blob = class Blob {
    constructor(parts = [], options = {}) {
      this.parts = parts;
      this.options = options;
    }
  };
}

// Mock File
if (!global.File) {
  global.File = class File {
    constructor(bits, name, options = {}) {
      this.bits = bits;
      this.name = name;
      this.options = options;
    }
  };
}

// Mock FormData
if (!global.FormData) {
  global.FormData = class FormData {
    constructor() {
      this.data = new Map();
    }
    append(name, value) {
      this.data.set(name, value);
    }
  };
}

// Mock URL
if (!global.URL) {
  global.URL = class URL {
    constructor(url) {
      this.url = url;
    }
  };
}

// Mock URLSearchParams
if (!global.URLSearchParams) {
  global.URLSearchParams = class URLSearchParams {
    constructor(init) {
      this.params = new Map();
      if (typeof init === 'string') {
        // Parse query string
        init.split('&').forEach(pair => {
          const [key, value] = pair.split('=');
          if (key) {
            this.params.set(decodeURIComponent(key), decodeURIComponent(value || ''));
          }
        });
      }
    }
  };
}

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
};

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
};

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

// Mock scrollTo
window.scrollTo = jest.fn();

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value.toString();
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
  };
})();
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

// Mock sessionStorage
const sessionStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value.toString();
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
  };
})();
Object.defineProperty(window, 'sessionStorage', {
  value: sessionStorageMock,
});
