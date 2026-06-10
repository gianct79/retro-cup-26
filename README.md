# Retro Cup 26

A 90s arcade-style tournament tracker and simulator for the 2026 Global Cup, built with **Svelte 5** and **Vite**.

## Features

- **Retro Aesthetic:** High-contrast neon blue theme with 8-bit pixel art flags and cards.
- **Complete Tournament Logic:** Implements the full 48-team tournament structure, including the complex FIFA-compliant 3rd-place allocation rules.
- **Local-First Persistence:** All scores and predictions are automatically saved to the browser's local storage.
- **Bilingual UI:** Full support for English and Portuguese.
- **Advanced Filtering:** View matches by specific date or venue.

## Getting Started

### Prerequisites

- Node.js (v18 or higher)
- npm

### Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   npm install
   ```

## Development

To start the development server with Hot Module Replacement (HMR):

```bash
npm run dev
```

## Production

To create an optimized production build:

```bash
npm run build
```

The build output will be located in the `dist/` directory, ready to be deployed to Netlify, Vercel, or GitHub Pages.

## Technical Stack

- **Framework:** Svelte 5 (utilizing Runes for high-performance reactivity)
- **Bundler:** Vite
- **Styling:** Custom CSS with advanced pixelated rendering techniques

## Maintenance & Tooling

### Sprite Generation
The flag spritesheet located in `public/flags-sprite.png` is generated from individual flag assets. The source images and the generation script are located in the `tools/flags` directory.

To update the spritesheet:
1. Add/update PNG flags in `tools/flags/source`.
2. Run the Python generator script: `python tools/flags/generate_sprite.py`.

## License

This project is licensed under the MIT License - see the LICENSE.txt file for details.
