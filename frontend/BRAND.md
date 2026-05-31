# IndoGovRAG Brand Guide

**Version:** 1.0 — 2026
**Platform:** IndoGovRAG — Platform Penelusuran Regulasi & Dokumen Hukum Indonesia
**AI-Powered Legal Research for Indonesia**

---

## 1. Brand Overview

IndoGovRAG is the authoritative digital platform for Indonesian legal and regulatory research. The brand identity combines:

- **Government authority** — structured, trustworthy, institutional
- **Indonesian cultural identity** — Garuda-inspired symbolism, Borobudur architectural motifs
- **Modern AI technology** — clean data visualization, RAG retrieval concept
- **Professional clarity** — no fluff, no decoration for decoration's sake

The visual system is designed to work across digital interfaces, print documents, and presentation materials with equal effectiveness.

---

## 2. Color System

### Primary Palette

| Name | Hex | RGB | Usage |
|------|-----|-----|-------|
| Deep Indigo (Primary) | `#3730a3` | 55, 48, 163 | Brand primary, headings, primary UI elements |
| Indigo Dark | `#312e81` | 49, 46, 129 | Deep backgrounds, dark mode, emphasis |
| Indigo Mid | `#4338ca` | 67, 56, 202 | Interactive states, links, focus rings |
| Indigo Light | `#6366f1` | 99, 102, 241 | Secondary accents, borders, subtle highlights |
| Indigo Lighter | `#818cf8` | 129, 140, 248 | Disabled states, placeholder text, very light accents |
| Indigo Pale | `#a5b4fc` | 165, 180, 252 | Subtle fills, light backgrounds |
| Indigo Faint | `#c7d2fe` | 199, 210, 254 | Dividers, very light backgrounds |
| Indigo Ghost | `#e0e7ff` | 224, 231, 255 | Page backgrounds, card backgrounds |

### Accent Palette

| Name | Hex | RGB | Usage |
|------|-----|-----|-------|
| Amber Primary | `#f59e0b` | 245, 158, 11 | Brand accent, CTAs, important highlights, seals |
| Amber Light | `#fbbf24` | 251, 191, 36 | Amber highlights, hover states, secondary accents |
| Amber Dark | `#d97706` | 217, 119, 6 | Active states, pressed buttons |
| Amber Pale | `#fffbe6` | 255, 251, 230 | Soft amber fills, subtle glow origins |
| Amber Faint | `#fef3c7` | 254, 243, 199 | Very light amber backgrounds |

### Neutral Palette

| Name | Hex | RGB | Usage |
|------|-----|-----|-------|
| Text Primary | `#1e293b` | 30, 41, 59 | Body text, primary content |
| Text Secondary | `#64748b` | 100, 116, 139 | Secondary text, labels, metadata |
| Text Tertiary | `#94a3b8` | 148, 163, 184 | Hints, placeholders, disabled text |
| Text Inverse | `#ffffff` | 255, 255, 255 | Text on dark/indigo backgrounds |
| Border Default | `#e2e8f0` | 226, 232, 240 | Card borders, dividers |
| Surface White | `#ffffff` | 255, 255, 255 | Card surfaces, modals |

### Semantic Colors

| Name | Hex | Usage |
|------|-----|-------|
| Success | `#10b981` | Success states, confirmed actions |
| Warning | `#f59e0b` | Warnings (shares amber — use amber contextually) |
| Error | `#ef4444` | Error states, destructive actions |
| Info | `#3b82f6` | Informational states, links |

---

## 3. Typography

### Primary Font Stack

```
'Segoe UI', 'SF Pro Display', 'SF Pro Text', Helvetica Neue, Helvetica, Arial, sans-serif
```

This stack prioritizes native system fonts for optimal performance across all platforms (Windows, macOS, iOS, Android). No web fonts are required — the brand loads instantly on any device.

### Type Scale

| Token | Size | Weight | Usage |
|-------|------|--------|-------|
| `--text-hero` | 48px / 3rem | 800 | Hero headlines |
| `--text-h1` | 36px / 2.25rem | 700 | Page titles |
| `--text-h2` | 28px / 1.75rem | 700 | Section headings |
| `--text-h3` | 22px / 1.375rem | 600 | Card headings, subsection titles |
| `--text-h4` | 18px / 1.125rem | 600 | Component headings |
| `--text-body` | 16px / 1rem | 400 | Body text |
| `--text-sm` | 14px / 0.875rem | 400 | Secondary text, descriptions |
| `--text-xs` | 12px / 0.75rem | 500 | Labels, badges, captions |
| `--text-micro` | 10px / 0.625rem | 600 | Legal fine print, metadata |

### Font Weight Usage

| Weight | Value | Usage |
|--------|-------|-------|
| Bold | 700–800 | Headlines, primary labels, wordmark |
| Semibold | 600 | Subheadings, navigation, emphasis |
| Regular | 400 | Body text, descriptions |
| Medium | 500 | Tags, badges, metadata |

### Line Height

- Headings: `1.1` to `1.2` (tight)
- Body text: `1.5` to `1.6` (comfortable)
- Legal / formal text: `1.7` to `1.8` (generous, readable)

### Letter Spacing

- Brand wordmark (IndoGovRAG): `0.5px`
- Taglines and labels: `1.5px` to `2px`
- ALL-CAPS labels: `2px` to `3px`
- Body text: `0` (default)

---

## 4. Logo Usage Guidelines

### Logo Components

The logo system has three elements used in combination or standalone:

1. **Symbol Mark** — Shield with Garuda eagle silhouette and RAG data stream
2. **Wordmark** — "IndoGovRAG" with amber accent on "RAG"
3. **Subtitle** — "Platform Penelusuran Regulasi & Dokumen Hukum Indonesia"

### Minimum Sizes

| Context | Minimum Width | Notes |
|---------|--------------|-------|
| Website header | 140px | Default full logo |
| App icon / mobile | 32px | Symbol only |
| Favicon | 16px | Simplified favicon-indo.svg |
| Print / document | 60px | Full logo preferred |

### Clear Space

Maintain a minimum clear space around the logo equal to the height of the "R" in the wordmark on all sides.

### Correct Usage

- Always use the provided SVG files — never reconstruct the logo from scratch
- Use `logo.svg` for all standard applications
- Use `favicon-indo.svg` for browser tabs, bookmark icons, PWA icons
- The amber accent on "RAG" must always be amber (`#f59e0b`)
- The shield must always be indigo (`#3730a3` or gradient of `#4338ca` to `#312e81`)

### Incorrect Usage

- Do not change the proportions of the shield mark
- Do not recolor the shield to gray, black, or any color outside the brand palette
- Do not place the logo on a background that has insufficient contrast with indigo
- Do not add drop shadows, outlines, or decorative frames unless explicitly shown in these guidelines
- Do not use the wordmark alone without the shield mark in the favicon or app icon contexts
- Do not stretch or compress the logo

---

## 5. Iconography

### Style Principles

- **Flat design** — No gradients on icons, no 3D effects, no complex shading
- **Geometric precision** — Clean paths, consistent stroke weights, rounded corners where appropriate
- **2px stroke weight** — Standard for all UI icons (line icons)
- **24x24 grid** — All icons align to a 24x24 viewBox
- **Rounded line caps** — `stroke-linecap="round"` on all line icons

### Icon Color

- Default state: `#64748b` (secondary text color)
- Hover/active state: `#3730a3` (brand primary)
- White: `#ffffff` (when on indigo/amber background)
- Disabled: `#94a3b8` at 50% opacity

### Icon Types

| Category | Description | Examples |
|----------|-------------|---------|
| Navigation | Main app navigation | search, document, bookmark, settings |
| Actions | Interactive buttons | upload, download, filter, sort |
| Status | System feedback | check-circle, warning, error, loading |
| Regulation | Legal document types | UU (Undang-Undang), PP (Peraturan Pemerintah), Perpres |

### Legal Document Type Badges

Document type badges follow a consistent system in the brand:

| Document | Badge Style | Color |
|----------|-------------|-------|
| UU (Undang-Undang) | Rectangular tag | Amber `#f59e0b` with white text |
| PP (Peraturan Pemerintah) | Rectangular tag | Amber with border |
| Perpres (Peraturan Presiden) | Rectangular tag | Dark indigo with white text |
| Permen (Peraturan Menteri) | Rectangular tag | Light indigo outline |
| Kepmen (Keputusan Menteri) | Rectangular tag | Light indigo outline |
| Perda (Peraturan Daerah) | Rectangular tag | Amber outline |

---

## 6. Illustration Style

### Legal Art (Hero Illustration)

The `legal-art.svg` illustration uses these principles:

- **Flat design** with limited palette (max 4 colors: indigo, amber, white, and slate grays)
- **Data grid background** — subtle geometric grid to represent digital/legal infrastructure
- **Central open law book** — the primary focal element, with realistic page texture via text lines
- **Borobudur columns** — left and right structural elements referencing Indonesian architecture
- **Floating documents** — representing the RAG retrieval concept, documents emerging from the knowledge base
- **Garuda silhouette** — subtle watermark in background for Indonesian identity
- **Data connection lines** — dashed amber paths connecting the book to retrieved documents
- **Magnifying glass** — representing the RAG (Retrieval Augmented Generation) concept

### Color Usage in Illustrations

- Background: `#f8faff` to `#e0e7ff` (light indigo gradient)
- Columns: `#c7d2fe` to `#a5b4fc` (indigo lighter tones)
- Documents: `#ffffff` with `#c7d2fe` or `#a5b4fc` borders
- Accents: `#f59e0b` (amber) for seals, badges, data nodes
- Text lines: `#94a3b8` (slate gray) at varying opacities
- Section headers in docs: `#312e81` (dark indigo) at lower opacity

---

## 7. Do's and Don'ts

### Do

- Use the official SVG logo files from `/public/logo.svg` and `/public/favicon-indo.svg`
- Use amber (`#f59e0b`) as the accent color in CTAs, badges, and highlights
- Use deep indigo (`#3730a3`) for primary headings and UI elements
- Maintain the amber-on-indigo contrast for the "RAG" text in the wordmark
- Use the legal art illustration (`/public/legal-art.svg`) for homepage hero sections
- Use system fonts via the recommended font stack
- Keep the brand clean — whitespace is your friend

### Don't

- Do not use more than 3 colors as dominant elements in a single UI component
- Do not add gradients to text or icons
- Do not create custom logo variants without design review
- Do not use bright, saturated colors outside the brand palette
- Do not use comic-style, hand-drawn, or decorative fonts
- Do not place logo text over busy photography without a solid background overlay
- Do not animate the logo in ways that alter its proportions or colors
- Do not use the favicon as a full-width hero element — it's designed for 16–64px contexts

---

## 8. Dark Mode Considerations

When IndoGovRAG is rendered in dark mode, the following color mappings apply:

| Light Mode | Dark Mode | Usage |
|------------|-----------|-------|
| `#ffffff` | `#0f172a` | Surfaces, cards |
| `#e0e7ff` | `#1e1b4b` | Page background |
| `#312e81` | `#818cf8` | Text on dark |
| `#f59e0b` | `#fbbf24` | Accent (slightly lighter) |
| `#94a3b8` | `#64748b` | Muted text |

---

## 9. File Reference

| File | Path | Purpose |
|------|------|---------|
| Logo (full) | `/public/logo.svg` | Header, landing pages, print |
| Favicon | `/public/favicon-indo.svg` | Browser tab, PWA, app icon |
| Legal Art | `/public/legal-art.svg` | Homepage hero section |
| Brand Guide | `/BRAND.md` | This document |

---

*IndoGovRAG Brand System v1.0 — Maintained by the platform design team. For questions about brand usage, contact the design team.*