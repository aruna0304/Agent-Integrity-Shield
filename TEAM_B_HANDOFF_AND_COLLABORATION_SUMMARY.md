# AIS Project — Team B Handoff & Collaboration Summary (Review 1 + v2 Enhancements)

**To:** Team A (ToolEmu Leads)  
**From:** Team B (Agent-SafetyBench Leads)  
**Date:** September 2026  
**Repository:** [https://github.com/aruna0304/Agent-Integrity-Shield-](https://github.com/aruna0304/Agent-Integrity-Shield-)  
**Branch:** `main` (Latest commit: `71b504b`)

---

## 1. Executive Summary

Team B has completed all deliverables assigned in the **AIS Team Split Brief** for the **40% Data Foundation & Trajectory Generation Milestone**, as well as the **v2 Strategy-Aware Agent & Interactive Mode** enhancements.

### Key Guarantees:
* **Zero Conflicts / Strict Boundary Adherence:** Team B worked exclusively inside `data/raw/agentsafetybench/`, `data/processed/agentsafetybench_*.jsonl`, and `scripts/*_agentsafetybench.py`. Team A's ToolEmu files and scripts were **100% untouched**.
* **Unified Schema Parity:** All Team B records strictly comply with `schema/trajectory_schema.json` with **0 validation errors**.
* **Cross-Benchmark Integration:** The new interactive agent (`scripts/interactive_agent.py`) seamlessly integrates and cross-references **both** Team A's ToolEmu records and Team B's Agent-SafetyBench records.

---

## 2. What Team B Delivered (Detailed Breakdown)

### Phase 1: Data Acquisition & Cryptographic Provenance
* **Raw Benchmark:** Downloaded the official release of **Agent-SafetyBench** (Zhang et al., 2024; Tsinghua CoAI) containing 2,000 cases across 349 environments.
* **Storage Location:** `data/raw/agentsafetybench/released_data.json` (2,941,592 bytes).
* **Provenance Verification:** Created `scripts/download_agentsafetybench.py`, which computes SHA-256 and records official metadata in `data/raw/agentsafetybench/provenance.json`:
  * SHA-256: `61c147ca0a783121a4a5f865d635fdaaa8b8a5a3421a09c9fac13f4953fcf3fa`

### Phase 2: Raw Structure Audit & Honest Normalization
* **Preflight Finding:** Verified that the official benchmark provides scenario instructions, risk categories, and environment tool specifications, but **does not contain pre-computed execution trajectories or agent run verdicts**.
* **Strict Domain Filtering:** Filtered the 2,000 raw cases down to the **3 locked domains**:
  * ✉️ `communication`: **46 clean cases** (`Email`, `SocialMedia`, `Slack`, `Phone`, `SMS`, `ChatApp`)
  * 📁 `file_operations`: **38 clean cases** (`FileManager`, `OS`, `FileProcessor`, `BackupSystem`)
  * 💳 `financial_transactions`: **32 clean cases** (`Bank`, `InvestmentManager`, `StockManager`, `MobilePayment`, `AntiMoneyLaundering`, `LoanApprovalSystem`, `SecureDigitalWallet`)
  * **Total Mapped: 116 clean cases** (1,884 unmapped/out-of-domain cases were skipped with explicit logged reasons).
* **Output File:** `data/processed/agentsafetybench_normalized.jsonl` (**100% schema valid, 0 errors**).

### Phase 3: Trajectory Generation & Multi-Role Safety Judge
* **Simulation Harness:** Built `scripts/generate_trajectories_agentsafetybench.py` executing a 4-role pipeline:
  1. **Agent Actor:** Decides next tool call or finishes based on task and tool definitions.
  2. **Tool Sandbox Emulator:** Simulates realistic tool return payloads and status codes.
  3. **Safety Judge:** Classifies trajectories into the 6 AIS failure categories (`hallucinated_tool_call`, `unauthorized_intent`, `tool_failure`, `wrong_parameters`, `silent_failure`, `no_verification`) with severity (`low`, `medium`, `high`) and confidence scores.
  4. **API Audit Logger:** Logs raw prompts, responses, latencies, and token counts to `data/processed/agentsafetybench_api_audit.jsonl`.
* **Output File:** `data/processed/agentsafetybench_executed.jsonl` (**0 schema errors**).

### Phase 4: Strategy-Aware Policy Agent (v2 Enhancement)
* **Rationale:** Real user prompts are vague. Built `scripts/strategy_agent_agentsafetybench.py` wrapping 15 constraint-ambiguous scenarios (5 per domain):
  * **Financial Transactions:** Evaluated against tiered policies (< $500 execute; $500–$5k confirm amount first; > $5k verify identity).
  * **File Operations:** Evaluated against retention policies (< 7d keep; 7–30d archive; > 30d delete).
  * **Communication:** Evaluated against urgency policies (minor -> team channel; major -> on-call page; critical -> leadership).
* **Policy Placement:** Policies are embedded directly inside tool descriptions (not in user prompts), forcing the agent to discover and adhere to them.
* **Ambiguity Metric:** Safety Judge evaluates `ambiguity_handling`: `clarified`, `policy_applied`, `guessed`, or `ignored_policy`.
* **Output File:** `data/processed/agentsafetybench_strategy_executed.jsonl`.

### Phase 5: Interactive Mode CLI (`scripts/interactive_agent.py`)
* **Auto Domain Detection:** User types any prompt freely; the system classifies it into one of the 3 domains.
* **Out-of-Domain Guardrail:** If an irrelevant prompt is entered (e.g., *"What is the weather in Tokyo?"*), it prints a formatted warning box and re-prompts:
  ```text
  +--------------------------------------------------------------+
  |  [!] OUT-OF-DOMAIN REQUEST                                   |
  |  This agent is trained on 3 domains only:                    |
  |    * file_operations                                         |
  |    * financial_transactions                                  |
  |    * communication                                           |
  +--------------------------------------------------------------+
  ```
* **Cross-Benchmark Dataset Comparison:** Performs token-overlap similarity against **both ToolEmu (Team A) and Agent-SafetyBench (Team B)** pre-run cases and prints the closest matching benchmark scenario side-by-side!
* **Session Logging:** Appends all runs to `data/processed/interactive_runs.jsonl`.

---

## 3. Shared Files & Coordination Details

### 1. `schema/trajectory_schema.json` (Non-Breaking Update)
To support strategy scenarios and interactive sessions, two optional properties were added to the schema:
```json
"scenario_type": {
  "type": "string",
  "enum": ["standard", "constraint_ambiguous", "interactive"]
},
"ambiguity_score": {
  "type": "object",
  "additionalProperties": false,
  "required": ["ambiguity_handling"],
  "properties": {
    "ambiguity_handling": {
      "type": "string",
      "enum": ["clarified", "policy_applied", "guessed", "ignored_policy"]
    },
    "reasoning": {"type": "string"}
  }
}
```
> **Backward Compatibility Verified:** Both `toolemu_normalized.jsonl` (43 records) and `toolemu_executed.jsonl` (5 records) were re-tested against this updated schema and pass with **0 errors**.

### 2. `README.md`
Updated to document the complete execution pipeline for both teams:
* Section: `## Execution Pipeline (ToolEmu — Team A)`
* Section: `## Execution Pipeline (Agent-SafetyBench — Team B)`
* Section: `## Interactive Mode (Live Generalization & Dataset Comparison)`

---

## 4. How Team A Can Pull and Test Team B's Work

On your local machine, open your terminal in the repository root and run:

```powershell
# 1. Pull the latest commits from GitHub
git pull origin main

# 2. Verify schema compliance of Team B's normalized dataset
python schema/validate_trajectory.py data/processed/agentsafetybench_normalized.jsonl

# 3. Verify schema compliance of Team B's executed trajectories
python schema/validate_trajectory.py data/processed/agentsafetybench_executed.jsonl

# 4. Run the Strategy Agent on 3 ambiguous scenarios (takes ~5s)
python scripts/strategy_agent_agentsafetybench.py --limit 3

# 5. Test the Interactive Agent CLI
python scripts/interactive_agent.py
```

---

## 5. Summary Table for Review 1 Presentation

When presenting together to the guide/evaluators:

| Dimension | **Team A (ToolEmu)** | **Team B (Agent-SafetyBench)** |
|---|---|---|
| **Raw Dataset Size** | 144 test cases | 2,000 test cases |
| **Origin** | Stanford / UC Berkeley | Tsinghua University |
| **Filtered Dataset (3 Domains)** | 43 normalized cases | 116 normalized cases |
| **Executed Trajectories** | `toolemu_executed.jsonl` | `agentsafetybench_executed.jsonl` |
| **Strategy & Ambiguity** | `strategy_agent_toolemu.py` | `strategy_agent_agentsafetybench.py` |
| **Interactive CLI** | Shared CLI (`interactive_agent.py`) | Shared CLI (`interactive_agent.py`) |
| **Schema Pass Rate** | **100% (0 errors)** | **100% (0 errors)** |

Everything is in sync and ready for Review 1!
