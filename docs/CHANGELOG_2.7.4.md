# Prismo 2.7.4 — 2026-10-09

- Completed English translations for all Settings tabs and Test Lab fixed labels, including the welcome message and mixed Persian/English RAG chat labels.
- Added an FA/EN language switch to the login page and removed the floating light/dark toggle there.
- Added the Prismo SVG app mark and favicon; updated page titles, setup UI, widget credit, admin/dashboard branding, and project documentation.
- Kept user-entered messages and runtime assistant responses out of automatic UI translation while allowing the built-in Test Lab greeting to follow the selected language.
- Bumped frontend asset cache keys to 2.7.4.
- Validation: 208 automated tests pass; static English-mode audit found no untranslated Persian text nodes in Settings, Test Lab, RAG behavior, or widget sections.
