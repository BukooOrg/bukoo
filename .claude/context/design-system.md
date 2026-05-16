# Bukoo Design System

> **Strict colour palette — no blues, greens, or reds anywhere in the UI.**
> The only exception is `destructive` (error states), which uses a muted red.

---

## Colour System

All colours are defined as HSL values in `frontend/src/styles/globals.css`.
Tailwind uses them via `bg-<token>`, `text-<token>`, `border-<token>`, etc.
Opacity modifiers work: `bg-primary/10`, `text-primary/40`, `border-primary/5`.

| Token | HSL value | Hex | Purpose |
|-------|-----------|-----|---------|
| `--background` | `0 0% 96%` | `#F5F5F5` | Page background (cool off-white) |
| `--foreground` | `31 85% 13%` | `#3F2305` | Default text colour (deep espresso) |
| `--primary` | `31 85% 13%` | `#3F2305` | CTAs, headings, icons, buttons |
| `--primary-foreground` | `45 53% 89%` | `#F2EAD3` | Text on primary backgrounds |
| `--card` | `45 53% 89%` | `#F2EAD3` | Primary surfaces, cards (warm parchment) |
| `--card-foreground` | `31 85% 13%` | `#3F2305` | Text on card surfaces |
| `--secondary` | `45 28% 81%` | `#DFD7BF` | Dividers, secondary surfaces (warm taupe) |
| `--border` | `45 28% 81%` | `#DFD7BF` | Borders, input borders |
| `--input` | `45 28% 81%` | `#DFD7BF` | Input field borders |
| `--ring` | `31 85% 13%` | `#3F2305` | Focus rings |
| `--muted` | `45 28% 50%` | `#A89B7A` | Muted backgrounds (darker taupe) |
| `--muted-foreground` | `31 85% 13%` | `#3F2305` | Muted text (use opacity instead: `text-primary/40`) |
| `--destructive` | `0 84.2% 60.2%` | `#E53E3E` | Error states only |

### Colour Usage Rules

- **Never** use arbitrary hex/rgb colours in Tailwind classes
- **Always** use semantic tokens: `bg-background`, `text-primary`, `border-secondary`
- **Opacity modifiers** are preferred for tints: `bg-primary/5`, `text-primary/40`, `border-primary/10`
- **No blues, greens, or reds** anywhere except `--destructive` for error states
- **Sidebar tokens** (`--sidebar-*`) are unused — do not reference them

---

## Typography

### Fonts

| Font | CSS Variable | Family | Usage |
|------|-------------|--------|-------|
| Serif | `--font-serif` | `'EB Garamond', serif` | Headings, editorial titles, italic quotes |
| Sans | `--font-sans` | `'Inter', system-ui, sans-serif` | Body text, UI elements, labels, inputs |
| Mono | `--font-mono` | `ui-monospace, ...` | Code, technical display |

### Heading Sizes (serif)

| Class | Size | Weight | Usage |
|-------|------|--------|-------|
| `text-5xl` | 48px | `font-black` | Page hero (Register page title) |
| `text-4xl` | 36px | `font-black` | Account page titles |
| `text-3xl` | 30px | `font-black` | Section headings, form page titles |
| `text-2xl` | 24px | `italic` | Empty state messages |
| `text-xl` | 20px | `font-bold` | Card titles, sub-sections |

### Body / UI Sizes (sans)

| Class | Size | Weight | Usage |
|-------|------|--------|-------|
| `text-base` | 16px | `font-bold` | Input text, body paragraphs |
| `text-sm` | 14px | `font-bold` | Secondary text, labels, error messages |
| `text-xs` | 12px | `font-black` | Form labels (uppercase, tracked), badges |
| `text-[10px]` | 10px | `font-black` | Result counts, sort labels |
| `text-[11px]` | 11px | `font-black` | Genre nav links |

### Label Pattern (form fields)

```jsx
<label className='block text-xs font-black uppercase tracking-[0.2em] text-primary/60 pl-1'>
  Field Label
</label>
```

### Line Height

- Use `leading-relaxed` (1.625) on body text and paragraphs
- Headings use default tight leading (`tracking-tighter` for large titles)

---

## Spacing & Layout

### Page Margins

| Context | Class | Value |
|---------|-------|-------|
| Content wrapper | `px-sides` | `var(--padding-sides)` = 2rem (32px) |
| Max content width | `max-w-[1440px]` | 1440px |
| Account content | `max-w-lg` (512px) / `max-w-3xl` (768px) | Narrow forms |
| Form container | `mx-auto` | Centered |

### Section Spacing

| Pattern | Class | Value |
|---------|-------|-------|
| Between sections | `space-y-8` | 32px |
| Between form groups | `space-y-5` | 20px |
| Between tight groups | `space-y-2` | 8px |
| Between inline items | `gap-3` / `gap-4` | 12px / 16px |
| Grid gap | `gap-4` | 16px |

### Vertical Padding

| Context | Class | Purpose |
|---------|-------|---------|
| Storefront pages | `pt-28 md:pt-40` | Offset for fixed header |
| Storefront content | `pb-24` | Bottom padding before footer |
| Form pages | `py-20` | Centered form vertical space |

---

## Borders & Outlines

### Border Radius

| Class | Value | Usage |
|-------|-------|-------|
| `rounded-xl` | 12px | Small cards, badges |
| `rounded-2xl` | 16px | **Inputs, buttons, cards, error boxes** (preferred) |
| `rounded-[40px]` | 40px | Auth page containers |
| `rounded-full` | 50% | Avatars, search bar, pill buttons |

### Border Styles

| Pattern | Class | Usage |
|---------|-------|-------|
| Default border | `border border-border` | Cards, sections |
| Input border | `border border-primary/5` | Inputs (resting) |
| Input focus | `focus:ring-2 focus:ring-primary/10 focus:border-primary/20` | Inputs (active) |
| Input error | `border-destructive/40 focus:border-destructive/20` | Inputs (invalid) |
| Subtle divider | `border-b border-border` | Section separators |
| Card border | `border bg-white/80` | Elevated cards |

### Focus Ring

```
focus:outline-none focus:ring-2 focus:ring-primary/10 focus:border-primary/20
```

---

## Input Fields (RegisterPage Pattern — apply to all forms)

```jsx
<div className='space-y-2'>
  <label className='block text-xs font-black uppercase tracking-[0.2em] text-primary/60 pl-1'>
    Field Label
  </label>
  <div className='relative group'>
    <div className='absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none'>
      <Icon className='w-5 h-5 text-primary/30 group-focus-within:text-primary transition-colors' />
    </div>
    <input
      type='text'
      placeholder='Enter value'
      className='w-full pl-12 pr-4 py-4 bg-white/40 border border-primary/5 rounded-2xl
                 focus:outline-none focus:ring-2 focus:ring-primary/10 focus:border-primary/20
                 transition-all font-sans font-bold'
    />
  </div>
</div>
```

### Input Style Rules

- **Background**: `bg-white/40` (semi-transparent white)
- **Border**: `border-primary/5` (very subtle, barely visible)
- **Padding**: `py-4` (generous vertical)
- **Font**: `font-sans font-bold` (bold text inside inputs)
- **Radius**: `rounded-2xl`
- **Icon**: left-aligned `pl-12`, right-aligned `pr-14` (for toggle buttons)
- **Focus**: ring + border color shift via `group-focus-within`
- **Placeholder**: `text-primary/30` (implicit from border colour)

---

## Buttons (CTA Pattern)

```jsx
<button
  className='w-full py-5 bg-primary text-secondary rounded-2xl font-sans font-bold
             uppercase tracking-[0.2em] shadow-2xl hover:scale-[1.02] active:scale-[0.98]
             transition-all flex items-center justify-center gap-3
             disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100'>
  <Icon className='w-5 h-5' />
  <span>Button Text</span>
</button>
```

### Button Style Rules

- **Background**: `bg-primary` (espresso brown)
- **Text**: `text-secondary` (warm taupe)
- **Padding**: `py-5` (generous)
- **Radius**: `rounded-2xl`
- **Font**: `font-sans font-bold uppercase tracking-[0.2em]`
- **Shadow**: `shadow-2xl`
- **Hover**: `hover:scale-[1.02]`
- **Active**: `active:scale-[0.98]`
- **Disabled**: `disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100`
- **Icon**: always paired with text, `gap-3`

---

## Cards & Surfaces

### Auth / Form Card

```jsx
<div className='max-w-md w-full bg-white/80 backdrop-blur-3xl p-10 md:p-12
               rounded-[40px] border border-white/40 shadow-2xl'>
```

### Content Card

```jsx
<div className='p-6 rounded-2xl border bg-white'>
```

### Error Box

```jsx
<div className='flex items-start gap-3 p-4 duration-300 border bg-destructive/5
               border-destructive/10 rounded-2xl animate-in slide-in-from-top-2'>
  <AlertCircle className='w-5 h-5 text-destructive shrink-0' />
  <p className='text-xs font-bold leading-relaxed text-destructive'>Error message</p>
</div>
```

---

## Page Header Pattern (Account Pages)

```jsx
<div className='text-center'>
  <div className='flex justify-center mb-4'>
    <div className='w-14 h-14 bg-primary/5 rounded-full flex items-center justify-center'>
      <Icon className='w-7 h-7 text-primary' />
    </div>
  </div>
  <h1 className='text-4xl font-serif font-black mb-2 text-primary tracking-tighter'>
    Page Title
  </h1>
  <p className='text-primary/40 font-bold italic text-sm'>
    Subtitle description
  </p>
</div>
```

---

## Background Decorations (Auth Pages)

```jsx
<div className='absolute top-[-10%] left-[-10%] w-[40%] aspect-square bg-secondary/10 rounded-full blur-[120px]' />
<div className='absolute bottom-[-10%] right-[-10%] w-[30%] aspect-square bg-secondary/20 rounded-full blur-[100px]' />
```

---

## Quick Reference: What NOT to Do

- ❌ Never use `bg-blue-*`, `bg-green-*`, `bg-red-*` (except `destructive` for errors)
- ❌ Never use arbitrary colours like `bg-[#123456]`
- ❌ Never use `bg-white` for inputs — use `bg-white/40`
- ❌ Never use `rounded-xl` for inputs — use `rounded-2xl`
- ❌ Never use `py-3` for inputs — use `py-4`
- ❌ Never use normal font weight in inputs — use `font-bold`
- ❌ Never use `border-primary/10` for inputs — use `border-primary/5`
- ❌ Never use `text-sm` for input text — use `text-base`
- ❌ Never skip the icon on form inputs (use left-aligned icon pattern)
- ❌ Never use plain error divs — use AlertCircle + `rounded-2xl` + animation
