<!-- Source: maintained in Persian CLAW workspace/silux/brand/luxury-studio-grammar.md; mirrored here for the public repo. Edit upstream first. -->

# Luxury Studio Grammar

Canonical prompt grammar for editorial-luxury jewellery imagery via AI image models.

## Bottom line

The quality bar is Calvin Klein / Aesop / COS campaign, not jewellery catalogue. The durable insight: frame the shot as fashion that happens to feature jewellery, not jewellery with a model attached. Every decision below serves that inversion. When the ring is the only fully-resolved element in the frame, surrounded by out-of-focus fabric and soft warm skin, the viewer reaches for it. When a hand holds a ring up at the camera on a marble surface, the viewer scrolls past.

---

## 1. Provider routing

Nano Banana (Gemini 3 Pro Image, `scripts/nano_banana_client.py`) is the primary provider for all editorial on-model jewellery work. It produces accurate real skin texture, fine fabric detail, hand anatomy, and natural light behaviour. Use it for every on-model ring shot, product close-up on skin, ambassador render, and photoreal scene.

gpt-image-2 (OpenAI, `scripts/gpt_image_client.py`) is primary only for typography-heavy outputs: infographs, course cards, social posts with overlay text, posters. It is not the right tool for editorial jewellery imagery.

This extends the routing rule already documented in `workspace/silux/brand/visual-content-pipeline.md` under "Image-provider routing". That section governs cost and API; this doc governs craft. They are both required reading.

---

## 2. Prompt grammar: the seven levers

**Lever 1. Subject framing.** Name who is in the frame, what they are wearing, what jewellery, and what the pose is. The pose must read as natural, not as "presenting" the piece. Cross-legged on the floor, hand resting on a raised knee, ring angled incidentally toward the light. Never: hand extended palm-up, ring held toward camera, fingers spread to show the stone.

**Lever 2. Lens character.** Name the focal length and aperture explicitly. "85mm at f/1.8" or "105mm at f/2" forces telephoto compression, separates the subject from the backdrop, and creates the radical focus hierarchy that makes on-model jewellery work. Wide-angle lenses (50mm or below) kill the compression. Never omit this lever; the model will default to a mediocre mid-range look without it.

**Lever 3. Lighting.** One source. Single soft directional light from upper-left, north-window quality. Rembrandt triangle on the face is acceptable. Soft wrap on the body. Multiple light sources fighting each other create the look of a catalogue shoot; one source creates the look of a documentary portrait. Name it: "single large soft source upper-left".

**Lever 4. Wardrobe, casting, skin.** Wardrobe must be minimalist, unbranded, and unstyled: plain white ribbed cotton tank top, cream cashmere crew, unstructured linen shirt. No logos, no couture silhouettes, no styling. Casting: real skin texture preserved, pores and fine arm hair visible, no makeup beyond brow and light moisturiser. Specify this explicitly because models default to polished, gloss-lipped, contoured faces unless instructed otherwise.

**Lever 5. Surface and backdrop.** Matte plaster wall, cream paper, unstyled plain studio. That is the complete list. Nothing else is acceptable. The backdrop is silence. A silent backdrop focuses every ounce of viewer attention on the piece.

**Lever 6. Post-grading.** Warm, slightly desaturated, lifted mid-tones, gently crushed shadows. "Kodak Portra 400" is a reliable single anchor phrase that encodes this grade. Add: subtle film grain for texture. The grain gives depth and separates the image from the over-sharpened AI-default look.

**Lever 7. Focal hierarchy.** State explicitly what is sharp and what is soft. "Hand razor-sharp, body soft, face very soft." The jewellery piece must be the only fully-resolved element in the frame. This is aperture-driven, not a post-processing blur. Naming the hierarchy in the prompt forces the model to prioritise fidelity where it matters.

---

## 3. What never to include

These choices drag any render into catalogue default. Cut them before generating.

- Strip-light sparkle reflections and diamond starbursts on every facet
- Perfect white seamless backdrop (infinity cyc look)
- Glamour pose: hand extended, palm up, ring "presented" to camera
- Heavy makeup: contoured cheekbones, gloss lips, lined eyes
- Retouched doll-skin smoothness, no pores visible
- Broad dramatic side-light contour (standard fashion-editorial cliché, over-used)
- Any marketing copy, watermarks, or branding in-frame
- Marble surfaces, fresh flowers, draped satin, jewellery boxes, velvet ring trays
- Multiple light sources creating competing shadows
- Wide-angle lens (50mm or shorter): destroys telephoto compression

---

## 4. Two worked examples

### Example A: on-model ring shot

**Before (jewellery-magazine default):** "A beautiful model wearing a gold sapphire ring in a luxurious setting with elegant lighting and a marble background, jewellery photography, high quality, professional."

**After (editorial campaign):** "Brown-skinned woman, mid-20s, athletic build, sleek hair pulled back tight, no flyaways. Plain white ribbed cotton scoop-neck tank top, no branding. Seated cross-legged on floor, leaning slightly forward, right hand resting on raised right knee, hammered yellow gold ring with oval blue sapphire on right ring finger, hand angled naturally, not presented. 85mm at f/1.8, single large soft directional source upper-left, Rembrandt triangle on face. Completely plain warm cream plaster wall, no props, no furniture. Hand razor-sharp, body soft, face very soft. Warm desaturated Kodak Portra 400 grade, lifted mid-tones, subtle film grain, gently crushed shadows."

### Example B: product-only close-up

**Before:** "A gold ring with a blue sapphire on a white background, product photography."

**After:** "Hammered yellow gold signet ring with oval blue sapphire, resting on matte cream paper, no props, no glare. 105mm macro lens at f/4, single large soft top-down source, warm directional, no fill. Ring fully sharp, background falls to soft blur. Warm Kodak Portra 400 grade, lifted mid-tones, subtle film grain. No marble, no velvet, no shadows on the stone."

---

## 5. Quick-reference checklist

Ask these five questions before generating. If any answer is no, fix it first.

1. Have I named a specific focal length and aperture?
2. Have I named one light source, not multiple?
3. Is the wardrobe unbranded, minimal, and unstyled?
4. Have I forbidden marble, flowers, satin, and props?
5. Have I named the focal hierarchy, stating what is sharp and what is soft?

---

*Cross-references: `workspace/silux/brand/visual-content-pipeline.md` (Image-provider routing). Colour-grade anchor: Kodak Portra 400. Aesthetic peer set: Calvin Klein, Aesop, COS.*
