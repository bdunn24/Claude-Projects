---
name: brand
description: PhoenixTeam house style for any page, deck or document built in this sandbox. Use before styling anything a reader sees.
---

# PhoenixTeam brand kit (interim)

Source: measured from the Value Engineering Textbook (see assets/SOURCES.md) on 2026-11-18 by
counting the fonts and fill colors in its page streams. The textbook names "the
tokens, the house style" as a pipeline station and the brand kit as a skill, but
prints no token list. Replace this file with the official kit when it arrives
(open question: brand assets in the build kit, textbook Part 2).
Set by Brit Dunn, 2026-11-18.

## Type
- Family: **Sofia Pro** (Light 300, Regular 400, SemiBold 600). Licensed; not on Google Fonts.
- Stack: `"Sofia Pro", "Figtree", system-ui, sans-serif`. Figtree loads from Google Fonts as the stand-in.
- Code and test IDs: `"JetBrains Mono", ui-monospace, Consolas, monospace`.
- Eyebrows: uppercase, SemiBold, letter-spacing 0.1em, in orange.

## Color
| Token | Hex | Use |
|---|---|---|
| navy | #0e1f3f | mastheads, section pages, primary buttons (light) |
| ink | #1b2233 | body text |
| orange | #f47823 | the Phoenix accent: rules, eyebrows on navy, primary button (dark) |
| orange-deep | #b8471a | orange text on light grounds |
| slate | #5b6474 | secondary text |
| grey | #8c94a3, #a7afbe, #c9cfda | muted text, strong lines |
| line | #e3e5ea | hairlines |
| paper | #f5f6f8, #ffffff | page and surface |
| terminal | #050806 ground, #00ff41 text | terminal and code illustrations only |

Status colors stay semantic and apart from the brand accent: pass green, fail
red, blocked amber, in progress blue. Never use orange for a status.

## Page conventions
- A navy masthead with a 4px orange top rule.
- A footer stamp: `PhoenixTeam · <area> · <version> · <date> · <classification>`.
- Every page names its as-of date and its version.
- Words follow CLAUDE.md Style and pass ./check.sh.
