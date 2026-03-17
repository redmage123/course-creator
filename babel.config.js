/**
 * Babel Configuration for Jest Testing
 *
 * Purpose: Configure Babel to transpile ES6+ JavaScript for Jest tests
 * Why: Jest needs ES6 modules converted to CommonJS for Node.js environment
 */
module.exports = {
  presets: [
    [
      '@babel/preset-env',
      {
        targets: {
          node: 'current',
        },
      },
    ],
  ],
  env: {
    test: {
      presets: [
        [
          '@babel/preset-env',
          {
            targets: {
              node: 'current',
            },
          },
        ],
      ],
    },
  },
};
