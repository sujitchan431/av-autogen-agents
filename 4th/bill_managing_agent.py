import asyncio
import os
from typing import Sequence

from PIL import Image as PILImage, ImageDraw, ImageFont

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import (
    BaseAgentEvent,
    BaseChatMessage,
    Image,
    MultiModalMessage,
)
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.ui import Console
from autogen_ext.models.anthropic import AnthropicChatCompletionClient


# ── Sample Receipt Generator ──────────────────────────────────────────────────

def create_sample_bill() -> PILImage.Image:
    """Draw a realistic sample grocery + household receipt for demo use."""
    W, H = 420, 780
    img = PILImage.new("RGB", (W, H), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    try:
        font_lg = ImageFont.truetype("arial.ttf", 18)
        font_md = ImageFont.truetype("arial.ttf", 14)
        font_sm = ImageFont.truetype("arial.ttf", 12)
    except OSError:
        font_lg = font_md = font_sm = ImageFont.load_default()

    y = [20]  # mutable for nested closure

    def center(text, font):
        bbox = draw.textbbox((0, 0), text, font=font)
        x = (W - (bbox[2] - bbox[0])) // 2
        draw.text((x, y[0]), text, fill=(0, 0, 0), font=font)
        y[0] += 22

    def left(text, font=font_md):
        draw.text((20, y[0]), text, fill=(0, 0, 0), font=font)
        y[0] += 20

    def rule():
        draw.line([(20, y[0]), (W - 20, y[0])], fill=(100, 100, 100), width=1)
        y[0] += 8

    center("WALMART SUPERCENTER", font_lg)
    center("1234 Oak Avenue, Chicago, IL 60601", font_sm)
    center("Date: 15-Dec-2024   Time: 14:32", font_sm)
    center("Receipt No: 0045-7821-3301", font_sm)
    rule()

    left("GROCERIES", font_sm)
    left("  Whole Milk 2L                  $3.49")
    left("  Whole Wheat Bread              $2.99")
    left("  Eggs (12 pack)                 $4.29")
    left("  Chicken Breast 2lb             $8.99")
    left("  Apples Bag 3lb                 $5.49")
    left("  Basmati Rice 5lb               $6.99")
    left("  Greek Yogurt 32oz              $5.29")
    rule()

    left("DINING / READY MEALS", font_sm)
    left("  Rotisserie Chicken            $12.99")
    left("  Caesar Salad Kit               $4.49")
    left("  Frozen Pizza (2pk)             $8.99")
    rule()

    left("UTILITIES / HOUSEHOLD", font_sm)
    left("  Dish Soap 32oz                 $3.29")
    left("  Paper Towels 6-pk              $7.99")
    left("  Laundry Detergent 64oz        $11.49")
    left("  Sponges 3-pk                   $2.49")
    rule()

    left("ENTERTAINMENT", font_sm)
    left("  Party Mix Chips 18oz           $4.99")
    left("  Cola Soda 12-pk                $5.99")
    left("  Scented Candle                 $6.49")
    rule()

    left("SHOPPING / PERSONAL CARE", font_sm)
    left("  Shampoo 12oz                   $5.49")
    left("  Toothpaste 2-pk                $3.29")
    left("  Moisturizer SPF30             $12.99")
    rule()

    left("  SUBTOTAL                     $128.30", font_md)
    left("  TAX (8%)                      $10.26", font_md)
    draw.line([(20, y[0]), (W - 20, y[0])], fill=(0, 0, 0), width=2)
    y[0] += 8
    left("  TOTAL                        $138.56", font_lg)
    y[0] += 6
    left("  PAYMENT: VISA ****4521", font_sm)
    y[0] += 4
    center("Thank you for shopping with us!", font_sm)

    return img


# ── Selector: enforces BillProcessingAgent → ExpenseSummarizationAgent order ──

def sequential_selector(
    messages: Sequence[BaseAgentEvent | BaseChatMessage],
) -> str | None:
    agent_speakers = [
        m.source
        for m in messages
        if hasattr(m, "source") and m.source not in ("UserProxy", "user", "User")
    ]
    if not agent_speakers:
        return "BillProcessingAgent"
    if agent_speakers[-1] == "BillProcessingAgent":
        return "ExpenseSummarizationAgent"
    return None  # termination condition takes over after ExpenseSummarizationAgent


# ── Image Loader ──────────────────────────────────────────────────────────────

def load_user_image(path: str) -> PILImage.Image | None:
    try:
        return PILImage.open(path).convert("RGB")
    except Exception as exc:
        print(f"  [Error] Cannot open '{path}': {exc}")
        return None


# ── Main Workflow ─────────────────────────────────────────────────────────────

async def run_bill_manager() -> None:
    print("\n" + "=" * 62)
    print("   BILL MANAGING AGENT  |  AutoGen Group Chat Collaboration")
    print("=" * 62)

    # ── User Proxy: Collect bill image ────────────────────────────────────────
    print("\n  USER PROXY AGENT")
    print("  " + "-" * 56)
    print("  Enter path to a bill/receipt image (JPG, PNG, etc.)")
    print("  or press Enter to use the built-in sample receipt.\n")

    raw_path = input("  Bill image path [Enter = sample]: ").strip()

    if raw_path:
        pil_img = load_user_image(raw_path)
        if pil_img is None:
            print("  [Fallback] Loading built-in sample receipt instead.")
            pil_img = create_sample_bill()
            image_label = "sample Walmart receipt (fallback)"
        else:
            image_label = f"uploaded receipt: {raw_path}"
    else:
        pil_img = create_sample_bill()
        image_label = "sample Walmart receipt (demo)"
        print("  [Info] Using built-in sample Walmart receipt.")

    print(f"\n  Sending '{image_label}' to Group Chat Manager...")
    print("=" * 62 + "\n")

    # ── Model Client ──────────────────────────────────────────────────────────
    model_client = AnthropicChatCompletionClient(
        model="claude-sonnet-4-6",
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
    )

    # ── Bill Processing Agent ─────────────────────────────────────────────────
    bill_processing_agent = AssistantAgent(
        name="BillProcessingAgent",
        model_client=model_client,
        system_message=(
            "You are the Bill Processing Agent in a bill management system.\n"
            "Your job: extract every line item from the bill/receipt image provided "
            "and organize expenses into categories.\n\n"
            "Valid categories: Groceries | Dining | Utilities | Shopping | Entertainment\n"
            "Assign each item to the closest matching category.\n\n"
            "Required output format:\n\n"
            "## Bill Processing Report\n\n"
            "**Source:** <store or merchant name>\n"
            "**Date:** <date if visible, else 'Not shown'>\n"
            "**Receipt #:** <number if visible>\n\n"
            "### Categorized Expenses\n\n"
            "| Category | Item | Amount |\n"
            "|----------|------|--------|\n"
            "| Groceries | Whole Milk 2L | $3.49 |\n"
            "| ... | ... | ... |\n\n"
            "### Category Totals\n"
            "| Category | Total |\n"
            "|----------|-------|\n"
            "| Groceries | $XX.XX |\n"
            "| Dining | $XX.XX |\n"
            "| Utilities | $XX.XX |\n"
            "| Shopping | $XX.XX |\n"
            "| Entertainment | $XX.XX |\n\n"
            "**Grand Total: $XX.XX**\n\n"
            "End your response with exactly: BILL PROCESSING COMPLETE"
        ),
    )

    # ── Expense Summarization Agent ───────────────────────────────────────────
    expense_summarization_agent = AssistantAgent(
        name="ExpenseSummarizationAgent",
        model_client=model_client,
        system_message=(
            "You are the Expense Summarization Agent in a bill management system.\n"
            "You receive structured expense data from the Bill Processing Agent.\n"
            "Your job: analyze spending patterns and provide actionable insights.\n\n"
            "Required output format:\n\n"
            "## Expense Summary & Spending Insights\n\n"
            "### 1. Spending Breakdown (ranked by amount)\n"
            "List all categories highest-to-lowest with amount and % of total.\n\n"
            "### 2. Highest Spending Category\n"
            "Name the top category, its total, percentage, and which items drove the cost.\n\n"
            "### 3. Spending Trends & Unusual Patterns\n"
            "Highlight any items that seem unusually expensive, any category that is "
            "disproportionately large, or any notable spending pattern.\n\n"
            "### 4. Budget Recommendations\n"
            "Provide 3 specific, actionable tips to reduce or optimize spending "
            "based on the actual bill data.\n\n"
            "Be concrete — reference actual item names and prices from the bill.\n\n"
            "End your response with exactly: TERMINATE"
        ),
    )

    # ── Termination Condition ─────────────────────────────────────────────────
    termination = TextMentionTermination("TERMINATE") | MaxMessageTermination(8)

    # ── Group Chat Team ───────────────────────────────────────────────────────
    team = SelectorGroupChat(
        participants=[bill_processing_agent, expense_summarization_agent],
        model_client=model_client,
        termination_condition=termination,
        selector_func=sequential_selector,
        allow_repeated_speaker=False,
    )

    # ── Task: User Proxy shares the bill image ────────────────────────────────
    task = MultiModalMessage(
        content=[
            (
                "Process this bill/receipt image. "
                "Extract all items, categorize them, and compute totals per category.\n"
                f"Source: {image_label}"
            ),
            Image(pil_img),
        ],
        source="UserProxy",
    )

    # ── Run Group Chat ────────────────────────────────────────────────────────
    await Console(team.run_stream(task=task))

    print("\n" + "=" * 62)
    print("   Bill Managing Agent — Session Complete")
    print("=" * 62 + "\n")


if __name__ == "__main__":
    asyncio.run(run_bill_manager())
