# -*- coding: utf-8 -*-
"""
scipilot-figure-skill :: 2025A 烟幕干扰弹建模论文图
====================================================
两张出版级数据图（中文核心期刊，宋体 + Times New Roman 混排）：

  fig_intervals    图1  三面板遮蔽区间图（问题3/4 区间口径；问题5 逐弹时长口径）
  fig_drop_points  图2  投放点与起爆点空间分布散点（x-y 投影，颜色=高度 z）

数据来源：new-model/matlab/result1.csv (Q3) / result2.csv (Q4) / result3.csv (Q5)
输出目录：new-model/figure/
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

SKILL_SCRIPTS = r"C:\Users\nbplus\.claude\skills\scipilot-figure\scripts"
sys.path.insert(0, SKILL_SCRIPTS)

from setup_style import setup_style                      # noqa: E402
from export_figure import export_figure                  # noqa: E402
from visual_qa import render_preview, audit_layout, print_report  # noqa: E402
from layout_tools import add_panel_labels, finalize_figure         # noqa: E402

# ---------------------------------------------------------------- 数据路径
DATA = Path(r"C:\Users\nbplus\Desktop\mathmodel\2025A\new-model\matlab")
OUT = Path(r"C:\Users\nbplus\Desktop\mathmodel\2025A\new-model\figure")
OUT.mkdir(parents=True, exist_ok=True)

# Okabe-Ito 色盲安全配色（蓝 / 橙 / 绿）
BLUE, ORANGE, GREEN = "#0072B2", "#E69F00", "#009E73"
GRAY = "#8c8c8c"

# ---------------------------------------------------------------- 读数据
q3 = pd.read_csv(DATA / "result1.csv", encoding="utf-8-sig")
q4 = pd.read_csv(DATA / "result2.csv", encoding="utf-8-sig")
q5 = pd.read_csv(DATA / "result3.csv", encoding="utf-8-sig")


# ================================================================ 图 1
def draw_intervals():
    setup_style(journal="general", lang="zh", use_sciplots=True,
                serif_for_zh=True, constrained_layout=True)
    # 中文核心：强制宋体（TrueType），避免 fallback 到 Noto Serif ExtraLight 细字重
    plt.rcParams["font.serif"] = ["SimSun", "Times New Roman", "Times",
                                  "DejaVu Serif"]
    plt.rcParams["font.size"] = 9
    plt.rcParams["axes.titlesize"] = 9
    plt.rcParams["xtick.labelsize"] = 8
    plt.rcParams["ytick.labelsize"] = 8
    plt.rcParams["legend.fontsize"] = 7.5

    fig, axes = plt.subplots(1, 3, figsize=(6.7, 3.35))
    BAR_H = 0.55
    handles_q5 = None   # 问题5 图例在图底部统一放置，避免压住数据条

    # ---------- (a) 问题 3：单机 3 弹区间
    ax = axes[0]
    labels, cols = ["弹 1", "弹 2", "弹 3"], [BLUE, ORANGE, GREEN]
    for i in range(3):
        y = 2 - i
        t0, t1 = q3.loc[i, "生效时间"], q3.loc[i, "失效时间"]
        dur = q3.loc[i, "有效干扰时长"]
        if dur > 0:
            ax.barh(y, t1 - t0, left=t0, height=BAR_H, color=cols[i],
                    edgecolor="black", linewidth=0.4)
            ax.text(t1 + 0.25, y, f"{dur:.2f} s", va="center",
                    fontsize=7, fontstyle="italic")
        else:
            ax.plot(t0 + 0.1, y, "x", color=GRAY, markersize=6, mew=1.2)
    ax.set_yticks([2, 1, 0], labels)
    ax.set_ylim(-0.7, 2.7)
    ax.set_xlim(0, 8.4)
    ax.set_xlabel("时间 $t$/s")
    ax.set_title("问题 3：单机 3 弹")
    ax.legend(handles=[Line2D([], [], marker="x", linestyle="", color=GRAY,
                              label="未生效（时长 0）")],
              loc="upper left", frameon=False)

    # ---------- (b) 问题 4：3 机各 1 弹区间
    ax = axes[1]
    labels = ["FY1", "FY2", "FY3"]
    cols = [BLUE, ORANGE, GREEN]
    for i in range(3):
        y = 2 - i
        t0, t1 = q4.loc[i, "生效时间"], q4.loc[i, "失效时间"]
        dur = q4.loc[i, "有效干扰时长"]
        if dur > 0:
            ax.barh(y, t1 - t0, left=t0, height=BAR_H, color=cols[i],
                    edgecolor="black", linewidth=0.4)
            ax.text(t1 + 0.8, y, f"{dur:.2f} s", va="center",
                    fontsize=7, fontstyle="italic")
        else:
            ax.plot(t0 + 0.2, y, "x", color=GRAY, markersize=6, mew=1.2)
    ax.set_yticks([2, 1, 0], labels)
    ax.set_ylim(-0.7, 2.7)
    ax.set_xlim(0, 34.5)
    ax.set_xlabel("时间 $t$/s")
    ax.set_title("问题 4：3 机各 1 弹")

    # ---------- (c) 问题 5：5 机 × 3 弹逐弹时长（横条口径）
    ax = axes[2]
    missile_col = {"M1": BLUE, "M2": ORANGE, "M3": GREEN}
    missile_hatch = {"M1": "", "M2": "//", "M3": "\\\\"}
    yticks, ylabels, k = [], [], 0
    for uav in range(1, 6):
        for b in range(1, 4):
            y = 14 - k
            row = q5[(q5["无人机编号"] == f"FY{uav}") &
                     (q5["干扰弹编号"] == b)].iloc[0]
            dur = row["有效干扰时长"]
            m = row["干扰导弹编号"]
            yticks.append(y)
            ylabels.append(f"FY{uav}-弹{b}")
            if dur > 0:
                ax.barh(y, dur, left=0, height=BAR_H,
                        color=missile_col[m], hatch=missile_hatch[m],
                        edgecolor="black", linewidth=0.4)
                ax.text(dur + 0.12, y, f"{dur:.2f} s", va="center",
                        fontsize=6.5, fontstyle="italic")
            else:
                ax.plot(0.08, y, "x", color=GRAY, markersize=5, mew=1.0)
            k += 1
    for sep_y in (2.5, 5.5, 8.5, 11.5):          # 无人机组间浅分隔线
        ax.axhline(sep_y, color="#bbbbbb", lw=0.5, ls=":", zorder=0)
    ax.set_yticks(yticks, ylabels, fontsize=6.5)
    ax.set_ylim(-0.7, 14.7)
    ax.set_xlim(0, 5.4)
    ax.set_xlabel("有效干扰时长/s")
    ax.set_title("问题 5：5 机×3 弹（逐弹时长）")
    # 图例不在面板内放置（右上角会压住 FY1-弹1 的条与时长标注）——
    # 改为整图底部居中横排一行
    handles_q5 = [
        Patch(facecolor=BLUE, hatch="", edgecolor="black", label="M1"),
        Patch(facecolor=ORANGE, hatch="//", edgecolor="black", label="M2"),
        Patch(facecolor=GREEN, hatch="\\\\", edgecolor="black", label="M3"),
        Line2D([], [], marker="x", linestyle="", color=GRAY,
               label="未生效（时长 0）")]

    finalize_figure(fig)
    fig.legend(handles=handles_q5, loc="outside lower center",
               ncol=4, frameon=False, handlelength=1.4, columnspacing=1.2)
    add_panel_labels(fig, style="paren", x_offset_pt=-24, y_offset_pt=2)
    return fig


# ================================================================ 图 2
def _base_style():
    """中文核心样式 + 强制宋体（TrueType）。"""
    setup_style(journal="general", lang="zh", use_sciplots=True,
                serif_for_zh=True, constrained_layout=False)
    # 中文核心：强制宋体（TrueType），避免 fallback 到 Noto Serif ExtraLight 细字重
    plt.rcParams["font.serif"] = ["SimSun", "Times New Roman", "Times",
                                  "DejaVu Serif"]
    plt.rcParams["font.size"] = 9
    plt.rcParams["axes.titlesize"] = 10
    plt.rcParams["xtick.labelsize"] = 7.5
    plt.rcParams["ytick.labelsize"] = 7.5
    plt.rcParams["legend.fontsize"] = 8


def draw_drop3d(df, title, colors, color_labels, size=(6.7, 4.2)):
    """单张 3D 散点图：投放点（实心）/ 起爆点（空心）空间分布。

    colors: 与 df 行对应的逐行颜色（弹号 / 无人机 / 导弹）
    color_labels: 图例中各类别的名称
    """
    _base_style()
    fig = plt.figure(figsize=size)
    ax = fig.add_subplot(111, projection="3d")
    fig.subplots_adjust(left=0.02, right=0.98, top=0.92, bottom=0.08)

    def pad_lim(vals, pct=0.10):
        lo, hi = float(vals.min()), float(vals.max())
        span = hi - lo if hi > lo else 1.0
        return lo - span * pct, hi + span * pct

    d = df[["投放点x", "投放点y", "投放点z"]].dropna()
    b = df[["起爆点x", "起爆点y", "起爆点z"]].dropna()
    # 起爆点（空心、同色描边）
    ax.scatter(b.iloc[:, 0], b.iloc[:, 1], b.iloc[:, 2],
               s=26, depthshade=False, facecolors="none",
               edgecolors=colors, linewidths=1.0)
    # 投放点（实心）
    ax.scatter(d.iloc[:, 0], d.iloc[:, 1], d.iloc[:, 2],
               s=26, depthshade=False, c=colors,
               edgecolors="black", linewidths=0.2)
    xs = np.concatenate([d.iloc[:, 0], b.iloc[:, 0]])
    ys = np.concatenate([d.iloc[:, 1], b.iloc[:, 1]])
    ax.set_xlim(*pad_lim(xs))
    ax.set_ylim(*pad_lim(ys))
    ax.set_zlim(0, 2000)
    ax.view_init(elev=22, azim=-55)
    ax.xaxis.set_major_locator(plt.MaxNLocator(4))
    ax.yaxis.set_major_locator(plt.MaxNLocator(4))
    ax.zaxis.set_major_locator(plt.MaxNLocator(4))
    ax.tick_params(labelsize=7.5, pad=-1)
    ax.set_xlabel("x/m", fontsize=9, labelpad=-2)
    ax.set_ylabel("y/m", fontsize=9, labelpad=-2)
    ax.set_zlabel("z/m", fontsize=9, labelpad=-6)
    ax.set_title(title, fontsize=10, pad=8)

    # 颜色图例（左上）+ 实心/空心图例（右下）
    leg1 = ax.legend(handles=[Patch(facecolor=c, edgecolor="black",
                                    label=lab)
                              for c, lab in zip(colors, color_labels)],
                     loc="upper left", frameon=False)
    ax.add_artist(leg1)
    ax.legend(handles=[
        Line2D([], [], marker="o", linestyle="", color="#555555",
               markeredgecolor="black", markeredgewidth=0.4,
               markersize=6, label="投放点（实心）"),
        Line2D([], [], marker="o", linestyle="", mfc="none",
               markeredgecolor="#555555", markersize=6,
               label="起爆点（空心）")],
        loc="lower right", frameon=False)
    return fig


# ==============================================35================= 主流程
if __name__ == "__main__":
    mcol = {"M1": BLUE, "M2": ORANGE, "M3": GREEN}
    figs = [
        ("intervals", draw_intervals(), (6.7, 3.35)),
        ("drop_q3", draw_drop3d(q3, "问题 3：单机 3 弹",
                                [BLUE, ORANGE, GREEN],
                                ["弹 1", "弹 2", "弹 3"]), (6.7, 4.2)),
        ("drop_q4", draw_drop3d(q4, "问题 4：3 机各 1 弹",
                                [BLUE, ORANGE, GREEN],
                                ["FY1", "FY2", "FY3"]), (6.7, 4.2)),
        ("drop_q5", draw_drop3d(q5, "问题 5：5 机×3 弹",
                                [mcol[m] for m in q5["干扰导弹编号"]],
                                ["M1", "M2", "M3"]), (6.7, 4.2)),
    ]
    ok = True
    for name, fig, size in figs:
        fig.set_size_inches(*size)
        print(f"\n===== {name} =====")
        render_preview(fig, str(OUT / f"_preview_{name}.png"), dpi=150)
        issues = audit_layout(fig)
        print_report(issues)
        if any(sev == "FAIL" for sev, _ in issues):
            ok = False
        if ok:
            export_figure(
                fig, basename=str(OUT / f"fig_{name}"),
                formats=["pdf", "svg", "png"],
                dpi=600, size_inches=size, grayscale_preview=True)
    print("\nDONE" if ok else "\nHAS FAIL ISSUES — 请先修复缺字问题")
