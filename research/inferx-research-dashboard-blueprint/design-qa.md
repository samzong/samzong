# Design QA

## Result

passed

## Visual truth

- Source URL: `https://inferx-research-dashboard.pages.dev/`
- Source captures:
  - `../inferx-research-dashboard-recovered/evidence/source/source-desktop-top-1440x900.png`
  - `../inferx-research-dashboard-recovered/evidence/source/source-mobile-top-390x844.png`
  - `../inferx-research-dashboard-recovered/evidence/source/source-desktop-focus-together-menu.jpg`
  - `../inferx-research-dashboard-recovered/evidence/source/source-mobile-image-modal-390x844.jpg`
- Implementation captures:
  - `evidence/implementation/blueprint-desktop-top-1440x900.png`
  - `evidence/implementation/blueprint-mobile-top-390x844.png`
  - `evidence/implementation/blueprint-desktop-together-menu-1280x720.jpg`
  - `evidence/implementation/blueprint-mobile-image-modal-390x844.jpg`
- Side-by-side comparisons:
  - `evidence/comparisons/desktop-top-source-left-blueprint-right.png`
  - `evidence/comparisons/mobile-top-source-left-blueprint-right.png`
  - `evidence/comparisons/desktop-menu-source-left-blueprint-right.png`
  - `evidence/comparisons/mobile-modal-source-left-blueprint-right.png`

## Viewports and states

| Surface | CSS viewport | Pixel size | State |
| --- | ---: | ---: | --- |
| Desktop top | 1440 × 900 | 1440 × 900 | initial page |
| Mobile top | 390 × 844 | 390 × 844 | initial page |
| Desktop menu | 1280 × 720 | source 2560 × 1440 at DPR 2; implementation 1280 × 720 at DPR 1 | Together AI hover menu, `scrollY=61` |
| Mobile modal | 390 × 844 | 390 × 844 | first image preview open |

The desktop menu source capture was normalized to the common 1280 × 720 CSS-pixel density with Lanczos downsampling before comparison. Other comparison pairs required no resampling.

## Evidence

- Desktop top: SSIM `0.989039`, PSNR `31.625195 dB`.
- Mobile top: SSIM `0.983096`, PSNR `29.911991 dB`.
- Desktop menu: SSIM `0.988198`, PSNR `31.559529 dB`.
- Mobile modal: SSIM `1.000000`, PSNR `∞`.
- Desktop full-page scroll: 116 images complete, 0 remote images, 0 broken images.
- Mobile full-page scroll: 116 images complete, 0 remote images, 0 broken images.
- Source and implementation full-page heights match: desktop `29676 px`; mobile `76609 px`.
- Browser console: 0 errors, 0 warnings during desktop and mobile verification.
- Interactions verified: section navigation, top navigation, Together AI dropdown, image modal open and close.

## Fidelity review

- Typography, spacing, layout, color tokens, copy, and responsive breakpoints come from the recovered production CSS and bundle.
- All observed image assets are local. No runtime dependency remains on the original Pages deployment.
- The Blueprint root loads the recovered bundle directly, avoiding an iframe scroll seam and an extra document-load boundary.

## Comparison history

- P1: initial recovery missed the root logo and several late-loaded image URLs. Fixed by collecting the remaining DOM assets and rewriting them to local paths.
- P2: initial Blueprint shell used an iframe, which added a visible scroll seam and made readiness checks race the child document. Fixed by loading the recovered bundle directly from the Blueprint root.
- P0: none.
- Remaining P3: capture-only raster and scrollbar differences at mixed DPR; no product-facing mismatch found.
