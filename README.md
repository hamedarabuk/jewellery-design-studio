# Jewellery Design Studio

A Claude Code skill repository for fine and high jewellery designers. Send a reference image from a luxury house (Harry Winston, Boucheron, Cartier, Tiffany, Graff), and Claude produces an original, IP-safe derived design in your brand's voice. Renders, brief, approval workflow, all in one folder per piece.

Built on the same pattern as [youtube-channel-studio](https://github.com/hamedarabuk/youtube-channel-studio): a public template + per-brand foundation gitignored so your personal brand data never ships in the public repo.

## What you get

Two skills:

1. **`brand-init`** - a one-time interview that captures your brand identity (palette, motifs, naming conventions, IP rules). Writes `brands/<brand-slug>/foundation.md`. Run once per brand.

2. **`design-from-reference`** - the workhorse. Send a reference image, get a derived piece with reference DNA analysis, design brief, hero render via gpt-image-2, iteration loop, approval, and on-model render. Files land at `brands/<brand-slug>/proposed/<piece-slug>/` and graduate to `brands/<brand-slug>/approved/<NN>-<piece-slug>/` on approval.

The IP-safe transformation rule is enforced at brief-writing time: every derived piece must change motif content + framing device + cultural anchor relative to its reference. The richness level (pavé density, multi-cut arrangement, mixed-metal palette) is preserved. The "would this be confused with the reference" check has to be answered explicitly.

## Install

```bash
# Clone the repo
git clone https://github.com/<your-username>/jewellery-design-studio.git
cd jewellery-design-studio

# Set up Python (3.11+)
python -m venv .venv
.venv\Scripts\activate            # Windows
# or: source .venv/bin/activate    # macOS / Linux

pip install -r requirements.txt

# Set your API keys
cp .env.example .env
# Edit .env: add OPENAI_API_KEY (required) and Telegram bot token (optional)
```

You need an OpenAI API key for gpt-image-2: https://platform.openai.com/api-keys

Telegram is optional. Without it, renders are saved to disk and you review them via file explorer. With it, every render is delivered to your Telegram chat with a captioned approval prompt. To set up: message `@BotFather`, create a bot, get the token; then message your new bot once and read your chat id from `https://api.telegram.org/bot<TOKEN>/getUpdates`.

## First-run walkthrough

Open the repo in Claude Code. Then:

### 1. Set up your brand foundation (one-time per brand)

```
> invoke the brand-init skill, brand slug "my-brand-2026"
```

Claude conducts a short interview: designer identity, partner brand (if licensing), catalogue tiers, design language, stone palette (allowed and banned), metal palette, naming convention, cultural anchor, IP-safe transformation rule, render defaults.

When the interview is done, `brands/my-brand-2026/foundation.md` is your durable brand identity. You never re-supply this information.

### 2. Design a piece from a reference

```
> design from this reference [attach reference image]
  brand=my-brand-2026, tier=high-jewellery
```

The skill:

1. Saves the reference to `brands/my-brand-2026/proposed/<slug>/reference-source.png`.
2. Writes `reference.md` with a DNA analysis (what makes the reference expensive; what to take; what to change).
3. Writes `brief.md` with the derived piece (name, design intent, materials, retail, lead time, "what makes this not a clone" section).
4. Renders the front view via gpt-image-2 high quality at 1536x2048.
5. Sends a Telegram preview (or prints the file path) and asks for approval.

### 3. Iterate or approve

You can:

- **Approve as-is**: skill graduates the piece to `approved/<NN>-<slug>/` and renders the on-model shot at 2400x3200 using the front render as a consistency reference. Updates `approved/INDEX.md`.
- **Iterate with notes**: "make the central rose smaller", "both feet on the branch", "white chain not yellow". The skill re-renders via gpt-image-2 edit using the current render as reference.
- **Render variations**: useful when there is a binary choice (chain colour, pose, framing). The skill produces 2-4 variations and builds a 2x2 collage so you can pick.
- **Reject and start over**: the proposed folder is archived; you can send a new reference image.

### 4. Send the next reference

Once a piece is approved, send the next reference image. The skill writes the next position number into `approved/INDEX.md` automatically.

## File layout per brand

```
brands/<brand-slug>/
├── foundation.md                       # your brand identity (gitignored)
├── proposed/                           # iteration working folder
│   └── <piece-slug>/
│       ├── reference-source.png        # the reference you sent
│       ├── reference.md                # DNA analysis
│       ├── brief.md                    # proposed design
│       ├── render-v1.png               # first iteration
│       ├── render-v1-tg.jpg            # Telegram preview
│       ├── render-v2-<note>.png        # subsequent iterations
│       └── comparison-collage.png      # if variations were rendered
└── approved/
    ├── INDEX.md                        # ordered table of locked pieces
    └── <NN>-<piece-slug>/
        ├── reference.md
        ├── brief.md                    # status=APPROVED
        ├── manifest.json
        ├── render-front.png            # locked hero
        ├── render-on-model.png         # editorial portrait
        └── render-on-model-tg.jpg
```

## Cost expectations

Per approved piece (front + on-model + 1-2 iterations):

- gpt-image-2 high quality at 1536x2048: ~$0.50 - $1.00 per render
- On-model at 2400x3200: ~$1 - $2
- Typical total per approved piece: **$2 - $4**

Per-session soft cap: $10 of render charges. The skill flags when you approach this.

## AI metadata stripping (no "Made with AI" badges)

Every image written by `gpt_image_client.py` runs through `scripts/lib/image_io.py:strip_metadata` immediately after generation. The strip rebuilds the image from raw pixel data into a fresh Pillow Image, guaranteeing that no ancillary chunks (C2PA, ContentCredentials, XMP, EXIF, OpenAI / gpt-image-2 software tags) survive.

This matters because LinkedIn, Instagram, X, and other social platforms read these tags and display a visible "Made with AI" badge on posts that carry them. Stripping is automatic and unconditional in this skill.

Note: SynthID is a pixel-level watermark embedded by Google's image models (Gemini, Imagen, Nano Banana) into the actual image pixels. It cannot be removed by metadata stripping and is left intact. OpenAI's gpt-image-2 does not embed SynthID, so renders from this skill's default generator are clean.

**Verify any image yourself:**

```
python scripts/design_workflow.py verify-clean --path brands/<brand>/approved/<NN>-<slug>/render-front.png
```

Exit code 0 if clean, 1 if any AI-generator signature is still present. Pass `--json` for a structured report.

## Telegram approval (optional)

Without Telegram the workflow still runs: renders are saved to disk and you review them via file explorer, approving in the Claude Code chat. With Telegram every render lands in your phone with three one-tap buttons: **Approve**, **Iterate**, **Reject**.

### Two-minute setup

1. Message `@BotFather` on Telegram. Send `/newbot` and follow the prompts. Copy the bot token it gives you (format `123456789:ABCdef...`).
2. Start a chat with your new bot by searching for its username and sending `/start`.
3. Visit `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates` in your browser. Find your chat id in the JSON (`result[0].message.chat.id`).
4. Add both values to your `.env`:

```
TELEGRAM_BOT_TOKEN=123456789:ABCdef...
TELEGRAM_CHAT_ID=749526661
```

> **Hard warning: use a dedicated bot token.** Telegram `getUpdates` can be consumed by only one process at a time. If you reuse a bot token already polled by another service (for example an existing notification bot or another skill poller), that service will consume the approval callbacks and the studio's poller will time out silently. Create a new bot in BotFather specifically for the studio.

### Manual test

Send a render manually, then start the poller in a second terminal:

```bash
# Terminal 1: send
python scripts/telegram_approval.py send \
  --piece brands/my-brand/proposed/albion-garland \
  --image brands/my-brand/proposed/albion-garland/render-v1-tg.jpg \
  --caption "Test send from jewellery-design-studio"

# Terminal 2: poll (run immediately after; 60-second timeout for a quick test)
python scripts/telegram_approval.py poll \
  --piece brands/my-brand/proposed/albion-garland \
  --timeout 60
```

Tap a button in Telegram. The poller prints the verdict JSON and exits.

### Dry run (no API call)

Verify the payload shape and keyboard layout without touching the API:

```bash
python scripts/telegram_approval.py send \
  --piece brands/my-brand/proposed/albion-garland \
  --image brands/my-brand/proposed/albion-garland/render-v1-tg.jpg \
  --caption "Dry run test" \
  --dry-run
```

The printed JSON shows the `inline_keyboard` array with three buttons and the `jds:<action>:<id>` callback_data shape.

---

## How to customise

Edit `brands/<brand-slug>/foundation.md` directly to refine your brand voice. The `design-from-reference` skill reads it on every invocation, so changes take effect immediately.

Edit `.claude/skills/design-from-reference/SKILL.md` to adjust the workflow (render sizes, iteration cap, Telegram caption format). Edits stay local to your clone; you can fork the repo and share your variant.

## Licensing the studio for your students or team

The repo is MIT-licensed. You can:

- Fork it for your own students or workshop participants.
- Add your own custom skills (e.g. for studio quoting, GIA certificate generation, supplier price lookup).
- Pre-populate brand foundations for your students so they start from a working example.

## What this skill is NOT

- It is not a CAD program. It produces editorial renders, not Rhino or MatrixGold files. Use it for pitch artefacts, catalogue images, and design exploration. Bring renders to your CAD jeweller separately.
- It is not a copy machine. The IP-safe transformation rule is the heart of the tool. Pieces that fail the "would this be confused with the reference" check are refused.
- It is not a customer-facing site. The `approved/` folder is your input. A separate microsite or catalogue tool reads `approved/INDEX.md` and `manifest.json` to build the customer-facing artefact.

## Acknowledgements

Pattern inspired by [youtube-channel-studio](https://github.com/hamedarabuk/youtube-channel-studio). Born out of the Mappin & Webb Collection 01 pitch (Hamed Arab Choobdar, independent designer, 2026).
