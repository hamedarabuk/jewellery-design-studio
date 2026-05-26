# On-model prompt template

See `docs/luxury-studio-grammar.md` for the full grammar. This template embeds
the seven levers as named slots. Fill every slot before generating. Do not delete
the locked grammar block.

---

## Slots

- `{{SUBJECT_DESCRIPTION}}` — e.g. "brown-skinned woman, mid-20s, athletic build, sleek hair pulled back tight, no flyaways"
- `{{WARDROBE}}` — e.g. "plain white ribbed cotton scoop-neck tank top, no branding"
- `{{POSE}}` — e.g. "seated cross-legged on floor, leaning slightly forward, right hand resting on raised right knee"
- `{{PIECE_DESCRIPTION}}` — e.g. "hammered yellow gold signet ring with oval blue sapphire"
- `{{PLACEMENT}}` — e.g. "right ring finger, hand angled naturally, not presented"
- `{{BACKDROP_TONE}}` — e.g. "completely plain warm cream plaster wall, no props, no furniture"

---

## Locked grammar (do not delete from the final assembled prompt)

- **Lens:** 85mm at f/1.8, telephoto compression, very shallow depth of field
- **Lighting:** single large soft directional source upper-left, north-window quality, Rembrandt triangle on face
- **Skin:** real texture preserved, pores and fine arm hair visible, no makeup beyond brow and light moisturiser
- **Focal hierarchy:** hand razor-sharp, body soft, face very soft. Aperture-driven, not Photoshop-driven.
- **Post-grading:** warm desaturated Kodak Portra 400 grade, lifted mid-tones, subtle film grain, gently crushed shadows
- **NEVER:** marble, flowers, satin, props, perfect white seamless backdrop, glamour pose, heavy makeup, doll-skin smoothness, strip-light sparkle, diamond-ad starbursts, hand-extended-toward-camera, marketing copy in-frame, multiple competing light sources

---

## Assembly

Concatenate slots and locked grammar into one paragraph, then send to Nano Banana:

```bash
python scripts/nano_banana_client.py --action generate \
    --prompt "<assembled prompt>" \
    --aspect 4:5 \
    --size 1280x1600 \
    --output brands/<slug>/proposed/<piece>/on-model.png
```

For the approved on-model render (step 8 of the skill), pass the locked front render as a reference to preserve the piece's appearance:

```bash
python scripts/nano_banana_client.py --action generate \
    --prompt "<assembled prompt>" \
    --reference brands/<slug>/approved/<NN>-<piece>/render-front.png \
    --aspect 4:5 \
    --size 1280x1600 \
    --output brands/<slug>/approved/<NN>-<piece>/render-on-model.png
```

---

## Worked example (filled-in template)

"Brown-skinned woman, mid-20s, athletic build, sleek hair pulled back tight, no flyaways. Plain white ribbed cotton scoop-neck tank top, no branding. Seated cross-legged on floor, leaning slightly forward, right hand resting on raised right knee, hammered yellow gold ring with oval blue sapphire on right ring finger, hand angled naturally, not presented. Completely plain warm cream plaster wall, no props, no furniture. 85mm at f/1.8, single large soft directional source upper-left, north-window quality, Rembrandt triangle on face. Real skin texture preserved, pores and fine arm hair visible, no makeup beyond brow and light moisturiser. Hand razor-sharp, body soft, face very soft. Warm desaturated Kodak Portra 400 grade, lifted mid-tones, subtle film grain, gently crushed shadows. No marble, no flowers, no satin, no props, no glamour pose, no strip-light sparkle, no diamond-ad starbursts, no marketing copy in-frame, no multiple competing light sources, portrait 4:5 aspect ratio."

*(This is the "After" example from `docs/luxury-studio-grammar.md` Example A, assembled into one paragraph.)*

---

## Checklist before generating

1. Have I named a specific focal length and aperture?
2. Have I named one light source only?
3. Is the wardrobe unbranded, minimal, and unstyled?
4. Have I forbidden marble, flowers, satin, and props?
5. Have I named the focal hierarchy (what is sharp, what is soft)?

All five must be yes before submitting to Nano Banana.
