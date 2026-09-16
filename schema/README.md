# AIS unified trajectory schema

`trajectory_schema.json` is the common contract for every benchmark adapter in AIS. It separates the original task, the observed tool-use sequence, and the source's evaluation annotation. This lets later detection and recovery experiments compare different benchmarks without changing their input format.

- `trajectory_id`: stable, source-prefixed identifier (for example, `toolemu_0001`).
- `source_dataset`: human-readable dataset origin.
- `status`: distinguishes a published scenario definition from an observed, executed trajectory.
- `task_context`: the user's original instruction.
- `domain`: the deliberately small initial scope: file operations, financial transactions, or communication.
- `actions`: ordered tool calls. Each call records its name, input, lifecycle stage, and output. An empty list is valid when a source publishes test cases but no executed trace.
- `risk_taxonomy`: the source's potential risky actions and outcomes, kept as separate lists.
- `expected_achievements` and `underspecifications`: source-provided safe-success expectations and missing task/safety constraints.
- `ground_truth_label`: the benchmark's outcome annotation in AIS terminology. `is_failure` can be null when the source has no verdict; `note` explains why. `source_annotation` always preserves the source wording.
- `raw_source_ref`: file and record identifier that can be used to trace a normalized record back to the original data.

## ToolEmu mapping

ToolEmu's official `all_cases.json` is a *risk-test-case* benchmark, not a release of executed agent trajectories. Consequently, its records have `status: "scenario_only"`; `User Instruction` maps directly to `task_context`, and `Toolkits` is used to choose `domain`; `actions` remains `[]` rather than inventing tool calls or parameters. `Potential Risky Actions` and `Potential Risky Outcomes` map to the separate `risk_taxonomy` lists; `Expected Achievements` and `Underspecifications` are retained directly. A future export produced by ToolEmu's emulator can populate `actions`; where it has no lifecycle marker, use `execution` (see the TODO in the adapter).

ToolEmu supplies potential risks, not an observed pass/fail event. The adapter therefore records `is_failure: null`, with null category/severity and a note that an LM-emulated sandbox run is required for a verdict. This avoids representing a hypothetical risk as an observed failure. `raw_source_ref` is `all_cases.json#<ToolEmu case name>`.
