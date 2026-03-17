// Jest setup file for DOM testing
require('@testing-library/jest-dom');

// Load lab functions for testing
const fs = require('fs');
const path = require('path');

// Load lab-template.js functions into global scope
const labTemplatePath = path.join(__dirname, '../frontend/js/lab-template.js');
if (fs.existsSync(labTemplatePath)) {
  const labTemplate = fs.readFileSync(labTemplatePath, 'utf8');
  // Execute the lab template code in Node.js context with proper global setup
  const vm = require('vm');
  const context = {
    window: global.window || {},
    document: global.document || {},
    console: global.console,
    global: global
  };
  vm.createContext(context);
  vm.runInContext(labTemplate, context);
  
  // Copy functions to global window
  Object.assign(global.window, context.window);
}

// Mock global objects that might be used in tests
global.fetch = jest.fn();
global.localStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn()
};

// Mock window.locations for navigation tests
delete window.locations;
window.locations = {
  href: 'http://localhost:8080',
  hash: '',
  pathname: '/',
  search: '',
  assign: jest.fn(),
  replace: jest.fn(),
  reload: jest.fn()
};

// Mock console methods to avoid noise in tests
global.console = {
  ...console,
  log: jest.fn(),
  error: jest.fn(),
  warn: jest.fn(),
  info: jest.fn()
};

// Setup for cleanup after each test
afterEach(() => {
  jest.clearAllMocks();
  localStorage.clear();
  document.body.innerHTML = '';
});