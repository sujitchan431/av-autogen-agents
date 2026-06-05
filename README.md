<div align="center">

# 🤝 AutoGen AI Agents — 4 Multi-Agent Patterns

[![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python)](https://python.org)
[![AutoGen](https://img.shields.io/badge/AutoGen-0.4.x-purple)](https://microsoft.github.io/autogen/)
[![Claude](https://img.shields.io/badge/Claude-Haiku_4.5-blueviolet)](https://anthropic.com)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-412991?logo=openai)](https://openai.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> Four AutoGen projects demonstrating Reflection, FunctionTool, StateFlow, and Multi-modal agent patterns.

**🎓 Part of the [Analytics Vidhya GenAI Pinnacle Plus Program](https://www.analyticsvidhya.com/)**

</div>

---

## 📋 Overview

Progressive series of AutoGen multi-agent systems, each introducing a new design pattern — from a two-agent reflection loop to a multi-modal bill analyzer that processes real receipt images.

---

## 📁 Sub-Projects

```
AutoGen Ai Agents/
├── 1st/  ← Smart Content Creation (Reflection Pattern)
├── 2nd/  ← Smart Health Assistant (FunctionTool + BMI)
├── 3rd/  ← Financial Portfolio Manager (StateFlow)
└── 4th/  ← Bill Managing Agent (Multi-modal + SelectorGroupChat)
```

---

## 🛠️ Tech Stack

| Technology | Used In |
|-----------|---------|
| `autogen_agentchat` (new API) | Sub-1, Sub-2, Sub-4 |
| `autogen` (classic API) | Sub-3 |
| Claude Haiku 4.5 | Sub-1, Sub-2, Sub-4 |
| GPT-4o | Sub-3 |
| PIL (Pillow) | Sub-4 (receipt generation) |

---

## 🔄 Sub-1 — Reflection Pattern (Content Creation)

**Two agents:** ContentCreator ↔ ContentCritic  
**Topic:** Agentic AI — comprehensive technical piece  
**Loop:** Creator drafts → Critic evaluates (clarity/accuracy/structure) → Creator revises → repeat  
**Termination:** `TextMentionTermination("FINAL DRAFT")` OR `MaxMessageTermination(10)`  
**Output:** `output.md` — polished content piece

```python
team = RoundRobinGroupChat(
    participants=[content_creator, content_critic],
    termination_condition=termination,
)
```

---

## 🏥 Sub-2 — FunctionTool (Health Assistant)

**Custom tool:** `calculate_bmi(weight_kg, height_cm)` → BMI score + category  
**Flow:** CLI collects user profile → agent analyzes with BMI tool → personalized advice

```python
bmi_tool = FunctionTool(calculate_bmi, description="...")
agent = AssistantAgent(name="HealthAgent", tools=[bmi_tool])
```

---

## 💰 Sub-3 — StateFlow (Portfolio Manager)

**5 agents** in a conditional workflow:

```
INIT → Portfolio_Analysis_Agent
    → GROWTH_INVESTMENT (if >60% FDs/bonds)
    → VALUE_INVESTMENT  (if >60% equities)
    → Investment_Advisory_Agent → END
```

---

## 🧾 Sub-4 — Multi-modal (Bill Manager)

- Generates a realistic Walmart receipt as a PIL image
- Sends as `MultiModalMessage` to `SelectorGroupChat`
- Agents analyze spending categories from the image

---

## ⚙️ Setup

```bash
pip install autogen-agentchat autogen-ext[anthropic] pillow
```

```bash
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...  # for sub-3
```

---

## 💡 Key Learnings

- **Reflection pattern** — two-agent critic-creator loop for quality improvement
- **FunctionTool** — registering Python functions as callable agent tools
- **StateFlow** — explicit state transitions with conditional branching
- **Multi-modal messages** — sending PIL images to vision LLMs via AutoGen
- **SelectorGroupChat** vs **RoundRobinGroupChat** — dynamic vs round-robin routing
- **Termination conditions** — combining text-mention + message-count conditions
- Windows UTF-8 fix for Claude response encoding

---

## 🎓 Program Context

**Analytics Vidhya GenAI Pinnacle Plus Program** — AutoGen Multi-Agent Framework module.

---

## 📄 License

MIT © 2026 [sujitchan431](https://github.com/sujitchan431)
