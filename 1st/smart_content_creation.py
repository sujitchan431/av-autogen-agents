"""
Smart Content Creation using AutoGen Reflection Pattern
Two-agent conversation: Content Creator <-> Content Critic
Topic: Agentic AI
"""

import asyncio
import os
import sys

# Force UTF-8 output on Windows to handle Unicode characters in LLM responses
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr.encoding != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.ui import Console
from autogen_ext.models.anthropic import AnthropicChatCompletionClient

# ── Model client ──────────────────────────────────────────────────────────────
model_client = AnthropicChatCompletionClient(
    model="claude-haiku-4-5-20251001",
    api_key=os.environ.get("ANTHROPIC_API_KEY"),
)

# ── Agent definitions ─────────────────────────────────────────────────────────
content_creator = AssistantAgent(
    name="ContentCreator",
    model_client=model_client,
    system_message=(
        "You are the Content Creator Agent. Your role is to draft content on topics involving "
        "Generative AI — specifically Agentic AI. Ensure the content is clear, concise, and "
        "technically accurate. On first turn draft the initial content. On subsequent turns "
        "revise your draft based on the critic's feedback. When you are satisfied with the "
        "final draft after at least one revision cycle, end your message with 'FINAL DRAFT'."
    ),
)

content_critic = AssistantAgent(
    name="ContentCritic",
    model_client=model_client,
    system_message=(
        "You are the Content Critic Agent. Your role is to evaluate content drafted by the "
        "Content Creator Agent on Agentic AI. Provide structured feedback covering: "
        "(1) Language clarity and readability, "
        "(2) Technical accuracy and depth, "
        "(3) Structure and flow, "
        "(4) Specific suggestions for improvement. "
        "Be constructive and precise. After the creator submits a revised draft, evaluate "
        "it again and acknowledge improvements before giving final recommendations."
    ),
)

# ── Termination conditions ────────────────────────────────────────────────────
termination = (
    TextMentionTermination("FINAL DRAFT")
    | MaxMessageTermination(max_messages=10)  # safety cap (5 turns = 10 messages)
)

# ── Team / orchestration ──────────────────────────────────────────────────────
team = RoundRobinGroupChat(
    participants=[content_creator, content_critic],
    termination_condition=termination,
    max_turns=5,
)


async def main() -> None:
    print("=" * 70)
    print("  SMART CONTENT CREATION - Reflection-Based Agentic Pattern")
    print("  Topic: Agentic AI")
    print("=" * 70)
    print()

    task = (
        "Draft a comprehensive, technically accurate piece of content about "
        "Agentic AI - covering what it is, how it works, key architectural "
        "patterns (reflection, tool use, planning, multi-agent collaboration), "
        "real-world applications, and future outlook. "
        "The audience is technically literate but not AI researchers."
    )

    # Collect messages for markdown export
    messages = []
    async for msg in team.run_stream(task=task):
        source = getattr(msg, "source", None)
        content = getattr(msg, "content", None)
        if source and content and isinstance(content, str):
            print(f"\n{'='*70}")
            print(f"  {source}")
            print(f"{'='*70}")
            print(content)
            messages.append((source, content))

    # Write markdown output
    with open("output.md", "w", encoding="utf-8") as f:
        f.write("# Smart Content Creation — Agentic AI\n")
        f.write("## Reflection-Based Multi-Agent Conversation\n\n")
        f.write("---\n\n")
        for source, content in messages:
            role = "Content Creator Agent" if source == "ContentCreator" else "Content Critic Agent"
            f.write(f"### {role}\n\n")
            f.write(content.strip())
            f.write("\n\n---\n\n")

    print("\n\nMarkdown output saved to output.md")


if __name__ == "__main__":
    asyncio.run(main())
