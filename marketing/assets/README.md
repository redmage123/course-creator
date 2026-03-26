# TechUni Course Creator — Marketing Visual Assets

Generated: 2026-03-24 | Brand Designer

## Asset Inventory

| File | Dimensions | Format | Use |
|------|-----------|--------|-----|
| `hero-image.svg` | 1200×628px | SVG | Landing page hero, OG/social share image |
| `icon-ai-generation.svg` | 128×128px | SVG | Feature icon: AI Course Generation |
| `icon-docker-labs.svg` | 128×128px | SVG | Feature icon: Docker Lab Environments |
| `icon-org-management.svg` | 128×128px | SVG | Feature icon: Organization Management |
| `social-linkedin.svg` | 1200×627px | SVG | LinkedIn post template (stat posts) |
| `social-twitter.svg` | 1200×675px | SVG | Twitter/X post template (stat posts) |
| `pricing-table.svg` | 900×520px | SVG | Pricing comparison: Free / Growth / Enterprise |
| `email-header.svg` | 600×180px | SVG | Email drip sequence header |

## Brand Tokens Used

| Token | Value | Role |
|-------|-------|------|
| Primary | `#2196F3` → `#1565C0` | Blue gradient, buttons |
| Secondary | `#7C4DFF` | Purple accent |
| Accent Green | `#10B981` | Success, live indicators |
| Accent Orange | `#F97316` | Warnings, drafts |
| Dark BG | `#0D47A1` → `#311B92` | Hero/social backgrounds |
| Font | Inter (system fallback: Arial) | All text |

## Editing the Social Templates

Both `social-linkedin.svg` and `social-twitter.svg` are templated:

- Replace `STAT` text node with the actual number (e.g. `45s`, `98%`)
- Replace `HEADLINE TEXT HERE` with the post stat line
- Replace supporting detail line for each campaign

The Twitter template ships with the "43 hours → 45 seconds" layout pre-composed
as a reference; swap values directly in the SVG text nodes.

## Icon Sizes

All icons render cleanly at:
- **64×64px** — sidebar / feature list
- **128×128px** — feature cards
- **256×256px** — hero feature section

## Export to PNG (if needed)

```bash
# Requires Inkscape
inkscape --export-type=png --export-width=1200 hero-image.svg

# Or using rsvg-convert
rsvg-convert -w 1200 hero-image.svg -o hero-image.png
```

## Notes

- All assets use SVG so they scale to any resolution without quality loss.
- Fonts load from Google Fonts (Inter) in browser contexts; fall back to Arial in email clients.
- For email use, export `email-header.svg` to PNG at 600px wide (email clients have limited SVG support).
