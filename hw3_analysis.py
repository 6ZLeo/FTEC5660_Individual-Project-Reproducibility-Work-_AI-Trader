#!/usr/bin/env python3
"""
HW3 Reproducibility Analysis Script
FTEC5660 — AI-Trader Cryptocurrency Market Reproducibility Study

Usage:
    python hw3_analysis.py

Generates:
    - hw3_results/table1_reproduction.csv  : Reproduced Table 1 metrics
    - hw3_results/table2_modification.csv  : Modification experiment metrics
    - hw3_results/fig1_portfolio_values.png: Portfolio value over time
    - hw3_results/fig2_metrics_comparison.png: Bar chart comparing key metrics
    - hw3_results/summary_report.txt       : Human-readable summary
"""

import json
import os
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd

# Ensure project root is on path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from tools.calculate_metrics import (calculate_metrics,
                                      calculate_portfolio_values,
                                      load_all_price_files,
                                      load_position_data)

OUTPUT_DIR = project_root / "hw3_results"
OUTPUT_DIR.mkdir(exist_ok=True)

CRYPTO_DATA_DIR = project_root / "data" / "crypto"
AGENT_DATA_DIR  = project_root / "data" / "agent_data_crypto"

# Models from the original paper
PAPER_MODELS = [
    "claude-3.7-sonnet",
    "deepseek-chat-v3.1",
    "gemini-2.5-flash",
    "gpt-5",
    "MiniMax-M2",
    "qwen3-max",
]

# Display names for the report
MODEL_DISPLAY = {
    "claude-3.7-sonnet":   "Claude-3.7-Sonnet",
    "deepseek-chat-v3.1":  "DeepSeek-Chat-V3.1",
    "gemini-2.5-flash":    "Gemini-2.5-Flash",
    "gpt-5":               "GPT-5",
    "MiniMax-M2":          "MiniMax-M2",
    "qwen3-max":           "Qwen3-Max",
    "deepseek-chat-reproduce":  "DeepSeek-Chat (Reproduced)",
    "deepseek-chat-riskaverse": "DeepSeek-Chat (Risk-Averse Mod)",
}

# CD5 Baseline data (from paper's repo)
CD5_BASELINE_FILE = project_root / "data" / "crypto" / "CD5_baseline" / "position.jsonl"


def load_metrics(signature: str) -> dict | None:
    pos_file = AGENT_DATA_DIR / signature / "position" / "position.jsonl"
    if not pos_file.exists():
        return None
    positions = load_position_data(str(pos_file))
    price_data = load_all_price_files(str(CRYPTO_DATA_DIR), is_crypto=True)
    portfolio_df = calculate_portfolio_values(positions, price_data, is_crypto=True, verbose=False)
    metrics = calculate_metrics(portfolio_df, periods_per_year=365)
    metrics["signature"] = signature
    metrics["display_name"] = MODEL_DISPLAY.get(signature, signature)
    metrics["portfolio_df"] = portfolio_df
    return metrics


def load_cd5_baseline() -> dict:
    """Load CD5 buy-and-hold baseline."""
    positions = []
    with open(CD5_BASELINE_FILE) as f:
        for line in f:
            entry = json.loads(line)
            # CD5 baseline only has CASH, which represents portfolio value
            positions.append({
                "date": entry["date"],
                "positions": {"CASH": entry["positions"]["CASH"]}
            })
    df = pd.DataFrame([
        {"date": pd.Timestamp(p["date"]), "total_value": p["positions"]["CASH"]}
        for p in positions
    ])
    values = df["total_value"].values
    returns = np.diff(values) / values[:-1]
    cr = (values[-1] - values[0]) / values[0]
    mdd_arr = (np.cumprod(1 + returns) - np.maximum.accumulate(np.cumprod(1 + returns))) / np.maximum.accumulate(np.cumprod(1 + returns))
    negative_returns = returns[returns < 0]
    excess = np.mean(returns)
    downside_std = np.std(negative_returns) if len(negative_returns) > 0 else 1e-9
    sortino = excess / downside_std * np.sqrt(365)
    vol = np.std(returns) * np.sqrt(365)
    win_rate = np.mean(returns > 0)
    return {
        "display_name": "CD5 Index (Buy & Hold)",
        "CR": cr,
        "SR": sortino,
        "Vol": vol,
        "MDD": np.min(mdd_arr) if len(mdd_arr) > 0 else 0,
        "Win Rate": win_rate,
        "Final Value": values[-1],
        "Initial Value": values[0],
        "portfolio_df": df,
    }


def build_table(results: list[dict]) -> pd.DataFrame:
    rows = []
    for r in results:
        rows.append({
            "Model": r["display_name"],
            "Final Value (USDT)": f"{r['Final Value']:,.2f}",
            "CR (%)": f"{r['CR']*100:.2f}",
            "Sortino Ratio": f"{r['SR']:.2f}",
            "Volatility (%)": f"{r['Vol']*100:.2f}",
            "MDD (%)": f"{r['MDD']*100:.2f}",
            "Win Rate (%)": f"{r.get('Win Rate', 0)*100:.1f}",
        })
    return pd.DataFrame(rows)


def plot_portfolio_values(all_results: list[dict], title: str, filename: str):
    fig, ax = plt.subplots(figsize=(12, 6))
    colors = plt.cm.tab10(np.linspace(0, 1, len(all_results)))

    for i, r in enumerate(all_results):
        df = r["portfolio_df"].copy()
        if "total_value" not in df.columns:
            continue
        df["date"] = pd.to_datetime(df["date"])
        ax.plot(df["date"], df["total_value"], label=r["display_name"],
                color=colors[i], linewidth=2 if "CD5" in r["display_name"] else 1.5,
                linestyle="--" if "CD5" in r["display_name"] else "-")

    ax.set_xlabel("Date", fontsize=12)
    ax.set_ylabel("Portfolio Value (USDT)", fontsize=12)
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.legend(loc="lower left", fontsize=9)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
    plt.xticks(rotation=30)
    ax.grid(True, alpha=0.3)
    ax.axhline(y=50000, color="gray", linestyle=":", alpha=0.5, label="Initial Value")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / filename, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"✅ Saved: {OUTPUT_DIR / filename}")


def plot_metrics_bar(results: list[dict], title: str, filename: str):
    names = [r["display_name"] for r in results]
    crs = [r["CR"] * 100 for r in results]
    mdds = [r["MDD"] * 100 for r in results]
    sortinos = [r["SR"] for r in results]

    x = np.arange(len(names))
    width = 0.25
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    bars1 = ax1.bar(x - width/2, crs, width, label="CR (%)", color="steelblue", alpha=0.8)
    bars2 = ax1.bar(x + width/2, mdds, width, label="MDD (%)", color="tomato", alpha=0.8)
    ax1.set_ylabel("Percentage (%)")
    ax1.set_title("Cumulative Return vs Max Drawdown", fontweight="bold")
    ax1.set_xticks(x)
    ax1.set_xticklabels(names, rotation=20, ha="right", fontsize=8)
    ax1.legend()
    ax1.axhline(y=0, color="black", linestyle="-", linewidth=0.5)
    ax1.grid(True, alpha=0.3, axis="y")

    colors_bar = ["#e74c3c" if s < 0 else "#2ecc71" for s in sortinos]
    ax2.bar(x, sortinos, color=colors_bar, alpha=0.8)
    ax2.set_ylabel("Sortino Ratio")
    ax2.set_title("Sortino Ratio (Risk-Adjusted Return)", fontweight="bold")
    ax2.set_xticks(x)
    ax2.set_xticklabels(names, rotation=20, ha="right", fontsize=8)
    ax2.axhline(y=0, color="black", linestyle="-", linewidth=0.5)
    ax2.grid(True, alpha=0.3, axis="y")

    fig.suptitle(title, fontsize=13, fontweight="bold", y=1.02)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / filename, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"✅ Saved: {OUTPUT_DIR / filename}")


def main():
    print("=" * 70)
    print("HW3 AI-Trader Reproducibility Analysis")
    print("FTEC5660 — Cryptocurrency Market (Nov 1–14, 2025)")
    print("=" * 70)

    # -------------------------------------------------------
    # Part 1: Reproduction — all 6 paper models
    # -------------------------------------------------------
    print("\n[1/4] Computing reproduction metrics for all 6 paper models...")
    paper_results = []
    for sig in PAPER_MODELS:
        m = load_metrics(sig)
        if m:
            paper_results.append(m)
            print(f"  ✅ {sig}: CR={m['CR']*100:.2f}%, MDD={m['MDD']*100:.2f}%")
        else:
            print(f"  ⚠️  {sig}: position file not found, skipping")

    cd5 = load_cd5_baseline()
    print(f"  ✅ CD5 Baseline: CR={cd5['CR']*100:.2f}%, MDD={cd5['MDD']*100:.2f}%")

    all_repro = paper_results + [cd5]

    table1 = build_table(all_repro)
    table1.to_csv(OUTPUT_DIR / "table1_reproduction.csv", index=False)
    print(f"\n  📊 Table 1 saved to hw3_results/table1_reproduction.csv")
    print(table1.to_string(index=False))

    plot_portfolio_values(
        all_repro,
        "AI-Trader: Portfolio Value — Cryptocurrency Market (Nov 1–14, 2025)\n[Reproduction of Paper Results]",
        "fig1_portfolio_values_reproduction.png"
    )
    plot_metrics_bar(
        all_repro,
        "Performance Metrics Comparison — All 6 LLMs + CD5 Baseline",
        "fig2_metrics_bar_reproduction.png"
    )

    # -------------------------------------------------------
    # Part 2: Modification experiment (if data exists)
    # -------------------------------------------------------
    print("\n[2/4] Checking for modification experiment data...")
    mod_sig = "deepseek-chat-riskaverse"
    rep_sig = "deepseek-chat-reproduce"

    mod_metrics = load_metrics(mod_sig)
    rep_metrics = load_metrics(rep_sig)

    # Also grab the paper's deepseek as comparison
    paper_deepseek = load_metrics("deepseek-chat-v3.1")

    if mod_metrics or rep_metrics:
        mod_results = []
        if paper_deepseek:
            mod_results.append(paper_deepseek)
        if rep_metrics:
            mod_results.append(rep_metrics)
        if mod_metrics:
            mod_results.append(mod_metrics)
        mod_results.append(cd5)

        table2 = build_table(mod_results)
        table2.to_csv(OUTPUT_DIR / "table2_modification.csv", index=False)
        print(f"  📊 Table 2 saved to hw3_results/table2_modification.csv")
        print(table2.to_string(index=False))

        plot_portfolio_values(
            mod_results,
            "AI-Trader: Modification Experiment\n[Baseline DeepSeek vs Risk-Averse Prompt vs CD5]",
            "fig3_portfolio_values_modification.png"
        )
        plot_metrics_bar(
            mod_results,
            "Baseline vs Risk-Averse Modification (DeepSeek-Chat)",
            "fig4_metrics_bar_modification.png"
        )
    else:
        print("  ℹ️  Modification experiment data not yet available.")
        print("     Run the modification experiment first:")
        print("     python main.py configs/crypto_baseline_reproduce_config.json")
        print("     python main.py configs/crypto_riskaverse_config.json")

    # -------------------------------------------------------
    # Part 3: Summary report
    # -------------------------------------------------------
    print("\n[3/4] Writing summary report...")
    with open(OUTPUT_DIR / "summary_report.txt", "w", encoding="utf-8") as f:
        f.write("=" * 70 + "\n")
        f.write("HW3 REPRODUCIBILITY STUDY — AI-TRADER\n")
        f.write("FTEC5660 Agentic AI for Business and FinTech\n")
        f.write("Cryptocurrency Market: Nov 1–14, 2025\n")
        f.write("=" * 70 + "\n\n")

        f.write("REPRODUCTION RESULTS (Table 1)\n")
        f.write("-" * 70 + "\n")
        f.write(table1.to_string(index=False))
        f.write("\n\n")

        f.write("KEY OBSERVATIONS\n")
        f.write("-" * 70 + "\n")
        if paper_results:
            best = max(paper_results, key=lambda x: x["CR"])
            worst = min(paper_results, key=lambda x: x["CR"])
            f.write(f"Best performer:  {best['display_name']} (CR={best['CR']*100:.2f}%)\n")
            f.write(f"Worst performer: {worst['display_name']} (CR={worst['CR']*100:.2f}%)\n")
            f.write(f"CD5 Baseline:    CR={cd5['CR']*100:.2f}%\n")
            beats_baseline = [r for r in paper_results if r["CR"] > cd5["CR"]]
            f.write(f"Models beating buy-and-hold: {len(beats_baseline)}/{len(paper_results)}\n")
        f.write("\n")

        if mod_metrics:
            f.write("MODIFICATION RESULTS\n")
            f.write("-" * 70 + "\n")
            f.write(f"Baseline (deepseek-chat-v3.1): CR={paper_deepseek['CR']*100:.2f}%, "
                    f"MDD={paper_deepseek['MDD']*100:.2f}%, SR={paper_deepseek['SR']:.2f}\n")
            f.write(f"Risk-Averse Mod:               CR={mod_metrics['CR']*100:.2f}%, "
                    f"MDD={mod_metrics['MDD']*100:.2f}%, SR={mod_metrics['SR']:.2f}\n")
            cr_delta = (mod_metrics["CR"] - paper_deepseek["CR"]) * 100
            mdd_delta = (mod_metrics["MDD"] - paper_deepseek["MDD"]) * 100
            sr_delta  = mod_metrics["SR"] - paper_deepseek["SR"]
            f.write(f"\nDelta (Mod - Baseline):\n")
            f.write(f"  ΔCR  = {cr_delta:+.2f}%\n")
            f.write(f"  ΔMDD = {mdd_delta:+.2f}%\n")
            f.write(f"  ΔSR  = {sr_delta:+.2f}\n")

    print(f"  📝 Summary saved to hw3_results/summary_report.txt")
    print("\n[4/4] Analysis complete!")
    print(f"\nAll outputs in: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
