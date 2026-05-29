# Photography Styles — Index

Named photography styles for AI image generation across Silux and Hamed Arab Academy work. Each style is invokable via a `/img-<slug>` slash command.

All styles share the same craft principles (see `workspace/silux/brand/luxury-studio-grammar.md` for the seven prompt levers). What differs per style: subject framing, lighting setup, lens character, backdrop, and the named aesthetic reference.

All styles default to **gpt-image-2** (OpenAI). Nano Banana is a documented fallback only.

## Shipped (V1)

| Slash | File | Use case |
|---|---|---|
| `/img-studio` | `studio-editorial.md` | On-model jewellery, hand-forward, shallow DOF, Calvin Klein / Aesop / COS feel. The default for any on-model render. |
| `/img-portrait` | `documentary-portrait.md` | Founder, ambassador, instructor. Soft daylight, matte plaster wall, single picture frame upper-right, 85mm f/2. Documentary realism over staged scenes. |
| `/img-product` | `product-catalogue.md` | Piece-only on plain backdrop, sharp throughout, Hermès / Cartier / Tiffany card clean. For PDP hero shots, ecatalogue thumbnails. |

## Candidates (not yet built — pick which to add next)

| Slash | Use case | Useful for |
|---|---|---|
| `/img-detail` | Extreme close-up showing texture, hammer marks, stone facets. Macro art-photo register. | Silux Reels openers, journal hero images, IG carousel slide 1. |
| `/img-hand` | Just the hand wearing the piece, no face. Cropped, Tiffany Hardwear / Cartier Love bracelet style. | Tight Reels, IG square posts where face would distract. |
| `/img-lifestyle` | Model in environment (café, garden, atelier desk) with jewellery as part of life. | Email marketing, journal hero, Reels with narrative. |
| `/img-atelier` | Behind-the-bench, jeweller's hands at work, files / wax / CAD screen visible. | Hamed Arab Academy course pages, "how it's made" content. |
| `/img-stilllife` | Piece on draped fabric (velvet, raw silk), single dramatic light, deep shadow. Classic luxury house product still life. | Mappin & Webb pitch artefacts, hero collection cards, print catalogue. |
| `/img-bw` | High-contrast monochrome, moody, often Boucheron campaign register. | Editorial features, journal long-form, anniversary collection pages. |
| `/img-arch` | Piece in a luxury architectural setting (marble corridor, Persian palace ceiling). | Silux brand storytelling, "world of Silux" hero on homepage. |

## How to add a new style

1. Write a new file at `workspace/silux/brand/photography-styles/<slug>.md` using one of the V1 files as a template. Required sections: aesthetic reference, lens, lighting, backdrop, post-grading, anti-patterns, assembly snippet.
2. Write a new slash command at `.claude/commands/img-<slug>.md` that reads the style file, asks for the variables, and fires `gpt_image_client.py`.
3. Append the row to this INDEX.

## Reference

- Full prompt grammar (seven levers + anti-patterns): `workspace/silux/brand/luxury-studio-grammar.md`
- **Subjects library** (ambassadors, founder, instructors with reference images): `workspace/silux/brand/subjects/INDEX.md`. Pair any style with a subject via `--subject <slug>` (e.g. `/img-studio --subject soraya`).
- Image-provider routing (cost / API): `workspace/silux/brand/visual-content-pipeline.md`
- Public mirror of grammar (for the jewellery-design-studio public skill): `D:/01 Projects/jewellery-design-studio/docs/luxury-studio-grammar.md`
