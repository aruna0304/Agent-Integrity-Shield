# AIS — Agent Integrity Shield

AIS is an exploration of a real-time integrity, policy compliance, and reliability layer for autonomous LLM agents. This repository contains the data foundation, unified trajectory schema, multi-role simulation harnesses, and interactive evaluation tooling for safety benchmarks.

---

## Benchmark Provenance & Attribution

- **ToolEmu:** Originates from **University of Toronto / Vector Institute, with Stanford (Hashimoto)** (Ruan et al., 2024). Raw test cases provide risk annotations and tool specifications across curated environments.
- **Agent-SafetyBench:** Originates from **Tsinghua University (CoAI Group)** (Zhang et al., 2024). Raw release contains 2,000 safety evaluation prompts and tool specifications across 349 environments.

---

## Project Status

### 1. Verified (Outputs Inspected & 100% Schema-Valid)
- **ToolEmu Normalized Scenarios:** 43 domain-filtered cases (`data/processed/toolemu_normalized.jsonl`).
- **ToolEmu Executed Trajectories:** 43 executed trajectories (`data/processed/toolemu_executed.jsonl`), reconstructed from verified audit logs (19 financial transactions, 13 file operations, 11 communication).
- **ToolEmu Strategy Trajectories:** 15 graduated-policy constraint scenarios (`data/processed/strategy_scenarios_executed.jsonl`).
- **Agent-SafetyBench Normalized Scenarios:** 116 domain-filtered cases (`data/processed/agentsafetybench_normalized.jsonl`).
- **Agent-SafetyBench Executed Trajectories:** 6 executed trajectories in `data/processed/agentsafetybench_executed.jsonl` (out of 116 available domain-filtered cases; 12 judge calls are logged in audit).
- **Agent-SafetyBench Strategy Trajectories:** 3 executed trajectories (`data/processed/agentsafetybench_strategy_executed.jsonl`).
- **Interactive Runs:** 8 runtime user sessions (`data/processed/interactive_runs.jsonl`).

### 2. Implemented but Not Fully Audited
- **Multi-Role LLM Simulation Harness:** 3-role execution pipeline (Agent Actor $\rightarrow$ Tool Sandbox Emulator $\rightarrow$ Safety Judge).
- **AIS Safety Evaluation Taxonomy:** Classification into 6 failure categories (`hallucinated_tool_call`, `unauthorized_intent`, `tool_failure`, `wrong_parameters`, `silent_failure`, `no_verification`), with severity ratings and calibrated confidence scores.
- **Safe Execution & Overwrite Guardrails:** Overwrite protection preventing partial test runs (`--limit`) from overwriting full runs, with `--dry-run` simulation and `--force` override.
- **Interactive Terminal Agent:** Zero-shot domain router, formatted out-of-domain rejection guardrails, human-in-the-loop clarification, and token-overlap reference matching.
- **Unified Trajectory Schema Validator:** Standalone CLI and Python API with bounds and type validation (`schema/validate_trajectory.py`).

### 3. Not Built Yet
- **Live Interception Point:** Real-time middleware hook intercepting agent tool dispatches in production runtime environments.
- **Detection Layer:** Online policy and anomaly classifier evaluating actions in flight before tool execution.
- **Recovery Engine:** Automated rollback, parameter steering, and dynamic clarification generation upon policy violation.
- **Audit Dashboard:** Web-based telemetry dashboard for visualizing live agent safety metrics and audit trails.

---

## Repository Layout

```text
ais/
├── data/raw/toolemu/              # Official ToolEmu raw JSON files & provenance
├── data/raw/agentsafetybench/     # Official Agent-SafetyBench release & provenance
├── data/processed/                # Normalized, strategy-executed, and interactive JSONL outputs
│   ├── toolemu_normalized.jsonl                 # 43 domain-filtered ToolEmu scenarios
│   ├── toolemu_executed.jsonl                   # 43 executed ToolEmu trajectories (full benchmark run)
│   ├── toolemu_executed_limit5_rerun.jsonl      # 5-record sample run
│   ├── strategy_scenarios_executed.jsonl        # 15 graduated-policy constraint scenarios
│   ├── agentsafetybench_normalized.jsonl        # 116 domain-filtered Agent-SafetyBench scenarios
│   ├── agentsafetybench_executed.jsonl          # 6 executed Agent-SafetyBench trajectories (partial run)
│   ├── agentsafetybench_strategy_executed.jsonl # 3 Agent-SafetyBench strategy trajectories
│   ├── interactive_runs.jsonl                   # 8 dynamic runtime user sessions
│   ├── toolemu_api_audit.jsonl                  # ToolEmu raw LLM API audit log (prompts, tokens, latencies)
│   ├── agentsafetybench_api_audit.jsonl         # Agent-SafetyBench raw LLM API audit log
│   └── agentsafetybench_strategy_audit.jsonl   # Agent-SafetyBench strategy audit log
├── schema/                        # Unified JSON Schema (Draft-07) and validator
│   ├── trajectory_schema.json                   # Unified contract across benchmarks
│   └── validate_trajectory.py                  # CLI and module validation utility
└── scripts/                       # Preprocessing, strategy, and interactive harnesses
    ├── download_toolemu.py                      # ToolEmu provenance downloader
    ├── preprocess_toolemu.py                    # ToolEmu domain normalization
    ├── generate_trajectories_toolemu.py         # ToolEmu trajectory simulation harness
    ├── strategy_agent_toolemu.py                # ToolEmu graduated-policy strategy agent
    ├── download_agentsafetybench.py             # Agent-SafetyBench downloader
    ├── preprocess_agentsafetybench.py           # Agent-SafetyBench domain normalization
    ├── generate_trajectories_agentsafetybench.py# Agent-SafetyBench simulation harness
    ├── strategy_agent_agentsafetybench.py       # Agent-SafetyBench strategy agent
    └── interactive_agent.py                     # Interactive CLI with auto-domain classifier
```

---

## Unified Trajectory Schema Contract

`schema/trajectory_schema.json` standardizes agent behavior records across disparate sources into a common structure:
- `trajectory_id`: Unique identifier with dataset provenance prefix.
- `status`: `"scenario_only"` | `"executed_trajectory"`.
- `scenario_type`: `"standard"` | `"constraint_ambiguous"` | `"interactive"`.
- `domain`: `"file_operations"` | `"financial_transactions"` | `"communication"`.
- `actions`: Ordered array of tool invocations with `lifecycle_stage` (`pre_execution`, `execution`, `post_execution`).
- `ambiguity_score`: Captures ambiguity resolution (`handling`, `reasoning`).
- `ground_truth_label`: Structured safety verdict (`is_failure`, `failure_category`, `severity`, `confidence`, `note`).

Validate any `.jsonl` dataset with the CLI validator:
```powershell
python schema/validate_trajectory.py data/processed/toolemu_executed.jsonl
```

---

## Execution Modes & How to Run

From the project root directory, configure your API key:

```powershell
$env:GOOGLE_API_KEY = "your-api-key-here"
```

### 1. ToolEmu Benchmark Pipeline
```powershell
# Step 1: Download & Verify Provenance
python scripts/download_toolemu.py

# Step 2: Filter to 3 Locked Domains & Validate Schema (43 cases)
python scripts/preprocess_toolemu.py

# Step 3: Run Full Benchmark Trajectory Generation (all 43 cases)
python scripts/generate_trajectories_toolemu.py --all

# Test run with --limit:
# NOTE: Using --limit N automatically writes to toolemu_executed_limit<N>.jsonl to protect
# the full-run dataset. Overwriting a larger file requires the explicit --force flag.
python scripts/generate_trajectories_toolemu.py --limit 5
```

### 2. Strategy-Aware Graduated Policy Harness (ToolEmu)
Evaluates agent decision logic on vague, real-world prompts with policy thresholds embedded in tool specifications:
```powershell
# Run all 15 constraint-ambiguous scenarios across 3 domains
python scripts/strategy_agent_toolemu.py

# Test run with --limit:
# NOTE: Automatically writes to strategy_scenarios_executed_limit<N>.jsonl to protect full run.
python scripts/strategy_agent_toolemu.py --domain financial_transactions --limit 3
```

### 3. Agent-SafetyBench Pipeline
```powershell
# Step 1: Download & Verify Provenance
python scripts/download_agentsafetybench.py

# Step 2: Filter & Normalize Scenarios (116 cases)
python scripts/preprocess_agentsafetybench.py

# Step 3: Run Safety Simulation Harness
# NOTE: Writes to agentsafetybench_executed_limit6.jsonl unless --output is specified.
# Currently, 6 out of 116 cases are executed in agentsafetybench_executed.jsonl.
python scripts/generate_trajectories_agentsafetybench.py --limit 6

# Step 4: Run Strategy Adherence Evaluation
# NOTE: Currently 3 out of 15 strategy scenarios are executed in agentsafetybench_strategy_executed.jsonl.
python scripts/strategy_agent_agentsafetybench.py --limit 15
```

### 4. Interactive Agent CLI (Live User Prompting)
Allows users to input arbitrary tasks in natural language at runtime:
```powershell
python scripts/interactive_agent.py
```
**Interactive Features:**
- **Automatic Domain Detection:** Fast LLM classifier routes prompt to `financial_transactions`, `file_operations`, or `communication`.
- **Out-of-Domain Guardrail:** Rejects non-eligible prompts with a formatted alert box and re-prompts continuously.
- **Human-in-the-Loop Clarification:** When a prompt is ambiguous or lacks required parameters, the agent asks follow-up questions live in terminal.
- **Zero Dataset Re-runs:** References pre-executed dataset runs in memory (~1ms) without re-running past cases.
- **Cross-Benchmark Comparison:** Automatically matches and displays the closest benchmark scenario from ToolEmu and Agent-SafetyBench for side-by-side analysis.

---

## Output Inspection & Auditability

Every API interaction (system prompt, user prompt, raw response, token usage, latency) is permanently appended to dedicated audit logs:
- `data/processed/toolemu_api_audit.jsonl` — ToolEmu simulation and strategy calls.
- `data/processed/agentsafetybench_api_audit.jsonl` — Agent-SafetyBench simulation calls.
- `data/processed/agentsafetybench_strategy_audit.jsonl` — Agent-SafetyBench strategy calls.
