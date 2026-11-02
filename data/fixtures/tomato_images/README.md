# Public tomato development photographs

These are real photographs, not generated or composited scenes. Their image-level
descriptions and licences were checked on Wikimedia Commons on 2 November 2026.
Original bytes, download URLs, authors, licences and SHA-256 checksums are retained
in `manifest.json`. Each image remains under its own licence, separate from code.

| File | Author / attribution | Licence | Source |
| --- | --- | --- | --- |
| mixed_mold.jpg | JIP, Moldy tomatoes | CC BY-SA 4.0 | [Commons](https://commons.wikimedia.org/wiki/File:Moldy_tomatoes.jpg) |
| market_discard.jpg | Gideon, Rotten tomatoes | CC BY-SA 2.0 | [Commons](https://commons.wikimedia.org/wiki/File:Rotten_tomatoes.jpg) |
| basket.jpg | George Chernilevsky, Tomatoes in basket 2022 G1 | CC BY 4.0 | [Commons](https://commons.wikimedia.org/wiki/File:Tomatoes_in_basket_2022_G1.jpg) |
| basket_detail.jpg | George Chernilevsky; crop by this project | CC BY 4.0 | Same basket source; crop bounds `[900,1250,3000,2600]` |

The mixed-condition image contains visible mold-like growth on some tomatoes,
normal-looking visible surfaces on others, occlusion and partial edge objects.
It is a useful engineering challenge, not a labeled crate benchmark. The market
image tests obvious damage; the basket tests crowded, partially hidden objects.
None establishes freshness, safety or hidden-surface condition.

No independent item labels or reference masks have been supplied. Do not report
precision, recall, IoU or a fresh/rotten accuracy from these photos without separate
annotation. These examples are development data and must not enter a future held-out
test set after prompts are revised using them.

The UI credits each source. Imported observations are marked `fixture` with a
sample ID; their timestamp is import time, not original capture time. Imports do
not run models. Clicking Analyse makes live Meta calls only when configured.
Derived crops/overlays of share-alike images retain the corresponding image licence.

`basket_detail.jpg` is a spatial crop only, not a composite or generated scene.
It was added after the full scene exceeded the bounded 32-object analysis limit.
Retain the full-scene failure in reports; a successful detail crop does not prove
the full basket was analysed. Reproduce the crop with Pillow:
`Image.open('basket.jpg').crop((900,1250,3000,2600)).convert('RGB').save('basket_detail.jpg', quality=95)`.
