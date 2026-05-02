// @ts-nocheck
import js from '@eslint/js';
import perfectionist from 'eslint-plugin-perfectionist';
import prettierPlugin from 'eslint-plugin-prettier';
import globals from 'globals';

const prettierBaseConfig = {
  $schema: 'https://json.schemastore.org/prettierrc',
  singleQuote: true,
  jsxSingleQuote: true,
  semi: true,
  printWidth: 100,
  tabWidth: 2,
  bracketSpacing: true,
  trailingComma: 'es5',
  bracketSameLine: true,
  useTabs: false,
  endOfLine: 'auto',
  arrowParens: 'always',
  overrides: [],
};

export default [
  {
    ignores: ['dist', 'node_modules', '.next', 'out', 'public', '**/*.min.js', '.cache'],
  },

  js.configs.recommended,

  // Default: ESM browser files (src/)
  {
    files: ['**/*.js', '**/*.jsx', '**/*.mjs'],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: 'module',
      parserOptions: {
        ecmaFeatures: { jsx: true },
      },
      globals: {
        ...globals.browser,
        ...globals.es2021,
        process: 'readonly',
      },
    },
  },

  // vite.config.js is ESM but Vite injects __dirname/__filename via its CJS compat shim
  {
    files: ['vite.config.js'],
    languageOptions: {
      globals: {
        __dirname: 'readonly',
        __filename: 'readonly',
      },
    },
  },

  // CJS config files that use module.exports (not ESM)
  {
    files: ['tailwind.config.js', 'postcss.config.js', '**/*.cjs'],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: 'commonjs',
      globals: {
        ...globals.node,
      },
    },
  },

  {
    plugins: {
      prettier: prettierPlugin,
    },
    rules: {
      ...prettierPlugin.configs.recommended.rules,
      'prettier/prettier': ['error', prettierBaseConfig],
      'arrow-body-style': 'off',
      'prefer-arrow-callback': 'off',
      'no-unused-vars': [
        'warn',
        { argsIgnorePattern: '^_', varsIgnorePattern: '^_|^React$', ignoreRestSiblings: true },
      ],
    },
  },

  {
    plugins: {
      perfectionist,
    },
    files: ['**/*.js', '**/*.jsx', '**/*.cjs', '**/*.mjs'],
    rules: {
      'perfectionist/sort-imports': [
        'error',
        {
          type: 'alphabetical',
          order: 'asc',
          fallbackSort: { type: 'unsorted' },
          ignoreCase: true,
          specialCharacters: 'keep',
          internalPattern: ['^~/.+', '^@/.+'],
          partitionByComment: false,
          partitionByNewLine: false,
          newlinesBetween: 1,
          groups: [
            'type-import',
            'value-builtin',
            'value-external',
            'type-internal',
            'value-internal',
            ['value-parent', 'type-parent'],
            ['value-sibling', 'type-sibling'],
            ['value-index', 'type-index'],
            'ts-equals-import',
            'unknown',
          ],
          customGroups: [],
          environment: 'node',
        },
      ],
      'perfectionist/sort-exports': [
        'error',
        {
          type: 'alphabetical',
          order: 'asc',
          fallbackSort: { type: 'unsorted' },
          ignoreCase: true,
          specialCharacters: 'keep',
          partitionByComment: false,
          partitionByNewLine: false,
          newlinesBetween: 'ignore',
          groups: [],
          customGroups: [],
        },
      ],
    },
  },
];
