---
name: brand-init
description: One-time interview to capture a jewellery brand's foundation (designer identity, palette, motifs, naming conventions, IP rules). Run once per brand; subsequent design work reads the foundation automatically.
model: sonnet
---

# brand-init

## Purpose

Capture a jewellery brand's durable identity once, so every subsequent design piece can read it without the user having to re-explain. This is the analogue of `yt-channel-init` in the youtube-channel-studio repo.

A brand foundation is a markdown file at `brands/<brand-slug>/foundation.md`. It is gitignored so personal brand data never ships in the public repo.

## When to invoke

Invoke this skill when one of these is true:

- The user is starting a new collection or licence pitch and no foundation exists yet at `brands/<brand-slug>/foundation.md`.
- The user explicitly asks to "init a brand" or "set up a new brand."
- The `design-from-reference` skill reports a missing foundation and the user wants to create one.

Do NOT invoke this skill if a foundation already exists at the brand path. To update an existing foundation, edit the file directly or run the skill with the `--refresh` flag (asks each question pre-filled with the current answer; user can keep or change).

## Inputs

Required:

- `brand_slug`: a short hyphenated identifier for the brand (e.g. `mappin-webb-collection-01`, `emma-atelier`, `my-licensing-pitch-2026`). The skill creates `brands/<brand_slug>/` if it does not exist.

Optional:

- `brand_name`: the human-readable brand name (e.g. "Mappin & Webb Collection 01"). Defaults to a title-case form of the slug.

## Protocol

1. **Verify the slug.** If `brands/<brand_slug>/foundation.md` already exists, refuse with a one-line message: "Foundation already exists at brands/<slug>/foundation.md. Edit it directly or pass --refresh to update interactively." Otherwise create the directory.

2. **Run the interview.** Ask each section in order. Take short, structured answers. If the user is brief or says "skip," fill the section with a sensible default and flag it as "needs review" in the foundation file. The interview sections are:

   **a. Designer identity**
   - Designer name and credentials (BCU, GIA, RJC, FCSD, etc.).
   - Studio location (city, country).
   - Brand voice in one sentence.

   **b. Partner brand (if licensing model)**
   - Partner retailer name and notable existing collections they carry.
   - Commercial model (designer-licensing, white-label, own-brand). Skip if own-brand.
   - Royalty model and rate, if licensing.
   - Exclusivity and term length, if any.

   **c. Catalogue tiers and price bands (retail ex-VAT)**
   - Commercial / Signature tier band (e.g. £8k - £60k).
   - High Jewellery tier band, if applicable (e.g. £80k - £250k+).
   - Lead time defaults per tier (Signature ~6-10 weeks, High Jewellery ~12-20 weeks).

   **d. Design language**
   - Aesthetic camp: decorative-high-jewellery (Boucheron Animaux, Harry Winston botanicals), minimalist-modernist (Cartier Trinity, Boucheron Quatre), figurative-modern (Tiffany Schlumberger), or other (free text).
   - Three to five reference houses the brand sits alongside in register and tier.
   - Three to five reference houses the brand explicitly does NOT want to be confused with (anti-reference).

   **e. Stone palette**
   - Allowed stones (specific types, colour grades, cut preferences).
   - Banned stones (explicit no-list). Example: "no turquoise, no cabochons, no synthetic stones."
   - Coloured-stone supply preferences (e.g. Burmese ruby, Ceylon sapphire, Colombian emerald, Australian opal).

   **f. Metal palette**
   - Allowed metals (18ct yellow, white, rose gold; platinum; silver).
   - Hallmark conventions (London Assay Office, Birmingham, etc.).

   **g. Naming convention**
   - Language register: English, Latinate, French-leaning, native-language, or mixed.
   - Length preference: one or two short words.
   - Cultural anchor for names (e.g. British heritage, Persian poetry, Japanese minimalism).
   - Forbidden naming patterns (e.g. "no Persian names for this collection").

   **h. Cultural anchor**
   - Heritage references the brand draws on (Garrard court jewellery, Art Deco, Japanese craft, Persian architecture).
   - Specific motifs already used or planned (laurel, rose, robin, oak, fan, ribbon-knot).
   - Defensible cultural story in one paragraph: why this aesthetic in this market.

   **i. IP-safe transformation rule**
   - Must-change axes when deriving from a reference (motif, framing, cultural anchor, palette).
   - Preservation axes (richness level, multi-cut arrangement, pavé density).
   - "Would this be confused with the reference" check criteria.

   **j. Render defaults**
   - Default generator (gpt-image-2 is the studio default).
   - Default render sizes per category (e.g. 1536x2048 portrait for pendants and brooches, 1024x1024 square for rings).
   - Backdrop style (pearl-grey gradient, matte black velvet, Carrara marble, cream linen).
   - Lighting style (soft directional studio light from upper left is the default).

3. **Write the foundation file.** Use `templates/foundation-template.md` as the layout. Replace each placeholder with the user's answer. Save to `brands/<brand_slug>/foundation.md`. Include a "Last reviewed: YYYY-MM-DD" line at the top.

4. **Create the brand subdirectories.** Make the empty folders so the design-from-reference skill has somewhere to write later:

   ```
   brands/<brand_slug>/
   ├── foundation.md          # the file you just wrote
   ├── proposed/              # iteration working folder
   └── approved/              # locked pieces
       └── INDEX.md           # initially empty (just the header)
   ```

   Seed `approved/INDEX.md` from `templates/index-template.md` with the brand name in the header.

5. **Confirm.** Print a short summary: brand slug, brand name, foundation file path, INDEX file path, and a one-line nudge to invoke the `design-from-reference` skill next.

## Output

- `brands/<brand_slug>/foundation.md` (the durable brand identity).
- `brands/<brand_slug>/approved/INDEX.md` (initially empty header).
- `brands/<brand_slug>/proposed/` (empty directory).

## Conventions

- British English by default (configurable in section a if the brand voice is non-British).
- No em-dashes. Use period, comma, colon, or parentheses.
- Avoid the banned phrases: "elevate, leverage, in today's, delve, navigate the landscape, synergy, unlock, curate, journey (as a noun)".
- Keep section answers terse: 1-3 bullets per question or one short paragraph.

## Examples

**Invocation 1 (new licensing pitch):**

```
User: init a new brand for my Mappin & Webb pitch, slug "mappin-webb-collection-01"
```

Skill runs the full interview, writes `brands/mappin-webb-collection-01/foundation.md`.

**Invocation 2 (own-brand atelier):**

```
User: brand-init "Emma Atelier", own-brand, slug "emma-atelier"
```

Skill skips partner / royalty questions, runs the rest, writes `brands/emma-atelier/foundation.md`.

**Invocation 3 (refresh existing):**

```
User: brand-init --refresh mappin-webb-collection-01
```

Skill re-asks each question with the current answer as the default; user accepts or edits.

## Stop conditions

- Foundation file written and `approved/INDEX.md` seeded. Then stop.
- User says "stop" or "skip the rest" mid-interview: write a partial foundation with placeholders, flag the unfilled sections as "needs review," and stop.
