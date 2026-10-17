# The Weighed Sling — mark 37

The sling holds the whole load before it enters the basket. It represents
ZipMerge's shared whole-archive input-size budget, which reaches the next
archive's gate before reading and parsing.

## Delivered media

- `artifacts/line-2/wall-v18.png`: 1254 × 1254, RGB PNG, 2,782,898 bytes.
- `artifacts/line-2/wall.png`: byte-identical continuation wall.
- `dist/line-2/37.jpg`: 512 × 512 JPEG, 93,201 bytes.
- `dist/line-2/37.json`: only new numbered record; PNG SHA-256 is
  `cf270e5558931eb8c3bf2773220bc1e72476e093e70af0768dfed1c3c5b31492`.

Read the inherited wall and inspected it with view_image before generation.
Used the imagegen skill and installed `mcp__image__generate_image` tool; no CLI,
key or fallback. The generator wrote the selected pigment directly to the
required output path. One-time assembly replaced that path with the complete
wall; no draft, mask, crop or other picture was saved elsewhere. Reused the
read-only inherited line-1 media codec and ffmpeg for in-memory pixels only.

## Full generation prompt

A single small primitive prehistoric cave painting motif isolated on a pure
white background for compositing: a curved woven carrying sling hanging from
a short bent branch, holding three irregular rounded ochre stones tightly
together. Burnt-stick charcoal uneven outlines, dry red ochre and yellow ochre
pigment, chalk white accents, flat simple thumb-painted drawing, worn and
sparse. Lascaux cave painting style, earth pigments only. The sling is irregular
and hand-drawn, not a scale diagram. No letters, numbers, text, symbols,
signatures, logos, frames, hands, people, frogs, photographic objects or 3D.
One compact centered motif filling the middle three quarters of the square.
White background completely blank.

The generator supplied 1254-pixel square pigment. Assembly cropped and scaled
it in memory, removed white, mapped pigment to charcoal/red/yellow ochre and
retained underlying rock grain. The only writable patch is [78,365,213,510),
135 × 145 pixels on bare left-side rock. Exactly 7,962 pixels changed, with
zero changes outside; the 1,564,554 remaining pixels are identical to the
inherited wall. No inherited mark was moved, erased or redrawn.

## Chosen visual review

Inspected the final full PNG and the 512-pixel JPEG with view_image. The cave
keeps its square size, warm rough rock, cracks, torchlight and framing. The new
sling is a sparse ochre/charcoal drawing, with bare stone showing through.
Pepe retains his wide mouth and heavy-lidded eyes. Counted five digits on the
raised hand: four fingers and one thumb; counted five on the hand above the
basket: four fingers and one thumb. No new hand or stencil appears.

No letters, numbers, captions, signatures, logos, watermarks, borders, real
people, political or hateful symbols observed. Unmet visual requirements:
**none observed**. Limitations: inherited rock has photographic texture;
small pigment details are softened in the JPEG, and visual review is a local
observation, not independent certification. This task's specific adjacent-JPEG
requirement is followed despite its general pictures-only-in-artifacts sentence.

The PNG and JPEG dimensions, file sizes, digest and preservation counts are
recorded in media-check-37.json. assemble-37.cjs is a one-time assembly record;
it deliberately refuses rerunning after the numbered record exists.
