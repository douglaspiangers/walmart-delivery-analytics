"""
visualization.py
Funções de visualização padronizadas para o projeto.
"""

import matplotlib.pyplot as plt
import seaborn as sns

PALETTE = "Blues_d"
FIG_SIZE = (10, 5)


def bar_chart(data, x, y, title, xlabel, ylabel, color="steelblue"):
    fig, ax = plt.subplots(figsize=FIG_SIZE)
    ax.bar(data[x], data[y], color=color)
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    return fig


def line_chart(data, x, y, title, xlabel, ylabel):
    fig, ax = plt.subplots(figsize=FIG_SIZE)
    ax.plot(data[x], data[y], marker="o", color="steelblue", linewidth=2)
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    return fig


def heatmap(pivot_table, title, fmt=".0f", cmap="YlOrRd"):
    fig, ax = plt.subplots(figsize=(12, 5))
    sns.heatmap(pivot_table, annot=True, fmt=fmt, cmap=cmap, ax=ax)
    ax.set_title(title, fontsize=14, fontweight="bold")
    plt.tight_layout()
    return fig
