# Product Catalogue

Piece-only, no model, no scene. Sharp throughout. Hermès / Cartier / Tiffany e-commerce card register. The default for PDP hero shots, collection thumbnails, and email marketing piece-features.

Distinct from `studio-editorial` (which is on-model) and `stilllife` (which adds fabric and drama). This is the clean utility shot.

## Aesthetic reference
- Hermès.com product page hero images
- Cartier.com e-commerce thumbnails (white-isolated but with subtle warmth)
- Tiffany.com PDP gallery shots
- Net-a-Porter premium-jewellery card cropping

## Variables to ask the user
- **Piece**: e.g. "hammered yellow gold signet ring with oval blue sapphire"
- **Materials detail**: optional, e.g. "Royal Blue Ceylon sapphire 1.2ct cushion-cut, 18ct yellow gold band 4mm wide"
- **Angle**: default "three-quarter front, slight elevation 15 degrees, piece centred"
- **Backdrop tone**: default "warm off-white cream paper, very subtle gradient darkening to the corners"

## Locked grammar (do not delete from final prompt)
- **Lens**: 105mm macro at f/5.6, sharp throughout the piece (no shallow DOF here — the whole piece must be in focus)
- **Lighting**: single soft top-down source with one soft fill from camera-left, no hard shadows, no glare on the stone
- **Surface**: matte cream paper, never glossy, never reflective, never coloured
- **Post-grading**: warm slightly desaturated, faithful colour rendering on the stone, subtle film grain, no over-saturation, no AI-default punch
- **Composition**: piece occupies 60-70% of frame, centred or rule-of-thirds offset, ample breathing room

## Anti-patterns (forbid in every prompt)
no marble, no velvet, no satin, no flowers, no jewellery box, no hand, no model, no glossy reflective surface, no harsh studio strobe, no specular sparkle on every facet, no diamond-ad starbursts, no coloured backdrop (no black, no navy, no gradient teal), no shallow depth of field that blurs part of the piece, no marketing copy in-frame, no logo overlay

## Default output
- **Size**: 1280x1280 (1:1 square) for collection thumbnails; 1024x1536 (2:3 portrait) for PDP hero
- **Quality**: high
- **Output path**: `outbox/images/product-<YYYY-MM-DD>-<piece-slug>.png`

## Assembly

```bash
python scripts/gpt_image_client.py --action generate \
    --prompt "<assembled prompt>" \
    --size 1280x1280 \
    --quality high \
    --output <output-path>
```

For an existing piece reference (e.g. a Rhino render or a previous AI generation), use edit mode to preserve appearance:

```bash
python scripts/gpt_image_client.py --action edit \
    --prompt "<assembled prompt>" \
    --reference <path-to-locked-piece.png> \
    --size 1280x1280 \
    --quality high \
    --output <output-path>
```

## Worked example
"Hammered yellow gold signet ring with an oval Royal Blue Ceylon sapphire 1.2ct cushion-cut, 18ct yellow gold band 4mm wide, hand-hammered finish on the shank, polished bezel setting on the stone. Three-quarter front angle, slight elevation 15 degrees, piece centred, occupying 65% of frame. Resting on matte warm off-white cream paper with a very subtle gradient darkening to the corners. 105mm macro lens at f/5.6, the entire piece in sharp focus, no shallow depth of field on the band or the stone. Single large soft top-down source with one soft fill from camera-left, no hard shadows, no glare on the stone, faithful sapphire blue colour with the stone's natural depth and crown facets visible. Warm slightly desaturated grade, subtle film grain, no over-saturation. No marble, no velvet, no satin, no flowers, no jewellery box, no hand, no model, no glossy surface, no harsh strobe, no specular sparkle on every facet, no diamond-ad starbursts, no coloured backdrop, no marketing copy in-frame, no logo overlay. Square 1:1 aspect ratio."
