---
name: design-from-reference
description: Take a reference image from a luxury jewellery brand and produce a derived original design, IP-safe, in the user's brand voice. Renders via gpt-image-2, sends preview, graduates to approved on user approval.
model: sonnet
---

# design-from-reference

## Purpose

Generate an original jewellery design inspired by a reference image (e.g. a Harry Winston necklace, a Boucheron animal brooch). The design must match the reference's level of richness while being clearly original (IP-safe). Renders are produced with gpt-image-2, previewed via Telegram or local file, and graduate to an `approved/` folder on user sign-off.

This is the workhorse skill of jewellery-design-studio. It is invoked every time the user sends a new reference image.

## When to invoke

Invoke when one of these is true:

- The user attaches a reference image and asks for a derived design, e.g. "design the next piece from this," "make me a Hamed Arab version of this," "next reference."
- The user explicitly invokes the skill: "design-from-reference, brand=mappin-webb-collection-01, tier=high-jewellery."

If no foundation exists at `brands/<brand_slug>/foundation.md`, ask the user to run `brand-init` first.

## Inputs

Required:

- `reference_image`: a local file path or an inline image attachment from the user.
- `brand_slug`: the brand to design for. If unspecified, ask. If only one brand exists in `brands/`, default to it.

Optional:

- `tier`: "high-jewellery" or "commercial" or "signature". Reads the brand foundation for which bands apply. If absent, infer from the reference image (typical signal: pavé density, multi-cut complexity, scale on model).
- `category`: ring, pendant, brooch, earrings, bracelet, necklace. Inferred from the reference if absent.
- `piece_slug`: override the generated slug. Default: ask the user for a piece name after proposing one in step 4.

## Protocol

### 1. Pre-flight

- Verify the brand foundation exists. If not, stop and instruct the user to run `brand-init`.
- Read `brands/<brand_slug>/foundation.md` into context. Especially: stone palette (allowed, banned), metal palette, naming convention, cultural anchor, IP-safe transformation rule, render defaults, reference and anti-reference houses.
- Determine the next piece slug. If the user has not supplied one, defer slug assignment until after step 4 (where the piece is named).

### 2. Save the reference image

Save the reference to `brands/<brand_slug>/proposed/<piece_slug>/reference-source.png` (or whatever extension matches). If the slug is not yet known, use a temporary working directory `brands/<brand_slug>/proposed/_inbox-<timestamp>/` and rename later.

### 3. Write reference.md (DNA analysis)

Use `templates/reference-template.md` as the layout. Fill these sections:

- **Source**: brand attribution if known, "supplied by user" if not. Tier and indicative retail of the reference if identifiable.
- **What I read in the reference**: six numbered design moves. Each is one short paragraph naming what makes the piece expensive-looking. Example axes: motif (figurative, botanical, geometric), framing device (frame, branch, garland, open), stone palette and arrangement, metal palette and finish, composition (centred, asymmetric, graduated), pavé density and cut variety.
- **What I will take**: the durable DNA we will preserve in the derived piece (richness level, multi-cut arrangement, pavé density, mixed-metal palette, format).
- **What I will change**: the IP-safe transformation. Must change motif content, framing device, cultural anchor, and ideally palette mix. Preserve the richness level only.
- **Cultural anchor for the derived piece**: the brand-foundation heritage thread that grounds the piece in the user's brand (laurel-and-rose for British court jewellery, sakura-and-koi for Japanese craft, etc.).

### 4. Propose the derived design

Write `brief.md` using `templates/brief-template.md`. Fill:

- **Name**: short, evocative, following the brand's naming convention. Examples in the M&W collection so far: Albion Garland, Redbreast, Westminster, Solene.
- **Tier and position**: based on the inferred or supplied tier and the next position number from `brands/<brand_slug>/approved/INDEX.md` (use `scripts/design_workflow.py next-position --brand <slug>`).
- **Design intent**: 80-200 words. State the silhouette, the structural moves (e.g. graduated knife-edge links, lancet-arch settings, pavé tiered cluster), the cultural anchor in one sentence, and the "British / Persian / Japanese / etc." identity signal. Explicit motifs and stone arrangement.
- **Materials**: specific carats, colours, cuts, and hallmark conventions per the brand foundation.
- **Indicative retail (ex-VAT)**: within the tier band declared in the brand foundation.
- **Lead time**: per the foundation defaults.
- **What makes this not a [Reference brand] copy**: at least four bullets covering motif content, framing device, cultural anchor, and palette differentiation. This is the IP-safety section and must be specific enough to defend.
- **Slug**: set once the name is locked. Use `python scripts/design_workflow.py slugify "<name>"`.

### 5. Render the first iteration

#### Provider routing

Use **gpt-image-2** (`scripts/gpt_image_client.py`) as the default for every
render in this skill: front product, on-model, scene, ambassador. Apply the
seven prompt levers from `docs/luxury-studio-grammar.md` regardless of subject.

Reach for **Nano Banana** (`scripts/nano_banana_client.py`) as a fallback only
when a specific gpt-image-2 render misses on a measurable dimension (pore
detail on a tight hand shot, fine fabric weave, hand anatomy) and a re-prompt
does not recover. Document the reason in `brief.md` when you fall back.

For the **front-view product render** (this step):

- `--action generate` (or `--action edit` with the reference image if explicit visual seeding is desired)
- `--size 1536x2048` for pendants, brooches, earrings (portrait 3:4)
- `--size 1024x1024` for rings, bracelets close-up (square 1:1)
- `--size 2160x2880` for hero necklaces shown full circle (closer to overhead-flat lay)
- `--quality high`
- `--output brands/<brand_slug>/proposed/<piece_slug>/render-v1.png`
- `--prompt`: detailed photoreal product-photography prompt referencing the brand foundation's render defaults (backdrop, lighting). Cite the specific motif, materials, and structural moves. Reference one or two of the foundation's reference houses for visual register.

Assemble the prompt using `templates/on-model-prompt-template.md` as the
starting point, filling in the six slots and keeping the locked grammar block
verbatim.

Build a Telegram-friendly JPEG preview at `<piece_slug>/render-v1-tg.jpg` via `python scripts/design_workflow.py preview --input render-v1.png --output render-v1-tg.jpg`.

### 6. Send for review

If Telegram is configured (TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID in `.env`), run:

```
python scripts/telegram_approval.py send \
  --piece brands/<brand_slug>/proposed/<piece_slug> \
  --image brands/<brand_slug>/proposed/<piece_slug>/render-v1-tg.jpg \
  --caption "PROPOSED: <Piece Name> (<tier>, £<retail>, <lead time>)

Inspired by <reference brand/piece if known>. I kept: <2-3 DNA points>.
I changed: <2-3 transformation points>.

Reply with iteration notes after tapping Iterate."
```

Capture the last line of stdout as `approval_id` (e.g. `jds-a1b2c3d4`). This is written to `approval.json` inside the piece folder.

If Telegram is not configured, print the file path and prompt the user via the chat session; skip the poll step.

### 7. Iteration loop

Run the poller immediately after step 6 (up to 30-minute default window):

```
python scripts/telegram_approval.py poll \
  --piece brands/<brand_slug>/proposed/<piece_slug> \
  --timeout 1800
```

Parse the JSON printed to stdout and branch on `verdict`:

- **`approve`**: proceed to step 8.
- **`iterate`**: use `notes` (the user's Telegram text reply) as a change addendum. Re-render via gpt-image-2 edit using the current render as `--reference`. Save as `render-v<N+1>-<short-note>.png`. Build a fresh JPEG preview, then loop back to step 6.
- **`reject`**: archive the proposed folder to `proposed/<piece_slug>.rejected-<ISO-timestamp>/` and ask the user for a new reference image or new direction.
- **`timeout`**: prompt the user in chat: "I did not hear back on Telegram within 30 minutes. Approve, iterate, or reject?"

For "Render variations" requests (user asks for 2-4 options on a single axis), produce variation renders, build a 2x2 collage via `python scripts/design_workflow.py collage`, send the collage image via `telegram_approval.py send`, and ask the user to pick. On pick, that variation becomes the current render; loop back to step 6.

Up to 5 iterations per piece is the soft cap. If the iteration count exceeds this, ask the user whether to continue or pause.

### 8. Graduate to approved

When the user approves:

- Compute the position number: `nn = python scripts/design_workflow.py next-position --brand <brand_slug>`.
- Create `brands/<brand_slug>/approved/<nn>-<piece_slug>/`.
- Copy the chosen front render to `render-front.png`.
- Copy `reference.md` and `brief.md` across.
- Update the brief.md "Status" line to APPROVED with the date. Append the "Locked decisions (in order applied)" section with the iteration audit trail.
- Generate the on-model render via **gpt-image-2** (editorial campaign quality).
  Assemble the prompt using `templates/on-model-prompt-template.md`. Use the
  edit endpoint with the locked front render as the reference so gpt-image-2
  preserves the piece appearance:

  ```bash
  python scripts/gpt_image_client.py --action edit \
      --prompt "<assembled prompt from on-model-prompt-template.md>" \
      --reference brands/<brand_slug>/approved/<nn>-<piece_slug>/render-front.png \
      --size 1280x1600 \
      --quality high \
      --output brands/<brand_slug>/approved/<nn>-<piece_slug>/render-on-model.png
  ```

  Include scale context in the prompt for small pieces (e.g. "delicate
  daily-wear pendant, ~18mm wide, refined scale, not statement-large"). If
  gpt-image-2 misses on hand anatomy or pore detail and a re-prompt does not
  recover, fall back to Nano Banana (`scripts/nano_banana_client.py`) with the
  same prompt and reference; note the reason in `brief.md`.
- Write `manifest.json` via `templates/manifest-template.json` filled in with the locked spec, locked-variations audit, and considered-variations list.
- Send the on-model preview to Telegram (or to the chat) with confirmation.
- Update `brands/<brand_slug>/approved/INDEX.md`: append a row in the appropriate tier table with the piece number, name, format, retail, approval date, and generator used.

### 9. Stop

Approved set is now `nn` pieces. Tell the user: "<Piece Name> locked at position <nn>. Send the next reference image when ready."

## File conventions

### Telegram configuration

Set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in `.env`. See the README's "Telegram approval (optional)" section for the two-minute setup walkthrough. Use a dedicated bot token for the studio: the poller consumes `getUpdates` exclusively and will conflict with any other bot service sharing the same token.

Each proposed piece folder:

```
brands/<brand_slug>/proposed/<piece_slug>/
├── reference-source.png        # the original reference image supplied by user
├── reference.md                # DNA analysis (what I take / change)
├── brief.md                    # proposed design intent + materials + retail
├── render-v1.png               # first iteration
├── render-v1-tg.jpg            # Telegram preview (downscaled JPEG)
├── render-v2-<note>.png        # subsequent iterations as needed
└── comparison-collage.png      # if variations were rendered
```

Each approved piece folder:

```
brands/<brand_slug>/approved/<NN>-<piece_slug>/
├── reference.md                # copy of the DNA analysis
├── brief.md                    # locked design intent, status=APPROVED
├── manifest.json               # structured spec for site builders
├── render-front.png            # locked hero shot
├── render-on-model.png         # editorial portrait
└── render-on-model-tg.jpg      # Telegram preview
```

Position numbers are two-digit, zero-padded (01, 02, ... 99). Slugs are lowercase, hyphen-separated, no special characters. Names in `brief.md` and `manifest.json` are title-case.

## Render budget

- Typical approved piece cost: $2-4 in OpenAI gpt-image-2 charges. Breakdown:
  - First iteration (1536x2048 high): ~$0.50-1.00
  - 1-2 iteration edits if needed: ~$0.50-1.00 each
  - On-model at 2400x3200 high: ~$1-2
- Per-session soft cap: $10. Tell the user if approaching the cap so they can opt to continue or pause.

## Cost reduction paths

If the user requests a cheaper iteration:

- Drop `--quality high` to `medium` (lower cost, slightly less detail).
- Use Google Nano Banana (Gemini 3 Pro Image) for first iteration if GEMINI_API_KEY is set. ~$0.04 per render. Trade-off: lower fidelity, often needs an upscale via gpt-image-2 edit before catalogue-ready.
- Defer on-model until the front is locked.

## Conventions enforced

- British English by default (override per brand foundation if the brand voice is non-British).
- No em-dashes anywhere. Use period, comma, colon, or parentheses.
- Banned phrases: "elevate, leverage, in today's, delve, navigate the landscape, synergy, unlock, curate, journey (as a noun)".
- All renders run through metadata strip automatically. `gpt_image_client.py` calls `scripts/lib/image_io.py:strip_metadata` after every successful generation. C2PA, ContentCredentials, OpenAI / gpt-image-2 software tags, and XMP/EXIF chunks are all removed so the renders carry no "Made with AI" signal on social platforms. SynthID pixel watermarks (Google models only) cannot be removed and are left intact; gpt-image-2 does not embed SynthID. Users can self-verify any render via `python scripts/design_workflow.py verify-clean --path <render>` (exit 0 = clean).
- The "what makes this not a [Brand] copy" section in brief.md is mandatory. Refuse to render if it is empty or generic.
- Stone palette must match the brand foundation. If a reference image includes a banned stone (e.g. turquoise in a reference but the foundation forbids it), automatically substitute with an allowed equivalent and call out the substitution in `reference.md`.
- Naming must respect the foundation. Refuse names from the foundation's forbidden-naming-patterns list.

## Examples

**Invocation 1 (M&W high-jewellery piece):**

```
User: design from this reference [attaches Harry Winston Endless Love necklace]
      brand=mappin-webb-collection-01, tier=high-jewellery
```

Skill: saves reference, reads foundation (laurel-and-rose, ruby-and-diamond, British court jewellery anchor), proposes "Albion Garland" with intertwined diamond-laurel and ruby-rose strands, renders at 2160x2880, sends Telegram preview.

**Invocation 2 (commercial Signature piece):**

```
User: design from this [attaches a Boucheron Quatre band]
      brand=mappin-webb-collection-01, tier=commercial
```

Skill: proposes a knife-edge band with fluted channels, renders at 1024x1024 square, sends preview.

**Invocation 3 (iteration on an existing piece):**

```
User: iterate, make the central rose smaller and add laurel detail above
```

Skill: re-renders via gpt-image-2 edit using the current render as reference and the change as prompt addendum.

## Stop conditions

- Approved piece graduated to `approved/<NN>-<slug>/` and INDEX.md updated. Stop and wait for the next reference image.
- User says "pause" or "stop" mid-iteration: archive working folder, stop.
- 5 iterations reached without approval: ask the user whether to continue or pause.
