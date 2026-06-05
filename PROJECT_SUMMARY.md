# AutoGen AI Agents — 4 Sub-Projects

## Project Overview

Four distinct AutoGen multi-agent projects demonstrating different agent patterns: reflection, tool-use, StateFlow, and multi-modal.

## Sub-Project Structure

```
AutoGen Ai Agents/
├── 1st/  ← Smart Content Creation (Reflection Pattern)
├── 2nd/  ← Smart Health Assistant (FunctionTool + User Proxy)
├── 3rd/  ← Financial Portfolio Manager (StateFlow + GroupChat)
└── 4th/  ← Bill Managing Agent (Multi-modal image + SelectorGroupChat)
```

---

## Sub-Project 1 — Smart Content Creation (Reflection Pattern)

**File:** `smart_content_creation.py`  
**Topic:** Agentic AI content piece

**Pattern:** Two-agent reflection loop — Creator drafts, Critic evaluates, Creator revises.

| Agent | Role |
|-------|------|
| `ContentCreator` | Draft + revise on Agentic AI |
| `ContentCritic` | Evaluate: clarity, accuracy, structure, suggestions |

**Orchestration:** `RoundRobinGroupChat`, max 5 turns  
**Termination:** `TextMentionTermination("FINAL DRAFT")` OR `MaxMessageTermination(10)`  
**LLM:** Claude Haiku 4.5 via `AnthropicChatCompletionClient`  
**Output:** Final polished content piece saved to `output.md`

---

## Sub-Project 2 — Smart Health Assistant (FunctionTool)

**File:** `smart_health_assistant.py`

**Pattern:** Single agent with custom `FunctionTool` + interactive user data collection.

**Tools:**
- `calculate_bmi(weight_kg, height_cm)` → BMI score + category (Underweight/Normal/Overweight/Obese)

**Flow:** CLI collects weight, height, age, gender → constructs health profile → agent analyzes with BMI tool → personalized health advice

**LLM:** Claude Haiku 4.5

---

## Sub-Project 3 — Financial Portfolio Manager (StateFlow)

**File:** `financial_portfolio_manager.py`  
**LLM:** GPT-4o via OpenAI

**Pattern:** StateFlow with conditional branching + GroupChat

**StateFlow transitions:**
```
INIT → PORTFOLIO_ANALYSIS 
    → GROWTH_INVESTMENT | VALUE_INVESTMENT  (based on portfolio composition)
    → INVESTMENT_ADVISORY → END
```

| Agent | Purpose |
|-------|---------|
| `User_Proxy` | Presents investor financial data |
| `Portfolio_Analysis_Agent` | Analyzes portfolio, decides GROWTH vs VALUE path |
| `Growth_Investment_Agent` | Recommends high-growth investments |
| `Value_Investment_Agent` | Recommends stable value investments |
| `Investment_Advisory_Agent` | Final consolidated advice |

**Decision logic:** >60% FDs/bonds → GROWTH path; >60% equities → VALUE path

---

## Sub-Project 4 — Bill Managing Agent (Multi-modal)

**File:** `bill_managing_agent.py`

**Pattern:** Multi-modal agent with `SelectorGroupChat`, processes receipt images.

**Features:**
- Generates a realistic sample grocery receipt as a PIL image (Walmart Supercenter, $100+ bill)
- Sends image as `MultiModalMessage` to agents
- `SelectorGroupChat` routes to specialized agents

**LLM:** Claude Haiku 4.5  
**Termination:** `TextMentionTermination("ANALYSIS_COMPLETE")` OR `MaxMessageTermination`

---

## Tech Stack Summary

| Technology | Used In |
|-----------|---------|
| AutoGen (`autogen_agentchat`) | Sub-1, Sub-2, Sub-4 |
| AutoGen classic (`autogen`) | Sub-3 |
| Anthropic Claude Haiku 4.5 | Sub-1, Sub-2, Sub-4 |
| OpenAI GPT-4o | Sub-3 |
| `FunctionTool` | Sub-2 |
| `SelectorGroupChat` | Sub-4 |
| `RoundRobinGroupChat` | Sub-1 |
| PIL (Pillow) | Sub-4 (receipt generation) |

## Work Completed

- [x] Reflection pattern with critic-creator loop + termination on "FINAL DRAFT"
- [x] Custom FunctionTool (BMI calculator) integrated with health agent
- [x] StateFlow with conditional branching (4 states, 5 agents)
- [x] Multi-modal bill analysis (generated receipt image → agents)
- [x] Windows UTF-8 encoding fix for Claude responses

## Complexity

**High** — Four distinct patterns: reflection, tool-use, stateful multi-agent workflow, and multi-modal. Three different LLMs used across sub-projects.
