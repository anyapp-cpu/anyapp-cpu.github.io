# Local case illustrations

`sources/` contains SVG exports from the supplied Figma files. Figma is never modified.
The preparation script replaces demonstration content, calculates text widths using
the same Inter outlines used for rendering, and reflows related UI elements before
outlining the text. Regenerate every full screen and crop together:

```sh
python3 -m pip install fonttools
python3 scripts/gocomment/prepare.py
```

`assets/gocomment/vectors/layout-audit.json` records badge padding, header spacing,
fractions, workspace names and status tokens. The original raster waving-hand emoji
is intentionally embedded inside the SVG. The puzzle is removed from local exports.
Inter is distributed under the license in `assets/fonts/Inter-OFL.txt`.

The audit also covers text badges, complete account controls, and neighboring tabs.
Mobile website states come from `7:19346`, `7:19424`, and `7:19436`; task transfer
uses `6363:155081` and `172:176050` in `NnGonWg651y3dTfD0qeMOV`. Their local exports
use the Forma site, consistent participants, dates, environment and attachments.

Circular tour indicators keep their original diameter and centered numerals. Mobile
SVGs fill the device viewport without letterboxing; the composer uses an enabled
send state, an end-of-text caret and the same cluster appearance as the site view.
These semantic states are recorded alongside spacing checks in the layout audit.
