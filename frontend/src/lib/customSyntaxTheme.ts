// /src/lib/customSyntaxTheme.ts

export const customTheme = {
  'code[class*="language-"]': {
    color: 'var(--foreground)',
    background: 'none',
    fontFamily: 'var(--font-mono)',
    fontSize: '13px',
    lineHeight: '1.6',
    textShadow: 'none',
  },
  'pre[class*="language-"]': {
    color: 'var(--foreground)',
    background: 'var(--card)',
    padding: '1rem 0',
    margin: '0',
    overflow: 'auto',
  },

  // Keywords (const, class, return)
  '.token.keyword': {
    color: 'var(--primary)',
    fontWeight: 500,
  },

  // Strings
  '.token.string': {
    color: 'oklch(0.75 0.13 140)', // green-ish
  },

  // Comments
  '.token.comment': {
    color: 'var(--muted-foreground)',
    fontStyle: 'italic',
  },

  // Numbers
  '.token.number': {
    color: 'oklch(0.8 0.15 200)',
  },

  // Function names
  '.token.function': {
    color: 'oklch(0.75 0.1 260)', // violet-ish
  },

  // Variables & params
  '.token.variable': {
    color: 'var(--foreground)',
  },

  // Operators (+, =, =>)
  '.token.operator': {
    color: 'var(--foreground)',
  },

  // Punctuation ({ } , ;)
  '.token.punctuation': {
    color: 'var(--muted-foreground)',
  },

  // Boolean / null / undefined
  '.token.boolean': {
    color: 'oklch(0.7 0.16 35)', // gold
  },
};
