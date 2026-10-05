# DESIGN.md: UI / UX Design System

Defines how the app looks and feels. The frontend must use these tokens. **Do not invent new colors, fonts, or spacing values.**

---

## 1. Design principles
1. **Developer-tool feel:** clean, dense but readable, calm. Think GitHub / Linear / Vercel.
2. **Evidence first:** file paths and code-like text are visually distinct (monospace chips).
3. **One clear action per screen:** the URL box on home; the report on results.
4. **Honest states:** warnings, partial results, and low confidence are always visible, never hidden.
5. **Dark by default**, light mode supported.

## 2. Color tokens

Define as CSS variables on `:root` and `[data-theme="light"]`; map them in the Tailwind config.

### Dark (default)
| Token | Hex | Use |
|---|---|---|
| `--bg` | `#0B0F17` | Page background |
| `--surface` | `#121826` | Cards, panels |
| `--surface-2` | `#1A2234` | Hover, nested surfaces, code chips |
| `--border` | `#263046` | Borders, dividers |
| `--text` | `#E6EAF2` | Primary text |
| `--text-muted` | `#93A0B8` | Secondary text |
| `--primary` | `#6C8CFF` | Primary buttons, links, focus ring |
| `--primary-hover` | `#8AA3FF` | Hover state |
| `--accent` | `#2DD4BF` | Highlights, success accents |
| `--success` | `#34D399` | Success |
| `--warning` | `#FBBF24` | Warnings, partial analysis |
| `--danger` | `#F87171` | Errors |

### Light
| Token | Hex |
|---|---|
| `--bg` | `#F7F8FB` |
| `--surface` | `#FFFFFF` |
| `--surface-2` | `#EEF1F7` |
| `--border` | `#D9DFEB` |
| `--text` | `#0F172A` |
| `--text-muted` | `#5B6780` |
| `--primary` | `#3B5BDB` |
| `--primary-hover` | `#2F4AC0` |
| `--accent` | `#0D9488` |
| `--success` | `#059669` |
| `--warning` | `#B45309` |
| `--danger` | `#DC2626` |

Rules: text/background contrast at least 4.5:1. Never use color alone to convey status (add an icon or label).

## 3. Typography
| Role | Font | Fallback |
|---|---|---|
| UI / body | **Inter** | system-ui, sans-serif |
| Code, file paths, tech chips | **JetBrains Mono** | ui-monospace, monospace |

| Style | Size / Line height | Weight |
|---|---|---|
| H1 (hero) | 40px / 48px (mobile 30/38) | 700 |
| H2 (section) | 24px / 32px | 600 |
| H3 (card title) | 18px / 26px | 600 |
| Body | 15px / 24px | 400 |
| Small / meta | 13px / 20px | 400 |
| Code / path | 13px / 20px | 500 |

## 4. Spacing, radius, shadow
- Spacing scale (px): 4, 8, 12, 16, 24, 32, 48, 64
- Radius: 8px (inputs, chips), 12px (cards), 999px (pills)
- Shadow (cards, dark): `0 1px 0 rgba(255,255,255,0.03) inset, 0 8px 24px rgba(0,0,0,0.25)`
- Max content width: 1100px; page padding 24px (mobile 16px)
- Border: 1px solid `--border`

## 5. Layout

### Home
- Centered hero: H1 "Understand any GitHub repo in seconds", one-line subtitle
- Large URL input (56px tall) + Analyze button; below it, 3 example repo chips
- Under the input: a small note on limits ("Public repos only")

### Report page
1. Sticky header: repo name, stars, license, branch, commit SHA (mono), buttons (Copy MD, Download JSON, Re-analyze)
2. Warnings banner (if any), then confidence badge
3. Summary card
4. Tech stack grid (cards by category, items as chips)
5. Architecture: pattern + component list (left), Mermaid diagram (right, pan/zoom)
6. Workflow: numbered steps with evidence chips
7. Key files, API endpoints (searchable table), env variables, how to run (copyable code blocks)
8. Metrics panel
9. Strengths / weaknesses / risks (three columns, stacked on mobile)
10. Chat: right-side drawer on desktop, bottom sheet on mobile

## 6. Components

| Component | Spec |
|---|---|
| Primary button | `--primary` bg, white text, 44px tall, radius 8px, focus ring 2px `--primary` offset 2px |
| Secondary button | transparent, 1px `--border`, `--text` |
| Input | `--surface`, 1px `--border`, focus ring `--primary` |
| Card | `--surface`, border, radius 12px, padding 24px |
| Tech chip | `--surface-2`, mono 13px, radius 8px, optional icon |
| Evidence chip | mono, truncated middle path, tooltip shows full path, click copies |
| Badge | pill; colors: success, warning, danger, neutral |
| Progress stages | horizontal stepper; current stage pulses; done = check icon |
| Confidence badge | 0 to 1 shown as High / Medium / Low with percentage |
| Toast | bottom-right, 4s, used for copy / export feedback |
| Skeleton | `--surface-2` shimmer, matches final layout |

## 7. States (every async component needs all four)
- **Loading:** skeletons plus progress stages
- **Empty:** helpful message ("Not detected") instead of blank space
- **Error:** icon, friendly message, Retry button if `retryable`
- **Success:** the content

## 8. Error message map
| Code | Message shown |
|---|---|
| `INVALID_URL` | "That doesn't look like a GitHub repository URL. Try `owner/repo`." |
| `REPO_NOT_FOUND` / `REPO_PRIVATE` | "We couldn't find this repo. It may be private or misspelled. Only public repos are supported." |
| `REPO_EMPTY` | "This repository is empty." |
| `REPO_TOO_LARGE` | "This repo is very large. We analyzed a partial view." |
| `GITHUB_RATE_LIMITED` | "GitHub is limiting requests. Try again in a few minutes." |
| `LLM_FAILED` | "AI analysis is unavailable. Showing detected facts only." |
| `TIMEOUT` | "This took too long. Try again." |
| `RATE_LIMITED` | "You've reached the hourly limit. Try again later." |
| `INTERNAL` | "Something went wrong on our side. Try again." |

## 9. Motion
- Duration 150 to 200 ms, ease-out. Only fade/slide on panels and toasts.
- Respect `prefers-reduced-motion`.

## 10. Accessibility
- All interactive elements keyboard reachable with visible focus
- ARIA labels on icon buttons; `aria-live="polite"` for progress and toasts
- Diagram has a text alternative (the component list)
- Minimum touch target 44px

## 11. Responsive breakpoints
Mobile under 640px (single column), tablet 640 to 1024px, desktop above 1024px.

## 12. Icons and tone
- Icon set: **lucide-react**
- Tone: direct and plain. No hype, no emojis in the UI.
