/**
 * Jest Setup for Frontend Tests
 * Configures test environment and mocks
 */

// Mock browser APIs
global.File = class File {
    constructor(bits, filename, options = {}) {
        this.bits = bits;
        this.name = filename;
        this.type = options.type || '';
        this.size = bits.reduce((size, bit) => size + bit.length, 0);
    }
};

global.FileReader = class FileReader {
    constructor() {
        this.result = null;
        this.error = null;
        this.readyState = 0;
        this.onload = null;
        this.onerror = null;
    }
    
    readAsDataURL(file) {
        setTimeout(() => {
            this.result = `data:${file.type};base64,${Buffer.from('fake-image-data').toString('base64')}`;
            this.readyState = 2;
            if (this.onload) this.onload({ target: this });
        }, 10);
    }
};

global.FormData = require('form-data');

// Mock fetch
global.fetch = jest.fn();

// Mock CONFIG
global.CONFIG = {
    API_URLS: {
        ORGANIZATION: 'https://test-api.com:8008'
    }
};

// Mock DOM methods
global.Element.prototype.scrollIntoView = jest.fn();

// Setup and teardown
beforeEach(() => {
    fetch.mockClear();
    console.warn = jest.fn();
    console.error = jest.fn();
});

afterEach(() => {
    jest.clearAllMocks();
});