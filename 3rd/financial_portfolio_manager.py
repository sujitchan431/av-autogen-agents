import os
from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager

# ─── LLM Configuration ───────────────────────────────────────────────────────

llm_config = {
    "config_list": [
        {
            "model": "gpt-4o",
            "api_key": os.environ.get("OPENAI_API_KEY", ""),
        }
    ],
    "temperature": 0.1,
    "cache_seed": None,
}

# ─── StateFlow Manager ────────────────────────────────────────────────────────

class StateFlowManager:
    """
    Tracks and prints state transitions throughout the portfolio workflow.

    States:
        INIT → PORTFOLIO_ANALYSIS → GROWTH_INVESTMENT | VALUE_INVESTMENT
             → INVESTMENT_ADVISORY → END
    """

    TRANSITIONS = {
        "INIT":                ["PORTFOLIO_ANALYSIS"],
        "PORTFOLIO_ANALYSIS":  ["GROWTH_INVESTMENT", "VALUE_INVESTMENT"],
        "GROWTH_INVESTMENT":   ["INVESTMENT_ADVISORY"],
        "VALUE_INVESTMENT":    ["INVESTMENT_ADVISORY"],
        "INVESTMENT_ADVISORY": ["END"],
    }

    def __init__(self):
        self.current_state   = "INIT"
        self.investment_path = None

    def transition(self, new_state: str):
        print(f"\n[StateFlow]  {self.current_state}  →  {new_state}")
        self.current_state = new_state

    def set_path(self, path: str):
        self.investment_path = path
        print(f"[StateFlow]  Investment path set to: {path}")


state_flow = StateFlowManager()

# ─── Agents ───────────────────────────────────────────────────────────────────

user_proxy = UserProxyAgent(
    name="User_Proxy",
    human_input_mode="NEVER",
    system_message=(
        "You are the User Proxy representing the investor. "
        "Your only job is to initiate the portfolio management process "
        "by presenting the user's financial information clearly."
    ),
    code_execution_config=False,
    max_consecutive_auto_reply=1,
)

portfolio_analysis_agent = AssistantAgent(
    name="Portfolio_Analysis_Agent",
    system_message="""You are an expert Portfolio Analysis Agent.

Your tasks:
1. Analyse the provided investment portfolio in full detail.
2. Calculate total portfolio value and asset-allocation percentages.
3. Assess the portfolio's risk profile (conservative / moderate / aggressive).
4. Decide the investment strategy:
   - Portfolio >60% in FDs, PPF, bonds, real estate → needs growth → GROWTH_INVESTMENT
   - Portfolio >60% in equities / equity MFs          → needs stability → VALUE_INVESTMENT
   - Mixed: assess based on overall risk balance.

Your reply MUST end with EXACTLY one of:
**WORKFLOW_DIRECTION: GROWTH_INVESTMENT**
**WORKFLOW_DIRECTION: VALUE_INVESTMENT**

Provide thorough analysis BEFORE the direction line.""",
    llm_config=llm_config,
)

growth_investment_agent = AssistantAgent(
    name="Growth_Investment_Agent",
    system_message="""You are a Growth Investment Specialist focused on high-growth opportunities.

Provide detailed recommendations covering:
1. Equity Mutual Funds – categories, specific fund types, allocation %
2. Direct Equity      – high-growth sectors, selection criteria
3. Emerging Sectors   – tech, green energy, EV, pharma, etc.
4. SIP Strategy       – recommended monthly amounts per instrument
5. Risk Management    – diversification rules and rebalancing frequency

Use Indian investment context (NSE/BSE, SEBI-registered instruments).
State expected returns and recommended time horizons for each category.""",
    llm_config=llm_config,
)

value_investment_agent = AssistantAgent(
    name="Value_Investment_Agent",
    system_message="""You are a Value Investment Specialist focused on stable, long-term wealth creation.

Provide detailed recommendations covering:
1. Blue-chip Stocks    – sectors, quality criteria, allocation %
2. Dividend Stocks     – high-yield consistent payers
3. Government/RBI Bonds, SGBs, T-bills
4. REITs               – listed Indian REITs
5. Conservative MFs    – large-cap, balanced advantage, debt hybrid

Use Indian investment context.
State stability ratings, expected yields, and recommended holding periods.""",
    llm_config=llm_config,
)

investment_advisor_agent = AssistantAgent(
    name="Investment_Advisor_Agent",
    system_message="""You are the Chief Investment Advisor who compiles the final financial report.

Using ALL information shared in this conversation, produce:

════════════════════════════════════════════════════
        PERSONALIZED FINANCIAL ADVISORY REPORT
════════════════════════════════════════════════════

## 1. CLIENT PROFILE

## 2. CURRENT PORTFOLIO ANALYSIS
   - Holdings breakdown with values and percentages
   - Portfolio strengths and gaps

## 3. INVESTMENT STRATEGY RATIONALE
   - Why Growth / Value was chosen

## 4. SPECIFIC INVESTMENT RECOMMENDATIONS
   - Itemised list with allocation %, instrument type, expected return

## 5. IMPLEMENTATION ROADMAP
   - Short-term  : 0–6 months
   - Medium-term : 6–24 months
   - Long-term   : 2+ years

## 6. RISK ASSESSMENT & MITIGATION

## 7. PROJECTED PORTFOLIO GROWTH
   - Conservative estimate
   - Optimistic estimate

## 8. IMMEDIATE NEXT STEPS

════════════════════════════════════════════════════

End your report with the word: TERMINATE""",
    llm_config=llm_config,
)

# ─── StateFlow Speaker-Selection Function ─────────────────────────────────────

def portfolio_state_flow(last_speaker, groupchat: GroupChat):
    """
    Implements StateFlow: deterministic, state-driven speaker transitions.

    Graph:
        User_Proxy
            ↓
        Portfolio_Analysis_Agent
            ↓ (GROWTH)              ↓ (VALUE)
        Growth_Investment_Agent   Value_Investment_Agent
                        ↓
              Investment_Advisor_Agent
                        ↓
                       END
    """
    messages = groupchat.messages

    # INIT → PORTFOLIO_ANALYSIS
    if last_speaker.name == "User_Proxy":
        state_flow.transition("PORTFOLIO_ANALYSIS")
        return portfolio_analysis_agent

    # PORTFOLIO_ANALYSIS → GROWTH or VALUE
    if last_speaker.name == "Portfolio_Analysis_Agent":
        last_content = messages[-1].get("content", "") if messages else ""

        if "WORKFLOW_DIRECTION: GROWTH_INVESTMENT" in last_content:
            state_flow.transition("GROWTH_INVESTMENT")
            state_flow.set_path("GROWTH")
            return growth_investment_agent

        if "WORKFLOW_DIRECTION: VALUE_INVESTMENT" in last_content:
            state_flow.transition("VALUE_INVESTMENT")
            state_flow.set_path("VALUE")
            return value_investment_agent

        # Fallback keyword detection
        lower = last_content.lower()
        if any(kw in lower for kw in ["growth", "equity", "aggressive", "high-risk"]):
            state_flow.transition("GROWTH_INVESTMENT")
            state_flow.set_path("GROWTH")
            return growth_investment_agent

        state_flow.transition("VALUE_INVESTMENT")
        state_flow.set_path("VALUE")
        return value_investment_agent

    # GROWTH / VALUE → INVESTMENT_ADVISORY
    if last_speaker.name in ("Growth_Investment_Agent", "Value_Investment_Agent"):
        state_flow.transition("INVESTMENT_ADVISORY")
        return investment_advisor_agent

    # INVESTMENT_ADVISORY → END
    if last_speaker.name == "Investment_Advisor_Agent":
        state_flow.transition("END")
        return None

    return None


# ─── Group Chat Setup ─────────────────────────────────────────────────────────

groupchat = GroupChat(
    agents=[
        user_proxy,
        portfolio_analysis_agent,
        growth_investment_agent,
        value_investment_agent,
        investment_advisor_agent,
    ],
    messages=[],
    max_round=8,
    speaker_selection_method=portfolio_state_flow,
    allow_repeat_speaker=False,
)

manager = GroupChatManager(
    groupchat=groupchat,
    llm_config=llm_config,
    is_termination_msg=lambda msg: "TERMINATE" in msg.get("content", ""),
)

# ─── Entry Point ──────────────────────────────────────────────────────────────

INITIAL_MESSAGE = """Hello! I need help managing my investment portfolio.

Here are my financial details:

Monthly Salary : ₹1,20,000

Current Investment Portfolio:
  • Fixed Deposits (FDs)                : ₹5,00,000
  • SIP – Mutual Funds (equity-oriented): ₹2,00,000
  • Real Estate                         : ₹30,00,000
  • Direct Stocks (NSE/BSE)             : ₹1,50,000
  • PPF (Public Provident Fund)         : ₹3,00,000
  • Gold ETF                            : ₹50,000

Total Portfolio Value : ₹42,00,000

Please analyse my portfolio and provide personalised investment recommendations."""


def main():
    print("=" * 60)
    print("   FINANCIAL PORTFOLIO MANAGER")
    print("   AutoGen  ·  Group Chat  ·  StateFlow")
    print("=" * 60)

    user_proxy.initiate_chat(
        manager,
        message=INITIAL_MESSAGE,
    )

    # ── Print final Investment Advisor report ──
    print("\n" + "=" * 60)
    print("   INVESTMENT ADVISOR – FINAL REPORT")
    print("=" * 60)

    for msg in reversed(groupchat.messages):
        if msg.get("name") == "Investment_Advisor_Agent":
            content = msg.get("content", "").replace("TERMINATE", "").strip()
            print(content)
            break


if __name__ == "__main__":
    main()
