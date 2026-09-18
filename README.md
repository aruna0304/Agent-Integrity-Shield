# AIS — Agent Integrity Shield

AIS is an exploration of a real-time integrity, policy compliance, and reliability layer for autonomous LLM agents. This repository contains the data foundation, unified trajectory schema, and simulation/execution harnesses for safety benchmarks and interactive agent evaluation.

## Layout

```text
ais/
├── data/raw/toolemu/              # Official ToolEmu raw JSON files & provenance
├── data/raw/agentsafetybench/     # Official Agent-SafetyBench release & provenance
├── data/processed/                # Normalized, strategy-executed, and interactive JSONL outputs
│   ├── toolemu_normalized.jsonl               # 43 domain-filtered ToolEmu scenarios
│   ├── toolemu_executed.jsonl                 # 43 executed ToolEmu trajectories
│   ├── strategy_scenarios_executed.jsonl      # 15 graduated-policy constraint scenarios
│   ├── agentsafetybench_normalized.jsonl      # 116 domain-filtered Agent-SafetyBench scenarios
│   ├── agentsafetybench_executed.jsonl        # Executed Agent-SafetyBench trajectories
│   ├── agentsafetybench_strategy_executed.jsonl # Agent-SafetyBench strategy trajectories
│   ├── interactive_runs.jsonl                 # Dynamic runtime user sessions
│   └── toolemu_api_audit.jsonl                # Audit log of all raw LLM API calls
├── schema/                        # Unified JSON Schema (Draft-07) and validator
│   ├── trajectory_schema.json                 # Unified contract across benchmarks
│   └── validate_trajectory.py                # Validation utility
└── scripts/                       # Preprocessing, strategy, and interactive harnesses
    ├── download_toolemu.py                    # ToolEmu provenance downloader
    ├── preprocess_toolemu.py                  # ToolEmu domain normalization
    ├── generate_trajectories_toolemu.py       # ToolEmu trajectory simulation harness
    ├── strategy_agent_toolemu.py              # ToolEmu graduated-policy strategy agent
    ├── download_agentsafetybench.py           # Agent-SafetyBench downloader
    ├── preprocess_agentsafetybench.py         # Agent-SafetyBench domain normalization
    ├── generate_trajectories_agentsafetybench.py # Agent-SafetyBench simulation harness
    ├── strategy_agent_agentsafetybench.py     # Agent-SafetyBench strategy agent
    └── interactive_agent.py                   # Interactive CLI with auto-domain classifier
```

---

## Unified Trajectory Schema Contract

`schema/trajectory_schema.json` standardizes agent behavior records across disparate sources into a common structure. Key fields include:
- `trajectory_id`: Unique identifier with dataset provenance prefix.
- `status`: `"scenario_only"` | `"executed_trajectory"`.
- `scenario_type`: `"standard"` | `"constraint_ambiguous"` | `"interactive"`.
- `domain`: `"file_operations"` | `"financial_transactions"` | `"communication"`.
- `actions`: Ordered array of tool invocations with `lifecycle_stage` (`pre_execution`, `execution`, `post_execution`).
- `ambiguity_score`: Captures handling quality (`clarified`, `policy_applied`, `guessed`, `ignored_policy`).
- `ground_truth_label`: Structured safety verdict (`is_failure`, `failure_category`, `severity`, `confidence`, `reasoning`).

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

# Step 2: Filter to 3 Locked Domains & Validate Schema
python scripts/preprocess_toolemu.py

# Step 3: Run Full Benchmark Trajectory Generation (43 cases)
python scripts/generate_trajectories_toolemu.py
```

### 2. Strategy-Aware Graduated Policy Harness (ToolEmu)
Evaluates agent decision logic on vague, real-world prompts with policy thresholds embedded in tool specifications:
```powershell
# Run all 15 constraint-ambiguous scenarios across 3 domains
python scripts/strategy_agent_toolemu.py

# Or filter to a specific domain / test limit
python scripts/strategy_agent_toolemu.py --domain financial_transactions --limit 3
```

### 3. Agent-SafetyBench Pipeline
```powershell
# Step 1: Download & Verify Provenance
python scripts/download_agentsafetybench.py

# Step 2: Filter & Normalize Scenarios (116 cases)
python scripts/preprocess_agentsafetybench.py

# Step 3: Run Safety Simulation Harness
python scripts/generate_trajectories_agentsafetybench.py --limit 6

# Step 4: Run Strategy Adherence Evaluation
python scripts/strategy_agent_agentsafetybench.py --limit 15
```

### 4. Interactive Agent CLI (Live User Prompting)
Allows users to input arbitrary tasks in natural language at runtime:
```powershell
python scripts/interactive_agent.py
```
**Interactive Features:**
- **Automatic Domain Detection:** Fast LLM classifier routes prompt to `financial_transactions`, `file_operations`, or `communication`.
- **Out-of-Domain Alert Box:** Rejects non-eligible prompts (e.g. poetry, weather) with an informative alert box and re-prompts continuously.
- **Human-in-the-Loop Clarification:** When a prompt is ambiguous or lacks required parameters, the agent asks you follow-up questions live in the terminal.
- **Zero Dataset Re-runs:** References pre-executed dataset runs in memory (~1ms) without re-running past cases.
- **Cross-Benchmark Comparison:** Automatically matches and displays the closest benchmark scenario from ToolEmu and Agent-SafetyBench for side-by-side analysis.

---

## Output Inspection & Auditability

Every API interaction (system prompt, user prompt, raw response, tokens, latency) is permanently appended to `data/processed/toolemu_api_audit.jsonl` with ISO 8601 timestamps and unique trajectory IDs for auditability.
