# Semantic integration: queued invocation cancelled

[Run43070787888](https://github.com/alvarovillalbaa/findlet/actions/runs/43070787888)
was cancelled while queued, before any runner steps. Source
`6f3c5d3e13f0738905d4e227554f12fc73247d07`; activation
`9a5cf310d3d8c86fff27f7753b461fa89190c5ad`. All S01/S02 checks are **unrun**.

Source review caught a draft admission floor above the documented free ARM64
runner's capacity. No setup, compilation, model download, native execution or
scratch/teardown observation occurred. The changed resource estimate is recorded
in the [proposal](../../../proposals/qmd-semantic-integration.md); no paid runner
or local storage exception was used. Original run and pre-cancel jobs API bodies
are adjacent `qmd-semantic-attempt-1.run.json` and `.jobs.json`.
