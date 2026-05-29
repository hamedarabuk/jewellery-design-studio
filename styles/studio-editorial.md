# Studio Editorial

The default on-model jewellery style. Calvin Klein / Aesop / COS register. Fashion that happens to feature jewellery, not jewellery with a model attached.

Full grammar: `workspace/silux/brand/luxury-studio-grammar.md`.

## Aesthetic reference
- Calvin Klein campaign photography (mid-2010s and later)
- Aesop product environment shots
- COS lookbook (minimalist sportswear era)

## Variables to ask the user
- **Subject**: prefer an ambassador via `--subject <slug>` (see `subjects/INDEX.md`). For on-model jewellery use Yasmin (glamorous hero) or Eleanor (persona-true buyer). If describing freehand, stay on-persona: e.g. "British woman, early 50s, warm chestnut hair with grey, green eyes" (Eleanor register).
- **Wardrobe**: e.g. "fine camel cashmere crew" or "forest-green wool jumper" (considered neutral luxury, never branded)
- **Pose**: e.g. "seated cross-legged on floor, leaning slightly forward, right hand on raised knee"
- **Piece**: e.g. "hammered yellow gold signet ring with oval blue sapphire"
- **Placement**: e.g. "right ring finger, hand angled naturally, not presented"
- **Backdrop tone**: default "completely plain warm cream plaster wall"

## Locked grammar (do not delete from final prompt)
- **Lens**: 85mm at f/1.8, telephoto compression, very shallow depth of field
- **Lighting**: single large soft directional source upper-left, north-window quality, soft Rembrandt fall-off on face
- **Skin**: real texture preserved, pores and fine arm hair visible, no makeup beyond brow and light moisturiser
- **Focal hierarchy**: hand razor-sharp, body soft, face very soft. Aperture-driven, not Photoshop-driven.
- **Post-grading**: warm desaturated Kodak Portra 400 grade, lifted mid-tones, subtle film grain, gently crushed shadows

## Anti-patterns (forbid in every prompt)
no marble, no flowers, no satin, no props, no perfect white seamless backdrop, no glamour pose, no heavy makeup, no doll-skin smoothness, no strip-light sparkle, no diamond-ad starbursts, no hand-extended-toward-camera, no marketing copy in-frame, no multiple competing light sources

## Default output
- **Size**: 1280x1600 (4:5 portrait)
- **Quality**: high
- **Output path**: `outbox/images/studio-<YYYY-MM-DD>-<short-slug>.png`

## Assembly

```bash
python scripts/gpt_image_client.py --action generate \
    --prompt "<assembled prompt>" \
    --size 1280x1600 \
    --quality high \
    --output <output-path>
```

For an existing piece reference (e.g. a locked product render), use edit mode:

```bash
python scripts/gpt_image_client.py --action edit \
    --prompt "<assembled prompt>" \
    --reference <path-to-locked-piece.png> \
    --size 1280x1600 \
    --quality high \
    --output <output-path>
```

## Worked example
"British woman in her early 50s, warm chestnut hair with natural grey softly swept back, green eyes, warm complexion with freckles kept (Eleanor, the Cultural Curator). Fine camel cashmere crew. Seated at a plain table, leaning slightly forward, right hand resting near her cheek, hammered yellow gold ring with an oval Persian turquoise cabochon on her right ring finger, hand angled naturally, not presented. Completely plain warm cream plaster wall, no props, no furniture. 85mm at f/1.8, single large soft directional source upper-left, north-window quality, soft Rembrandt fall-off on face. Real skin texture preserved, pores and fine lines visible, minimal makeup. Hand razor-sharp, body soft, face soft. Warm desaturated Kodak Portra 400 grade, lifted mid-tones, subtle film grain, gently crushed shadows. No marble, no flowers, no satin, no props, no glamour pose, no strip-light sparkle, no diamond-ad starbursts, no marketing copy in-frame, no multiple competing light sources. Portrait 4:5 aspect ratio."

For the glamorous launch and campaign-hero register, use `--subject yasmin` instead (early 30s, luminous, Caspian-teal silk, beauty-campaign lighting).
