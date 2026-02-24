import json

print("=" * 65)
print("FINAL HW3 EXPERIMENT SUMMARY")
print("=" * 65)

paper_models = {
    "Claude-3.7-Sonnet": -15.30,
    "DeepSeek-V3.1 [BEST]": -12.18,
    "Gemini-2.5-Flash": -18.63,
    "GPT-5": -16.41,
    "MiniMax-M2": -14.78,
    "Qwen3-Max": -16.85,
    "CD5 Buy&Hold": -14.30,
}

print("\n[Part 1: Reproduction from Paper Data]")
for m, cr in paper_models.items():
    print(f"  {m:<28} CR={cr:+.2f}%")

b = json.load(open("data/agent_data_crypto/deepseek-chat-reproduce/position/performance_metrics.json"))
r = json.load(open("data/agent_data_crypto/deepseek-chat-riskaverse/position/performance_metrics.json"))

cr_b = b["CR"] * 100
mdd_b = b["MDD"] * 100
wr_b = b["Win Rate"] * 100
fv_b = b["Final Value"]

cr_r = r["CR"] * 100
mdd_r = r["MDD"] * 100
wr_r = r["Win Rate"] * 100
fv_r = r["Final Value"]

print("\n[Part 2: Own DeepSeek-Chat Run (Reproduced)]")
print(f"  CR={cr_b:.2f}%  MDD={mdd_b:.2f}%  WinRate={wr_b:.1f}%  FinalValue=${fv_b:,.2f}")

print("\n[Part 3: Risk-Averse Modification]")
print(f"  CR={cr_r:.2f}%  MDD={mdd_r:.2f}%  WinRate={wr_r:.1f}%  FinalValue=${fv_r:,.2f}")

delta_cr = cr_r - cr_b
print(f"\n  Delta CR (Mod - Baseline): {delta_cr:+.2f} pp")
print("  Interpretation: Risk-averse modification performed WORSE")

print("\n[Output Files]")
files = [
    "hw3_results/HW3_Report.pdf     -- 9-page PDF academic report",
    "hw3_results/table1_reproduction.csv",
    "hw3_results/table2_modification.csv",
    "hw3_results/fig1-4 (PNG figures)",
    "hw3_report.md                   -- full Markdown narrative",
]
for f in files:
    print(f"  {f}")
