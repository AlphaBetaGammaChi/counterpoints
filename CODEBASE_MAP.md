# counterpoints codebase map

Jekyll site of evidence-backed rebuttals/discussion documents for
contested topics. Every claim is cited (DOI for peer-reviewed, URL for
grey literature).

## Layout

```
counterpoints/
├── _config.yml                  # Jekyll config
├── index.md                     # site landing page
├── topics/
│   └── woodsmoke/               # Active topic: residential wood burning
│       ├── index.md             #   landing / TL;DR
│       ├── evidence.md          #   master evidence review
│       ├── arguments/           #   one doc per common claim (claim →
│       │                        #   short answer → evidence → steelman → bottom line)
│       ├── references.md        #   bibliography
│       ├── advocacy.md          #   groups/programmes/resources
│       ├── slides.md|html       #   deck from same content
│       └── figures/             #   generated charts/animations
└── scripts/
    └── make_woodsmoke_figures.py  # regenerates the topic's figures
```

## Rules of the house

Every claim cited; peer-reviewed first, grey literature second. New topic =
new `topics/<name>/` dir following the woodsmoke template; figures are
generated in `scripts/`, never hand-edited.
