"""
data_loader.py
Funções responsáveis por carregar os dados brutos do projeto.
"""

import pandas as pd
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"


def load_orders() -> pd.DataFrame:
    return pd.read_csv(RAW_DIR / "orders.csv")


def load_customers() -> pd.DataFrame:
    return pd.read_csv(RAW_DIR / "customers.csv")


def load_products() -> pd.DataFrame:
    return pd.read_csv(RAW_DIR / "products.csv")


def load_drivers() -> pd.DataFrame:
    return pd.read_csv(RAW_DIR / "drivers.csv")


def load_order_items() -> pd.DataFrame:
    return pd.read_csv(RAW_DIR / "order_items.csv")


def load_all() -> dict[str, pd.DataFrame]:
    """Carrega todas as tabelas e retorna um dicionário."""
    return {
        "orders": load_orders(),
        "customers": load_customers(),
        "products": load_products(),
        "drivers": load_drivers(),
        "order_items": load_order_items(),
    }
