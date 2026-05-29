# Documentary Portrait

Founder, ambassador, instructor, or any single subject head-and-shoulders. Documentary realism, not staged scene. Proven on the Hamed Arab Academy homepage hero (2026-05-27, v2).

The lesson from that iteration: atelier backdrops read fake at AI-generation scale. Plain surfaces + soft daylight + shallow DOF read credible.

## Aesthetic reference
- Leica 85mm f/2 editorial portraits (Magnum-style documentary)
- New Yorker contributor portraits
- Founder portraits in Monocle and FT Weekend Magazine

## Variables to ask the user
- **Subject reference photo**: a real photo of the person to seed the edit (REQUIRED — this is an edit endpoint, not generate)
- **Subject wardrobe**: e.g. "navy pinstripe suit and white shirt" (preserve from reference if not specified)
- **Subject mood**: e.g. "calm, slight smile, eyes to camera"
- **Backdrop tone**: default "warm putty plaster wall, single dark wooden picture frame faintly out of focus upper-right"

## Locked grammar (do not delete from final prompt)
- **Lens**: Leica 85mm at f/2, telephoto compression, shallow depth of field
- **Lighting**: soft natural daylight from camera-left, no studio lights, no harsh fill, north-window quality
- **Skin**: real texture preserved, pores and laugh lines visible, no retouching, no makeup
- **Focal hierarchy**: subject's eyes razor-sharp, shoulders soft, background completely out of focus
- **Post-grading**: warm slightly desaturated, lifted mid-tones, slight film grain, subtle warmth in skin tones
- **Frame**: head-and-shoulders or three-quarter, centred or slightly off-centre, never tight close-up

## Anti-patterns (forbid in every prompt)
no studio strobes, no ring lights, no clean white seamless backdrop, no fake atelier props (no rolling mills, no jewellers' hammers, no fake desks), no styled scene, no aggressive contour shadows, no cinematic dramatic key light, no high-key beauty lighting, no perfect doll-skin smoothness, no styled hair flyaways, no marketing copy in-frame

## Default output
- **Size**: 1024x1536 (2:3 portrait, matches editorial magazine page proportions)
- **Quality**: high
- **Action**: `edit` (subject reference required to preserve likeness)
- **Output path**: `outbox/images/portrait-<YYYY-MM-DD>-<short-slug>.png`

## Assembly

```bash
python scripts/gpt_image_client.py --action edit \
    --prompt "<assembled prompt>" \
    --reference <path-to-subject-photo.jpg> \
    --size 1024x1536 \
    --quality high \
    --output <output-path>
```

## Worked example
"Documentary editorial portrait of the man in the reference image. Preserve the face, the navy pinstripe suit, the white shirt, the bald head, the trimmed beard, and the rose-gold watch. Reframe him into a warm putty plaster wall environment, single dark wooden picture frame faintly out of focus upper-right. Soft natural daylight from camera-left, no studio lights, north-window quality. Real skin texture preserved, pores and laugh lines visible, no retouching. Leica 85mm at f/2, shallow depth of field, eyes razor-sharp, shoulders soft, background completely out of focus. Warm slightly desaturated grade, lifted mid-tones, subtle film grain. Head-and-shoulders frame, three-quarter angle, calm expression with slight smile. No studio strobes, no ring lights, no fake atelier props, no styled scene, no aggressive shadows, no doll-skin smoothness, no marketing copy in-frame."
