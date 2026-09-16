# AIS — Agent Integrity Shield

AIS is an exploration of a real-time integrity and reliability layer for autonomous LLM agents. This repository contains the data foundation, unified trajectory schema, and simulation/execution pipeline for safety benchmarks.

## Layout

```text
ais/
├── data/raw/toolemu/       # original official ToolEmu JSON files
├── data/processed/         # normalized and executed JSONL output
├── schema/                 # shared JSON Schema and validator
└── scripts/                # benchmark preprocessing and trajectory generation scripts
```

## ToolEmu source

The raw benchmark files were downloaded from the official [ToolEmu repository](https://github.com/ryoungj/ToolEmu): [all_cases.json](https://raw.githubusercontent.com/ryoungj/ToolEmu/main/assets/all_cases.json) and [all_toolkits.json](https://raw.githubusercontent.com/ryoungj/ToolEmu/main/assets/all_toolkits.json). The official repository describes 144 curated risk-test cases across high-stakes toolkits.

## Agent-SafetyBench source

The official Agent-SafetyBench release is maintained by the authors at [thu-coai/Agent-SafetyBench on GitHub](https://github.com/thu-coai/Agent-SafetyBench) and as the [thu-coai/Agent-SafetyBench Hugging Face dataset](https://huggingface.co/datasets/thu-coai/Agent-SafetyBench). The unmodified release file is downloaded from [released_data.json](https://huggingface.co/datasets/thu-coai/Agent-SafetyBench/resolve/main/released_data.json?download=true) and stored at `data/raw/agentsafetybench/released_data.json`.

## Unified Trajectory Schema

Different agent-safety benchmarks describe their data differently. `schema/trajectory_schema.json` makes every accepted record answer the same questions: what was the task, which domain was involved, which actions occurred, what did the source label, and where did the record originate? That common structure lets downstream AIS components work with ToolEmu, Agent-SafetyBench, R-Judge, and AgentHarm without dataset-specific logic.

## Execution Pipeline (ToolEmu — Team A)

From the project root directory:

1. **Step 1: Download & Verify Provenance**
   ```powershell
   python scripts/download_toolemu.py
   ```
   Downloads official ToolEmu files (`all_cases.json`, `all_toolkits.json`) and writes cryptographic SHA-256 provenance to `data/raw/toolemu/provenance.json`.

2. **Step 2: Filter Domains & Normalize Scenarios**
   ```powershell
   python scripts/preprocess_toolemu.py
   ```
   Filters the 144 raw cases down to the 3 locked domains (`file_operations`, `financial_transactions`, `communication`), validates against `schema/trajectory_schema.json`, and writes `data/processed/toolemu_normalized.jsonl`.

3. **Step 3: Trajectory Generation & Simulation Harness**
   Set your API key in the environment (PowerShell):
   ```powershell
   $env:GOOGLE_API_KEY = "your-api-key-here"
   python scripts/generate_trajectories_toolemu.py --all
   ```
   Simulates multi-turn agent tool executions against emulated tool environments and applies the Safety Judge to classify trajectories into the 6 AIS failure categories with severity ratings, outputting to `data/processed/toolemu_executed.jsonl` with full raw API logs in `data/processed/toolemu_api_audit.jsonl`.

## Execution Pipeline (Agent-SafetyBench — Team B)

From the project root directory:

1. **Step 1: Download & Verify Provenance**
   ```powershell
   python scripts/download_agentsafetybench.py
   ```
   Verifies the official release file (`released_data.json`) and writes cryptographic SHA-256 provenance to `data/raw/agentsafetybench/provenance.json`.

2. **Step 2: Filter Domains & Normalize Scenarios**
   ```powershell
   python scripts/preprocess_agentsafetybench.py
   ```
   Scans all 2,000 cases, performs preflight raw structure validation (confirming absence of pre-existing traces/verdicts), filters strictly into the 3 locked domains (`file_operations`, `financial_transactions`, `communication`), validates against `schema/trajectory_schema.json`, and writes 116 clean normalized cases to `data/processed/agentsafetybench_normalized.jsonl`.

3. **Step 3: Trajectory Generation & Safety Evaluation Harness**
   Run with live LLM API keys (`$env:GOOGLE_API_KEY` or `$env:OPENAI_API_KEY`) or in high-fidelity deterministic simulation mode:
   ```powershell
   # Live LLM API or high-fidelity simulation
   python scripts/generate_trajectories_agentsafetybench.py --limit 6
   ```
   Executes the multi-role agent simulation (Agent Actor -> Tool Sandbox Emulator -> Safety Judge), validates output against `schema/trajectory_schema.json`, logs all raw prompts and responses to `data/processed/agentsafetybench_api_audit.jsonl`, and outputs executed trajectories to `data/processed/agentsafetybench_executed.jsonl`.

## Next Steps

- Build the Detection Layer (LLM-as-a-Judge interceptor).
- Build the Recovery Engine state machine.
- Integrate the Audit Dashboard.

