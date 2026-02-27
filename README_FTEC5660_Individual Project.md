# FTEC5660 HW3: Reproducibility Study — AI-Trader

**Student:** LingtengZeng (1155241166)  
**Course:** FTEC5660 Agentic AI for Business and FinTech  
**Assignment:** Homework 3 — Reproducibility Work  
**Paper:** [AI-Trader: Benchmarking Autonomous Agents in Real-Time Financial Markets](https://arxiv.org/abs/2512.10971) (Fan et al., 2025)  
**Original Repo:** https://github.com/HKUDS/AI-Trader  

---

## What This Fork Does

This fork reproduces **Table 1 (Cryptocurrency Market Performance)** from the AI-Trader paper, then makes one modification: adding **explicit risk management rules** to the agent's system prompt.

### Summary of Results

| Experiment | CR (%) | MDD (%) | Win Rate |
|---|---|---|---|
| Paper's DeepSeek-V3.1 | -12.18 | -14.02 | 52.9% |
| My Reproduced Baseline | -15.25 | -15.77 | 53.4% |
| **Risk-Averse Modification** | **-17.12** | **-17.60** | **50.0%** |
| CD5 Buy & Hold | -14.30 | -15.71 | 42.9% |

**Key finding:** Prompt-based risk constraints made performance *worse*, revealing that LLMs cannot reliably enforce quantitative rules through natural language alone.

---

## Changes from Original Repo (My Contributions)

### Bug Fixes (Windows Compatibility)

| File | Change |
|---|---|
| `agent_tools/tool_crypto_trade.py` | Replace Unix-only `fcntl` with cross-platform no-op lock |
| `agent_tools/tool_trade.py` | Same fix |
| `agent/base_agent_crypto/base_agent_crypto.py` | Monkey-patch LangChain to fix DeepSeek API list-content incompatibility |

### New Files (HW3 Additions)

| File | Purpose |
|---|---|
| `prompts/agent_prompt_crypto_riskaverse.py` | Modified system prompt with 4 risk management rules |
| `agent/base_agent_crypto/base_agent_crypto_riskaverse.py` | Risk-averse agent class (inherits BaseAgentCrypto) |
| `configs/crypto_baseline_reproduce_config.json` | Config to reproduce DeepSeek baseline (Nov 1–14, 2025) |
| `configs/crypto_riskaverse_config.json` | Config for risk-averse modification experiment |
| `hw3_results/` | Output tables and visualization figures used for HW3 |

### Modified Files

| File | Change |
|---|---|
| `main.py` | Register `BaseAgentCryptoRiskAverse` in AGENT_REGISTRY; fix indentation bug |

---

## Setup Instructions

### 1. Clone and Install

```bash
git clone https://github.com/YOUR_USERNAME/AI-Trader.git
cd AI-Trader
pip install langchain==1.0.2 langchain-openai==1.0.1 "langchain-mcp-adapters>=0.1.0" \
    fastmcp==2.12.5 python-dotenv requests numpy pandas matplotlib reportlab
```

### 2. Configure API Keys

Copy `.env.example` to `.env` and fill in your keys:

```bash
cp .env.example .env
# Edit .env:
OPENAI_API_BASE="https://api.deepseek.com"
OPENAI_API_KEY="your_deepseek_api_key"
ALPHAADVANTAGE_API_KEY="your_alphavantage_key"
```

Get API keys:
- DeepSeek: https://platform.deepseek.com (free tier available)
- Alpha Vantage: https://www.alphavantage.co/support/#api-key (free)

### 3. Start MCP Services

Open 4 separate terminals and run:

```bash
# Terminal 1: Math service
python agent_tools/tool_math.py

# Terminal 2: News search service  
python agent_tools/tool_alphavantage_news.py

# Terminal 3: Price service
python agent_tools/tool_get_price_local.py

# Terminal 4: Crypto trade service
python agent_tools/tool_crypto_trade.py
```

### 4. Run Experiments

**Reproduce baseline (DeepSeek-Chat, Nov 1–14, 2025):**
```bash
python main.py configs/crypto_baseline_reproduce_config.json
```

**Run risk-averse modification:**
```bash
python main.py configs/crypto_riskaverse_config.json
```

Both experiments auto-resume if interrupted (detects last completed date from position file).

### 5. Compute Metrics

```bash
# Compute metrics for both experiments
python tools/calculate_metrics.py data/agent_data_crypto/deepseek-chat-reproduce/position/position.jsonl --data-dir data/crypto --is-crypto
python tools/calculate_metrics.py data/agent_data_crypto/deepseek-chat-riskaverse/position/position.jsonl --data-dir data/crypto --is-crypto
```

Output files appear in `hw3_results/` (tables and figures for HW3 analysis).

---

## Reproducing Paper's Table 1 (Using Authors' Data)

The original repository includes exact position data for all 6 paper models in:
```
data/agent_data_crypto/<model_name>/position/position.jsonl
```

To reproduce Table 1 from this data (no API calls needed), rerun
`tools/calculate_metrics.py` on the authors' `position.jsonl` files.

---

## Windows Notes

Three compatibility fixes are required on Windows (already applied in this fork):

1. **`fcntl` module**: Replaced with no-op lock in `tool_crypto_trade.py` and `tool_trade.py`
2. **DeepSeek API format**: LangChain MCP returns list-type content; DeepSeek requires string. Fixed in `base_agent_crypto.py`
3. **Git checkout**: Repository paths with colons are invalid on Windows NTFS. Use binary re-checkout if needed.

---

## Modification Details

**Location:** `prompts/agent_prompt_crypto_riskaverse.py`  
**Change:** Added 4 rules to system prompt:

```
[RISK MANAGEMENT RULES — MANDATORY]
1. POSITION LIMIT: No single crypto may exceed 35% of portfolio
2. HOLD ASSESSMENT: Prefer HOLD if expected gain < 0.5%
3. DIVERSIFICATION: Hold at least 3 different assets
4. CASH RESERVE: Keep at least 10% CASH at all times
```

**Why this modification?** The paper identifies "risk control capability" as a key differentiator. This tests whether explicit prompt-based constraints can operationalize that finding.

**Result:** The modification performed *worse* (CR: -17.12% vs -15.25%), revealing that natural language risk rules are unreliably enforced by LLMs. Production risk management requires code-level enforcement.

---

## File Structure (HW3 Additions Only)

```
AI-Trader/
├── prompts/
│   ├── agent_prompt_crypto.py          (original)
│   └── agent_prompt_crypto_riskaverse.py  ← NEW
├── agent/base_agent_crypto/
│   ├── base_agent_crypto.py            (modified: Windows fix)
│   └── base_agent_crypto_riskaverse.py ← NEW
├── configs/
│   ├── crypto_baseline_reproduce_config.json  ← NEW
│   └── crypto_riskaverse_config.json          ← NEW
└── hw3_results/                        ← NEW
    └── tables_and_figures_for_HW3_analysis
```

---

## Citation

```bibtex
@article{fan2025aitrader,
  title={AI-Trader: Benchmarking Autonomous Agents in Real-Time Financial Markets},
  author={Fan, Tao and Yang, Yuhang and Jiang, Yao and Zhang, Yingyi and Chen, Yunyao and Huang, Chao},
  journal={arXiv preprint arXiv:2512.10971},
  year={2025}
}
```
