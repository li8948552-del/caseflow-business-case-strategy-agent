# CaseFlow Deck Benchmark

This benchmark catalog turns public past case-competition submissions into a
reproducible evaluation set without republishing third-party files.

## Dataset design

| Split | Purpose | Agent may learn from placement? |
|---|---|---|
| `reference` | Extract patterns and build scoring examples | Yes |
| `calibration` | Check whether the judge ranks submissions correctly | Only after scoring |
| `holdout` | Blind regression evaluation | No |
| `challenge` | Recent out-of-distribution test | No |

The first catalog contains 13 decks: six reference winners, a ranked three-deck
Nordea calibration set, a ranked three-deck Boozt holdout set, and one recent
L'Oreal challenge winner. Every placement is linked to the official CBS Case
Competition archive.

## Commands

```bash
python tools/benchmark_catalog.py validate
python tools/benchmark_catalog.py list
python tools/benchmark_catalog.py list --split calibration
python tools/benchmark_catalog.py export-blind --split holdout --output /tmp/holdout.json
```

`export-blind` removes placement, team, and learning-focus labels. Use that file
as evaluator input so the judge cannot infer the official ranking from metadata.

## Evaluation protocol

1. Run CaseFlow on the original case brief without exposing any submitted deck.
2. Score each submitted deck independently using `competition/rubric.yaml`.
3. Freeze scores before revealing placements.
4. Measure ranking accuracy within each same-case set and record reasoning.
5. Keep `holdout` and `challenge` out of prompts, RAG indexes, and examples.

Recommended metrics:

- `pairwise_ranking_accuracy`: correctly ordered deck pairs / all ranked pairs.
- `winner_selection_accuracy`: whether the official winner receives the top score.
- `score_stability`: score spread over three repeated judging runs.
- `citation_coverage`: supported material claims / all material claims.
- `numerical_traceability`: reproducible key figures / all key figures.
- `critical_issue_recall`: known judge weaknesses found / annotated weaknesses.

## Copyright and contamination controls

- The repository stores URLs and CaseFlow-authored metadata only.
- Do not commit downloaded PDFs, PPTX files, extracted slide text, or screenshots.
- Local downloads belong under `benchmarks/raw/`, which is git-ignored.
- Do not use `holdout` or `challenge` decks for prompt examples or scoring-rule edits.
- Record any accidental exposure in the experiment log and retire that case from
  blind evaluation.

