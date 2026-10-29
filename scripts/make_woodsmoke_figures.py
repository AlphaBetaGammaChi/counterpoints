#!/usr/bin/env python3
"""
Generate all figures for the woodsmoke counterpoints topic.

Outputs to ../topics/woodsmoke/figures/ relative to this script:
  fig_heating_ef.png        PM2.5 per MWh by heating method (EMEP 2019 / UK CMO 2022)
  fig_uk_pm25_sources.png   UK primary PM2.5 source shares, 2022 (Defra/NAEI via EAC)
  fig_wood_share_studies.png  Wood-burning share of PM across source-apportionment studies
  fig_launceston.png        Mortality change after wood-heater intervention (Johnston 2013)
  fig_diurnal.png           Stylised winter diurnal PM2.5 profile (illustrative)
  anim_refuel_spike.gif     Indoor PM2.5 spikes on stove-door opening (stylised, after
                            Chakraborty et al. 2020)
  anim_dispersion.gif       Neighbourhood smoke dispersion between houses (stylised)
  interactive_sources.html  Plotly interactive version of the study-shares chart

Run:  /opt/anaconda3/bin/python3 scripts/make_woodsmoke_figures.py
"""

import io
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
FIGDIR = os.path.join(HERE, "..", "topics", "woodsmoke", "figures")
os.makedirs(FIGDIR, exist_ok=True)

EMBER = "#d95f02"
SMOKE = "#6e6e6e"
CLEAN = "#1b9e77"
STEEL = "#7570b3"
TEXT = "#1a1a1a"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 11,
    "axes.edgecolor": TEXT,
    "axes.labelcolor": TEXT,
    "text.color": TEXT,
    "xtick.color": TEXT,
    "ytick.color": TEXT,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.facecolor": "white",
})


def save(fig, name):
    path = os.path.join(FIGDIR, name)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("wrote", path)


# ---------------------------------------------------------------- fig 1
def fig_heating_ef():
    """EMEP 2019 emission factors as published in UK CMO Annual Report 2022, Fig. 10."""
    labels = [
        "Solid-fuel\nopen fire", "Older\nwood stove", "Ecodesign /\nDefra-exempt\nstove",
        "Pellet-fired\nboiler", "Oil-fired\nboiler", "Gas-fired\nboiler", "Electric\nheating",
    ]
    vals = [2950, 2660, 335, 216, 5.4, 0.72, 0.0]
    multiples = [v / 0.72 for v in vals[:-1]]
    colors = [EMBER, EMBER, EMBER, "#e6a173", SMOKE, STEEL, CLEAN]

    fig, ax = plt.subplots(figsize=(9, 5))
    x = np.arange(len(labels))
    plot_vals = [max(v, 0.3) for v in vals]  # 0 can't be drawn on log scale
    bars = ax.bar(x, plot_vals, color=colors, edgecolor="black", linewidth=0.5)
    ax.set_yscale("log")
    ax.set_ylabel("PM2.5 emitted (g per MWh of heat, log scale)")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_title("PM2.5 emissions per unit of heat by domestic heating method",
                 fontsize=13, fontweight="bold")

    for xi, v, m in zip(x[:-1], vals[:-1], multiples):
        ax.annotate(f"{v:g} g\n({m:,.0f}\u00d7 gas)", (xi, plot_vals[xi]),
                    textcoords="offset points", xytext=(0, 6),
                    ha="center", fontsize=8.5)
    ax.annotate("0 g", (x[-1], 0.5), textcoords="offset points",
                xytext=(0, 6), ha="center", fontsize=8.5, fontweight="bold",
                color=CLEAN)
    ax.set_ylim(0.3, 20000)
    ax.spines[["top", "right"]].set_visible(False)
    ax.text(0.98, 0.97,
            "Source: EMEP/EEA 2019 Guidebook factors, via UK Chief Medical\n"
            "Officer's Annual Report 2022: Air Pollution, Figure 10 (gov.uk)",
            transform=ax.transAxes, ha="right", va="top",
            fontsize=7.5, color=SMOKE)
    save(fig, "fig_heating_ef.png")


# ---------------------------------------------------------------- fig 2
def fig_uk_pm25_sources():
    """UK primary PM2.5 source shares, 2022 (Defra/NAEI via Environmental Audit Cttee)."""
    labels = ["Domestic burning\n(~\u00be of it wood)", "Road transport",
              "Industrial processes\n& product use", "All other sources"]
    vals = [29, 18, 16.5, 36.5]
    colors = [EMBER, SMOKE, STEEL, "#bdbdbd"]

    fig, ax = plt.subplots(figsize=(8, 4))
    y = np.arange(len(labels))[::-1]
    ax.barh(y, vals, color=colors, edgecolor="black", linewidth=0.5, height=0.62)
    for yi, v in zip(y, vals):
        ax.annotate(f"{v:g}%", (v, yi), textcoords="offset points",
                    xytext=(6, -4), fontsize=11, fontweight="bold")
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=10)
    ax.set_xlim(0, 42)
    ax.set_xlabel("Share of UK primary PM2.5 emissions, 2022 (%)")
    ax.set_title("Domestic burning is the largest single source of UK PM2.5\n"
                 "— and the only major source still rising over 20 years",
                 fontsize=12, fontweight="bold")
    ax.spines[["top", "right"]].set_visible(False)
    ax.text(0.98, 0.62,
            "Source: Defra/NAEI data, written evidence to the\n"
            "Environmental Audit Committee (AIR0018, 2022 shares).\n"
            "~3/4 of domestic-combustion PM2.5 is wood.",
            transform=ax.transAxes, ha="right", va="top",
            fontsize=7.5, color=SMOKE)
    save(fig, "fig_uk_pm25_sources.png")


# ------------------------------------------------------- fig 3 + plotly
STUDIES = [
    # (label, share %, metric note, citation)
    ("Lycksele, N. Sweden (winter PM1)", 81, "up to 81% of winter PM1", "Krecl et al. 2008, ACP"),
    ("European Union (anthropogenic PM2.5)", 51, "~51% of anthropogenic PM2.5", "Glojek et al. 2022, ACP"),
    ("Swiss sites (black carbon)", 33, "up to ~33% of BC from <4% of energy", "Herich et al. 2011, AMT"),
    ("Southern Sweden (carbonaceous aerosol)", 32, "~32%, more than fossil fuels", "Genberg et al. 2011, ACP"),
    ("UK (primary PM2.5, domestic burning)", 29, "29%; ~\u00be is wood", "Defra/NAEI 2022 via EAC"),
    ("Canada (national PM2.5)", 21, "vs ~12% all transport", "Health Canada 2023"),
]


def fig_wood_share_studies():
    labels = [s[0] for s in STUDIES]
    vals = [s[1] for s in STUDIES]
    fig, ax = plt.subplots(figsize=(8, 4))
    y = np.arange(len(labels))[::-1]
    ax.barh(y, vals, color=EMBER, edgecolor="black", linewidth=0.5, height=0.6)
    for yi, v, s in zip(y, vals, STUDIES):
        ax.annotate(f"{v}%  ({s[3]})", (v, yi), textcoords="offset points",
                    xytext=(6, -4), fontsize=8.5)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=9.5)
    ax.set_xlim(0, 118)
    ax.set_xlabel("Measured share attributable to wood burning (%)")
    ax.set_title("Wood burning's share of particle pollution — measured across studies",
                 fontsize=12, fontweight="bold")
    ax.spines[["top", "right"]].set_visible(False)
    ax.text(0.98, 0.02,
            "Each bar is the published figure from the cited\n"
            "source-apportionment study; metrics differ (PM1,\n"
            "PM2.5, black carbon, carbonaceous aerosol) —\n"
            "see references.md.",
            transform=ax.transAxes, ha="right", va="bottom",
            fontsize=7.5, color=SMOKE)
    save(fig, "fig_wood_share_studies.png")


def interactive_sources():
    import plotly.graph_objects as go
    labels = [s[0] for s in STUDIES][::-1]
    vals = [s[1] for s in STUDIES][::-1]
    notes = [f"{s[2]} — {s[3]}" for s in STUDIES][::-1]
    fig = go.Figure(go.Bar(
        x=vals, y=labels, orientation="h",
        marker_color="#d95f02",
        text=[f"{v}%" for v in vals], textposition="outside",
        hovertext=notes, hoverinfo="text",
    ))
    fig.update_layout(
        title="Wood burning's share of particle pollution — hover for source",
        xaxis_title="Share attributable to wood burning (%)",
        xaxis=dict(range=[0, 95]),
        height=420, margin=dict(l=20, r=20, t=60, b=40),
    )
    path = os.path.join(FIGDIR, "interactive_sources.html")
    fig.write_html(path, include_plotlyjs="cdn")
    print("wrote", path)


# ---------------------------------------------------------------- fig 4
def fig_launceston():
    """Mortality change after Launceston wood-heater programme (Johnston et al. 2013, BMJ)."""
    cats = ["Respiratory\nmortality", "Cardiovascular\nmortality"]
    vals = [-28, -20]
    fig, ax = plt.subplots(figsize=(6, 4))
    x = np.arange(len(cats))
    ax.bar(x, vals, color=CLEAN, edgecolor="black", linewidth=0.5, width=0.5)
    for xi, v in zip(x, vals):
        ax.annotate(f"{v}%", (xi, v), textcoords="offset points",
                    xytext=(0, -16), ha="center", fontsize=13,
                    fontweight="bold", color="white")
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(cats, fontsize=11)
    ax.set_ylabel("Change in winter mortality (%)")
    ax.set_ylim(-35, 5)
    ax.set_title("Launceston, Tasmania: deaths fell after the city\n"
                 "cut wood-heater use (changeout + education campaign)",
                 fontsize=11.5, fontweight="bold")
    ax.spines[["top", "right"]].set_visible(False)
    ax.text(0.5, 0.9,
            "Source: Johnston et al. 2013, BMJ — doi:10.1136/bmj.e8446",
            transform=ax.transAxes, ha="center", va="top",
            fontsize=7.5, color=SMOKE)
    save(fig, "fig_launceston.png")


# ---------------------------------------------------------------- fig 5
def fig_diurnal():
    """Stylised winter diurnal PM2.5 profile — the wood-smoke evening peak."""
    hours = np.arange(0, 24.01, 0.1)
    base = 12 + 3 * np.sin((hours - 8) / 24 * 2 * np.pi)
    evening = 55 * np.exp(-((hours - 19.5) / 2.2) ** 2)
    morning = 12 * np.exp(-((hours - 7.5) / 1.1) ** 2)
    rng = np.random.default_rng(7)
    pm = base + evening + morning + rng.normal(0, 1.2, len(hours))
    pm = np.clip(pm, 2, None)

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(hours, pm, color=EMBER, lw=2)
    ax.fill_between(hours, 0, pm, color=EMBER, alpha=0.15)
    ax.axvspan(17, 23, color=EMBER, alpha=0.08)
    ax.annotate("stoves lit — smoke pools in\nthe street under winter inversions",
                (19.5, pm.max()), textcoords="offset points",
                xytext=(-135, -6), fontsize=9.5)
    ax.annotate("morning\nre-firing", (7.5, 26), ha="center", fontsize=8.5,
                color=SMOKE)
    ax.set_xlim(0, 24)
    ax.set_xticks(range(0, 25, 3))
    ax.set_xlabel("Hour of day")
    ax.set_ylabel("Local PM2.5 (µg/m³, illustrative)")
    ax.set_title("Wood smoke concentrates when people are home:\n"
                 "the winter evening peak", fontsize=12, fontweight="bold")
    ax.spines[["top", "right"]].set_visible(False)
    ax.text(0.02, 0.96,
            "Stylised illustration of the diurnal pattern reported in\n"
            "wood-burning communities (e.g. Fuller et al. 2014;\n"
            "Krecl et al. 2008).",
            transform=ax.transAxes, ha="left", va="top",
            fontsize=7.5, color=SMOKE)
    save(fig, "fig_diurnal.png")


# ------------------------------------------------------------ GIF utils
def gif_frames(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110, bbox_inches="tight")
    buf.seek(0)
    return Image.open(buf).copy()


def write_gif(frames, name, duration=120, hold_last=12):
    frames = frames + [frames[-1]] * hold_last
    path = os.path.join(FIGDIR, name)
    frames[0].save(path, save_all=True, append_images=frames[1:],
                   duration=duration, loop=0, optimize=True)
    print("wrote", path)


# ------------------------------------------------------------ gif 1
def anim_refuel_spike():
    """
    Indoor PM2.5 spikes each time the stove door is opened to refuel.
    Stylised after Chakraborty et al. 2020 (real-world UK homes, incl.
    exempt appliances, saw PM2.5 flooding living rooms at refuelling).
    """
    rng = np.random.default_rng(11)
    t = np.linspace(0, 120, 900)  # two hours, minutes
    pm = 18 + rng.normal(0, 2.5, len(t))
    door_times = [25, 65, 95]
    for dt in door_times:
        spike = 620 * np.exp(-((t - dt - 1.2) / 2.0) ** 2)
        tail = 140 * np.exp(-np.clip(t - dt - 4, 0, None) / 18) * (t > dt + 4)
        pm += spike + tail
    pm = np.clip(pm, 2, None)

    who_g, who_24 = 5, 15  # WHO 2021 AQG annual & 24-h
    n_frames = 60
    frames = []
    idxs = np.linspace(20, len(t) - 1, n_frames).astype(int)
    for i in idxs:
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(t[:i], pm[:i], color=EMBER, lw=1.6)
        ax.axhline(who_g, color=CLEAN, lw=1, ls="--")
        ax.axhline(who_24, color=STEEL, lw=1, ls=":")
        ax.text(1, who_g + 14, "WHO annual guideline (5 µg/m³)", fontsize=7.5,
                color=CLEAN)
        ax.text(1, who_24 + 14, "WHO 24-h guideline (15 µg/m³)", fontsize=7.5,
                color=STEEL)
        for dt in door_times:
            if t[i] > dt:
                ax.annotate("door opened", (dt, pm[np.argmin(abs(t - dt - 1.2))]),
                            textcoords="offset points", xytext=(-14, 12),
                            fontsize=8, color=TEXT,
                            arrowprops=dict(arrowstyle="->", lw=0.7))
        ax.set_xlim(0, 120)
        ax.set_ylim(0, 700)
        ax.set_xticks(range(0, 121, 20))
        ax.set_xticklabels(["19:00", "19:20", "19:40", "20:00",
                          "20:20", "20:40", "21:00"])
        ax.set_xlabel("Time (evening)")
        ax.set_ylabel("Living-room PM2.5 (µg/m³)")
        ax.set_title("Every refuelling floods the room with PM2.5\n"
                     "(stylised, after Chakraborty et al. 2020 — incl. 'eco' stoves)",
                     fontsize=11, fontweight="bold")
        ax.spines[["top", "right"]].set_visible(False)
        frames.append(gif_frames(fig))
        plt.close(fig)
    write_gif(frames, "anim_refuel_spike.gif", duration=140)


# ------------------------------------------------------------ gif 2
def anim_dispersion():
    """
    Top-down stylised smoke dispersion from one chimney into neighbouring
    homes on a residential street — the 'secondhand smoke' mechanism.
    """
    rng = np.random.default_rng(3)
    nx = 80
    x = np.linspace(0, 40, nx)      # street cross-section, metres
    y = np.linspace(0, 25, 50)      # along-street, metres
    X, Y = np.meshgrid(x, y)
    cx, cy = 20, 15                  # chimney position (mid-house)

    # cumulative smoke field: advected + diffused puffs
    field = np.zeros_like(X)
    frames = []
    n_frames = 60
    puff_x = 0.55                    # slow drift direction (light wind)

    houses = [(12, 8, 8, 6), (12, 17, 8, 6), (4, 8, 6, 6), (28, 8, 6, 6),
              (4, 17, 6, 6), (28, 17, 6, 6)]

    for f in range(n_frames):
        age = f / n_frames
        # growing plume: multiple overlapping Gaussians drifting downwind
        field *= 0.90
        for k in range(3):
            sig = 1.2 + age * 6 + k * 0.9
            amp = np.exp(-age * 2.5) * 9
            field += amp * np.exp(-(((X - cx - age * 8 * puff_x) ** 2 +
                                     (Y - cy) ** 2) / (2 * sig ** 2)))
        field += rng.normal(0, 0.04, field.shape)
        field = np.clip(field, 0, None)

        if f % 2 == 0 or f == n_frames - 1:
            fig, ax = plt.subplots(figsize=(7.5, 4.6))
            ax.imshow(field, extent=[0, 40, 0, 25], origin="lower",
                      cmap="OrRd", vmin=0, vmax=6, alpha=0.9)
            for (hx, hy, w, h) in houses:
                rect = plt.Rectangle((hx, hy), w, h, fill=True,
                                     facecolor="#4d4d4d", edgecolor="black",
                                     zorder=3)
                ax.add_patch(rect)
            ax.plot(cx, cy + 0.3, marker="^", ms=11, color="#2b2b2b",
                    zorder=4, markeredgecolor="white")
            ax.annotate("your chimney", (cx, cy), textcoords="offset points",
                        xytext=(8, 8), fontsize=9, fontweight="bold")
            ax.annotate("neighbour's bedroom window", (16, 17.2),
                        textcoords="offset points", xytext=(-140, -24),
                        fontsize=8, color=TEXT,
                        arrowprops=dict(arrowstyle="->", lw=0.7, color=TEXT))
            ax.set_xlim(0, 40)
            ax.set_ylim(0, 25)
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_title("Wood smoke is the other secondhand smoke:\n"
                         "the plume doesn't stop at the fence (stylised)",
                         fontsize=11, fontweight="bold")
            frames.append(gif_frames(fig))
            plt.close(fig)
    write_gif(frames, "anim_dispersion.gif", duration=160, hold_last=14)


# ---------------------------------------------------------------- fig 6
def fig_particle_size():
    """Aerodynamic diameter vs deposition region (log scale)."""
    fig, ax = plt.subplots(figsize=(8.5, 4.4))
    ax.set_xscale("log")
    zones = [
        (10, 120, SMOKE, 5.0),
        (2.5, 10, STEEL, 4.0),
        (0.1, 2.5, EMBER, 3.0),
        (0.05, 0.1, "#8c2d04", 2.0),
    ]
    for lo, hi, color, y in zones:
        ax.broken_barh([(lo, hi - lo)], (y - 0.35, 0.7), facecolors=color,
                       edgecolors="black", linewidth=0.5, alpha=0.85)
    ax.text(9.5, 5.0, "trapped in nose & throat —\ncoughed or swallowed out ",
            ha="right", va="center", fontsize=8, color=SMOKE,
            fontweight="bold")
    ax.text(2.3, 4.0, "conducting airways ", ha="right", va="center",
            fontsize=8, color=STEEL, fontweight="bold")
    ax.text(0.095, 3.0, "alveoli — the gas-exchange\nsurface ", ha="right",
            va="center", fontsize=8, color=EMBER, fontweight="bold")
    ax.text(0.115, 2.0, " UFP — some cross into the bloodstream", ha="left",
            va="center", fontsize=8, color="#8c2d04", fontweight="bold")

    items = [("human hair", 70), ("PM10", 10), ("PM2.5", 2.5),
             ("PM1", 1.0), ("UFP", 0.1)]
    for name, d in items:
        ax.axvline(d, color="black", lw=0.6, ls=":", alpha=0.5,
                   ymin=0.05, ymax=0.9)
        ax.plot(d, 5.62, marker="v", color=TEXT, ms=7, clip_on=False)
        ax.text(d, 5.75, f"{name}\n{d:g} µm", ha="center", va="bottom",
                fontsize=8, fontweight="bold")
    ax.set_xlim(0.04, 160)
    ax.set_ylim(0.8, 6.6)
    ax.set_yticks([])
    ax.set_xlabel("Aerodynamic diameter (µm, log scale)")
    ax.set_title("Where particles land in the lungs — size decides",
                 fontsize=12, fontweight="bold", pad=26)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.text(0.99, 0.04,
            "Wood smoke is dominated by the fine end: ~half of wood-smoke particles\n"
            "are ultrafine (<0.1 µm) in chamber studies — invisible, reaching the\n"
            "alveoli and crossing into blood (Barregård 2006; Nemmar 2002).",
            transform=ax.transAxes, ha="right", va="bottom",
            fontsize=7, color=SMOKE)
    save(fig, "fig_particle_size.png")


# ---------------------------------------------------------------- fig 7
def fig_burn_types():
    """Two-panel: PM2.5 per kg fuel and per typical session (derived estimates)."""
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.6))

    # panel A — per kg fuel
    namesA = ["Garden bonfire\n(damp waste)", "Open fireplace /\nfire pit",
              "Old wood stove", "Ecodesign stove"]
    valsA = [22, 13, 11.7, 1.5]
    colsA = ["#8c2d04", EMBER, EMBER, "#e6a173"]
    y = np.arange(len(namesA))[::-1]
    a1.barh(y, valsA, color=colsA, edgecolor="black", linewidth=0.5,
            height=0.6)
    for yi, v in zip(y, valsA):
        a1.annotate(f"~{v:g} g", (v, yi), textcoords="offset points",
                    xytext=(6, -4), fontsize=10, fontweight="bold")
    a1.set_yticks(y)
    a1.set_yticklabels(namesA, fontsize=9)
    a1.set_xscale("log")
    a1.set_xlim(0.8, 60)
    a1.set_xlabel("PM2.5 per kg fuel (g, log) — derived")
    a1.set_title("Per kilogram burned", fontsize=11.5, fontweight="bold")
    a1.spines[["top", "right"]].set_visible(False)

    # panel B — per session
    namesB = ["Garden bonfire\n(~100 kg waste)", "Fire pit evening\n(~8 kg)",
              "Open fireplace evening\n(~5 kg)", "Ecodesign stove evening\n(~5 kg)",
              "Gas boiler evening\n(equivalent heat)"]
    valsB = [2200, 104, 63, 7, 0.02]
    colsB = ["#8c2d04", EMBER, EMBER, "#e6a173", CLEAN]
    y2 = np.arange(len(namesB))[::-1]
    a2.barh(y2, valsB, color=colsB, edgecolor="black", linewidth=0.5,
            height=0.6)
    for yi, v in zip(y2, valsB):
        a2.annotate(f"~{v:g} g", (v, yi), textcoords="offset points",
                    xytext=(6, -4), fontsize=10, fontweight="bold")
    a2.set_yticks(y2)
    a2.set_yticklabels(namesB, fontsize=9)
    a2.set_xscale("log")
    a2.set_xlim(0.005, 30000)
    a2.set_xlabel("PM2.5 per session (g, log) — derived")
    a2.set_title("Per typical session", fontsize=11.5, fontweight="bold")
    a2.text(1500, y2[0], "one bonfire \u2248 ~300 stove evenings ",
            color="white", fontsize=8, fontweight="bold", ha="right",
            va="center")
    a2.spines[["top", "right"]].set_visible(False)

    fig.suptitle("Bonfires, fire pits, fireplaces, stoves — same fuel, very "
                 "different doses", fontsize=12.5, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.90])
    fig.text(0.5, -0.07,
             "Derived estimates: EMEP/CMO g/MWh factors × ~0.0043 kg⁻¹ seasoned wood; damp garden\n"
             "waste penalised ~1.5–2.5× (McDonald 2000; Kocbach Bølling 2009). Order-of-magnitude —\n"
             "assumptions documented in burn-types.md.",
             ha="center", va="top", fontsize=7, color=SMOKE)
    save(fig, "fig_burn_types.png")


# ------------------------------------------------------------- anim 3
def anim_body_pathway():
    """
    Schematic particle journey: nose -> trachea -> bronchi -> alveoli,
    with ultrafines crossing into the bloodstream and reaching the heart.
    Stylised diagram — mechanisms from Nemmar 2002, Barregård 2006.
    """
    import matplotlib.patches as mpatches

    # waypoints per class
    PATHS = {
        "PM10":  [(28, 47), (22, 44), (18, 41), (17, 33)],
        "PM2.5": [(28, 47), (22, 44), (18, 41), (17, 24),
                  (14, 21), (10, 16), (10, 10)],
        "UFP":   [(28, 47), (22, 44), (18, 41), (17, 24),
                  (20, 21), (25, 16), (26, 9), (30, 6.5),
                  (37, 7.5), (43, 10)],
    }
    COLORS = {"PM10": "#8c8c8c", "PM2.5": EMBER, "UFP": "#8c2d04"}
    SIZES = {"PM10": 26, "PM2.5": 15, "UFP": 8}
    SPEED = {"PM10": 0.075, "PM2.5": 0.055, "UFP": 0.05}

    def path_xy(pts, prog):
        pts = np.array(pts)
        seg = np.sqrt(((np.diff(pts, axis=0)) ** 2).sum(axis=1))
        cum = np.concatenate([[0], np.cumsum(seg)])
        L = cum[-1]
        d = np.clip(prog, 0, 1) * L
        i = np.searchsorted(cum, d, side="right") - 1
        i = min(i, len(seg) - 1)
        f = (d - cum[i]) / seg[i] if seg[i] > 0 else 0
        return pts[i] + f * (pts[i + 1] - pts[i])

    def draw_static(ax):
        # head
        head = mpatches.Circle((18, 49), 8.5, facecolor="#f2e4d5",
                               edgecolor=TEXT, lw=1.2, zorder=2)
        ax.add_patch(head)
        ax.add_patch(mpatches.Polygon([[25.5, 50], [28.5, 47.5], [25.2, 46.5]],
                                      facecolor="#f2e4d5", edgecolor=TEXT,
                                      lw=1.0, zorder=3))
        ax.add_patch(mpatches.Ellipse((18, 52), 10, 6, facecolor="#e8c4e8",
                                      edgecolor=TEXT, lw=0.8, zorder=3))
        ax.text(18, 52, "brain", fontsize=6.5, ha="center", va="center",
                zorder=4)
        # trachea
        ax.plot([17, 17], [41, 24], color="#d9b38c", lw=7, zorder=1,
                solid_capstyle="round")
        ax.plot([17, 14, 10], [24, 21, 17], color="#d9b38c", lw=5, zorder=1,
                solid_capstyle="round")
        ax.plot([17, 20, 25], [24, 21, 17], color="#d9b38c", lw=5, zorder=1,
                solid_capstyle="round")
        # lungs
        for (lx, lw_) in [(10, 13), (26, 11)]:
            ax.add_patch(mpatches.Ellipse((lx, 14), lw_, 15,
                                          facecolor="#f6c8b8",
                                          edgecolor=TEXT, lw=1.1, zorder=1,
                                          alpha=0.95))
        # alveoli
        for (ax_, ay_) in [(9, 8.5), (12, 8), (25, 8.5), (27.5, 8)]:
            ax.add_patch(mpatches.Circle((ax_, ay_), 1.5, facecolor="#fbe3d9",
                                         edgecolor="#c46a4a", lw=0.8,
                                         zorder=2))
        ax.text(11, 4.6, "alveoli", fontsize=7, ha="center", color=TEXT)
        # blood vessel
        ax.plot([26, 30, 37, 43], [8.8, 6.5, 7.5, 10], color="#c0392b",
                lw=6, alpha=0.35, zorder=1, solid_capstyle="round")
        ax.text(35, 4.8, "bloodstream", fontsize=7, ha="center",
                color="#c0392b")
        # heart
        hx, hy = 46, 11
        heart_path = mpatches.Path(
            [(hx, hy - 4), (hx - 7, hy + 1.5), (hx - 3.5, hy + 6),
             (hx, hy + 3), (hx + 3.5, hy + 6), (hx + 7, hy + 1.5),
             (hx, hy - 4)],
            [mpatches.Path.MOVETO, mpatches.Path.CURVE4,
             mpatches.Path.CURVE4, mpatches.Path.CURVE4,
             mpatches.Path.CURVE4, mpatches.Path.CURVE4,
             mpatches.Path.CURVE4])
        ax.add_patch(mpatches.PathPatch(heart_path, facecolor="#c0392b",
                                        edgecolor="black", lw=0.8, zorder=2))
        ax.text(46, 0.5, "heart", fontsize=7.5, ha="center", color=TEXT)
        # zone labels
        ax.annotate("nose & throat\n(PM10 caught here)", (27, 47),
                    textcoords="offset points", xytext=(12, 12),
                    fontsize=7, color=SMOKE,
                    arrowprops=dict(arrowstyle="->", lw=0.6, color=SMOKE))
        ax.annotate("airways (PM2.5)", (13, 19), textcoords="offset points",
                    xytext=(-58, -6), fontsize=7, color=SMOKE,
                    arrowprops=dict(arrowstyle="->", lw=0.6, color=SMOKE))
        # legend
        handles = [plt.Line2D([], [], marker="o", ls="", color=COLORS[k],
                              ms=np.sqrt(SIZES[k]), label=k)
                   for k in ("PM10", "PM2.5", "UFP")]
        ax.legend(handles=handles, loc="upper right", fontsize=8,
                  frameon=True, title="particle class", title_fontsize=8)
        ax.set_xlim(0, 60)
        ax.set_ylim(-2, 62)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title("Where inhaled wood-smoke particles go\n"
                     "(stylised — mechanisms: Nemmar 2002; Barregård 2006)",
                     fontsize=11, fontweight="bold")

    rng = np.random.default_rng(5)
    parts = []
    for cls in ("PM10", "PM2.5", "UFP"):
        n = {"PM10": 8, "PM2.5": 16, "UFP": 22}[cls]
        for i in range(n):
            parts.append({
                "cls": cls, "spawn": rng.uniform(0, 45),
                "jit": rng.normal(0, 0.6, 2),
                "rate": SPEED[cls] * rng.uniform(0.8, 1.2),
            })

    frames = []
    n_frames = 70
    for f in range(n_frames):
        fig, ax = plt.subplots(figsize=(8, 5.5))
        draw_static(ax)
        for p in parts:
            prog = (f - p["spawn"]) * p["rate"]
            if prog <= 0:
                continue
            xy = path_xy(PATHS[p["cls"]], prog) + p["jit"]
            ax.scatter(*xy, s=SIZES[p["cls"]], color=COLORS[p["cls"]],
                       zorder=5, edgecolors="none", alpha=0.9)
        # heart pulse after UFPs arrive
        pulse = 1 + 0.06 * np.sin(f * 0.9) if f > 40 else 1
        ax.scatter(46, 11, s=60 * pulse, color="#ffb3a7", zorder=1)
        frames.append(gif_frames(fig))
        plt.close(fig)
    write_gif(frames, "anim_body_pathway.gif", duration=110)


# ------------------------------------------------------------- anim 4
def anim_burn_types():
    """
    Three-panel stylised comparison: chimney plume (stove), head-height
    smoke (fire pit), mass plume (bonfire).
    """
    rng = np.random.default_rng(9)
    x = np.linspace(0, 40, 70)
    y = np.linspace(0, 22, 45)
    X, Y = np.meshgrid(x, y)

    # (source x, source y, drift, initial sigma, growth, amp, colour, vmax)
    SOURCES = [
        ("Wood stove — chimney height,\nevery evening, all winter",
         (12, 13), 0.35, 1.0, 4.5, 5.0, "OrRd", 6),
        ("Fire pit — released at seated\nhead height",
         (12, 6), 0.55, 1.4, 6.5, 7.0, "OrRd", 9),
        ("Garden bonfire — one event,\nthe whole street",
         (12, 5), 0.75, 2.4, 9.5, 13.0, "YlOrBr", 15),
    ]

    def houses(ax):
        for (hx, hy, w, h) in [(26, 0, 8, 8), (14, 0, 8, 8), (0, 0, 8, 8)]:
            ax.add_patch(plt.Rectangle((hx, hy), w, h, facecolor="#4d4d4d",
                                       edgecolor="black", zorder=3))
            ax.add_patch(plt.Polygon([[hx - 0.5, h], [hx + w / 2, h + 2.5],
                                      [hx + w + 0.5, h]],
                                     facecolor="#3a3a3a", edgecolor="black",
                                     zorder=3))

    n_frames = 48
    frames = []
    fields = [np.zeros_like(X) for _ in SOURCES]
    for f in range(n_frames):
        age = f / n_frames
        if f % 2 == 0 or f == n_frames - 1:
            fig, axes = plt.subplots(1, 3, figsize=(11, 3.6))
        for si, (title, (cx, cy), drift, sig0, grow, amp, cmap, vmax) in \
                enumerate(SOURCES):
            fields[si] *= 0.90
            sig = sig0 + age * grow
            fields[si] += amp * np.exp(
                -(((X - cx - age * 9 * drift) ** 2) / (2 * sig ** 2) +
                  ((Y - cy - age * 2.5) ** 2) / (2 * (sig * 0.8) ** 2)))
            fields[si] += rng.normal(0, 0.03, X.shape)
            fields[si] = np.clip(fields[si], 0, None)

            if f % 2 == 0 or f == n_frames - 1:
                ax = axes[si]
                ax.imshow(fields[si], extent=[0, 40, 0, 22], origin="lower",
                          cmap=cmap, vmin=0, vmax=vmax, alpha=0.92)
                houses(ax)
                if si == 0:
                    ax.add_patch(plt.Rectangle((cx - 0.6, 8), 1.2, 5,
                                               facecolor="#3a3a3a", zorder=4))
                    ax.plot(cx, cy, marker="^", ms=8, color="black", zorder=5)
                elif si == 1:
                    ax.plot(cx - 4, 4.5, marker="$p$", ms=26, color="#222",
                            zorder=5)
                    ax.add_patch(plt.Circle((cx - 4, 7.5), 1.3,
                                            facecolor="#f2e4d5",
                                            edgecolor="black", zorder=5))
                    ax.add_patch(plt.Polygon([[cx - 2, cy], [cx + 2, cy],
                                              [cx, cy + 1.8]],
                                             facecolor="#333", zorder=4))
                else:
                    ax.add_patch(plt.Polygon([[cx - 3, 0], [cx + 3, 0],
                                              [cx, cy]],
                                             facecolor="#4a2c14",
                                             edgecolor="black", zorder=4))
                    ax.add_patch(plt.Circle((cx, cy + 0.5), 1.0,
                                            facecolor="#ff7b00",
                                            edgecolor="#b34700", zorder=5))
                ax.set_xlim(0, 40)
                ax.set_ylim(0, 22)
                ax.set_xticks([])
                ax.set_yticks([])
                ax.set_title(title, fontsize=8.5)
        if f % 2 == 0 or f == n_frames - 1:
            fig.suptitle("Same fuel, different smoke: where each burn type "
                         "puts its plume (stylised)", fontsize=11,
                         fontweight="bold")
            fig.tight_layout(rect=[0, 0, 1, 0.90])
            frames.append(gif_frames(fig))
            plt.close(fig)
    write_gif(frames, "anim_burn_types.gif", duration=170, hold_last=14)


if __name__ == "__main__":
    fig_heating_ef()
    fig_uk_pm25_sources()
    fig_wood_share_studies()
    fig_launceston()
    fig_diurnal()
    fig_particle_size()
    fig_burn_types()
    anim_refuel_spike()
    anim_dispersion()
    anim_body_pathway()
    anim_burn_types()
    interactive_sources()
    print("done")
