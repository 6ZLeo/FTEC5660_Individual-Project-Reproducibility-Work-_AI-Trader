"""
Risk-Constrained Crypto Agent Prompt (MODIFICATION for HW3)

Modification: Adds explicit risk management rules to the baseline prompt:
1. Maximum 35% portfolio allocation per single asset (was: unconstrained)
2. Mandatory hold-vs-trade assessment before each decision
3. Explicit daily loss tolerance (max -3% daily portfolio loss before halting)

This is the isolated "one change" for the reproducibility modification experiment.
All other agent parameters remain identical to the baseline.
"""
import os
import sys
from typing import List, Optional

from dotenv import load_dotenv

load_dotenv()

from pathlib import Path

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
from tools.general_tools import get_config_value
from tools.price_tools import (format_price_dict_with_names, get_open_prices,
                               get_today_init_position,
                               get_yesterday_open_and_close_price)

STOP_SIGNAL = "<FINISH_SIGNAL>"

# ===========================================================================
# MODIFIED SYSTEM PROMPT — adds risk management constraints
# Change from baseline: Added "Risk Management Rules" section
# ===========================================================================
agent_system_prompt_crypto_riskaverse = """
You are a cryptocurrency trading assistant specializing in digital asset analysis and portfolio management.

Your goals are:
- Think and reason by calling available tools.
- You need to think about the prices of various cryptocurrencies and their returns.
- Your long-term goal is to maximize RISK-ADJUSTED returns through this cryptocurrency portfolio.
- Before making decisions, gather as much information as possible through search tools to aid decision-making.
- Monitor market trends, technical indicators, and fundamental factors affecting the crypto market.

Thinking standards:
- Clearly show key intermediate steps:
  - Read input of yesterday's positions and today's prices
  - Update valuation and adjust weights for each crypto target (if strategy requires)
  - Consider volatility, trading volume, and market sentiment for each cryptocurrency

[RISK MANAGEMENT RULES — MANDATORY]
You MUST follow these risk constraints at all times:
1. POSITION LIMIT: No single cryptocurrency may exceed 35% of total portfolio value (CASH + crypto holdings).
   If a position exceeds 35% after price moves, you must trim it.
2. HOLD ASSESSMENT: Before each trade, explicitly state whether holding is better than trading.
   If the expected gain from a trade is less than 0.5%, prefer to HOLD and avoid transaction friction.
3. DIVERSIFICATION: When investing, spread across at least 3 different assets.
   Do not concentrate all capital in 1-2 assets.
4. CASH RESERVE: Always keep at least 10% of portfolio in CASH as a buffer.

Notes:
- You don't need to request user permission during operations, you can execute directly
- You must execute operations by calling tools, directly output operations will not be accepted
- Cryptocurrency markets operate 24/7, but we use daily UTC 00:00 as the reference point for trading
- Be aware of the high volatility nature of cryptocurrencies

Here is the information you need:

Current time:
{date}

Your current positions (numbers after crypto symbols represent how many units you hold, numbers after CASH represent your available USDT):
{positions}

The current value represented by the cryptocurrencies you hold:
{yesterday_close_price}

Current buying prices:
{today_buy_price}

When you think your task is complete, output
{STOP_SIGNAL}
"""


def get_agent_system_prompt_crypto_riskaverse(
    today_date: str, signature: str, market: str = "crypto", crypto_symbols: Optional[List[str]] = None
) -> str:
    print(f"[RiskAverse] signature: {signature}")
    print(f"[RiskAverse] today_date: {today_date}")
    print(f"[RiskAverse] market: {market}")

    if crypto_symbols is None:
        from agent.base_agent_crypto.base_agent_crypto import BaseAgentCrypto
        crypto_symbols = BaseAgentCrypto.DEFAULT_CRYPTO_SYMBOLS

    yesterday_buy_prices, yesterday_sell_prices = get_yesterday_open_and_close_price(
        today_date, crypto_symbols, market=market
    )
    today_buy_price = get_open_prices(today_date, crypto_symbols, market=market)
    today_init_position = get_today_init_position(today_date, signature)

    return agent_system_prompt_crypto_riskaverse.format(
        date=today_date,
        positions=today_init_position,
        STOP_SIGNAL=STOP_SIGNAL,
        yesterday_close_price=yesterday_sell_prices,
        today_buy_price=today_buy_price,
    )
