"""
preprocessing.py
Funções de limpeza e transformação dos dados brutos.
"""

import pandas as pd


def clean_orders(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["order_amount"] = (
        df["order_amount"]
        .str.replace(r"[\$,]", "", regex=True)
        .astype(float)
    )
    df["delivery_hour"] = pd.to_datetime(
        df["delivery_hour"], format="%H:%M:%S"
    ).dt.hour
    df["day_of_week"] = df["date"].dt.day_name()
    df["month"] = df["date"].dt.to_period("M").astype(str)
    df["has_missing"] = df["items_missing"].astype(bool)
    return df


def clean_products(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.rename(columns={"produc_id": "product_id"})
    df["price"] = (
        df["price"]
        .str.replace(r"[\$,]", "", regex=True)
        .astype(float)
    )
    return df


def clean_drivers(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.rename(columns={"Trips": "trips"})
    return df


def build_master(orders, customers, drivers) -> pd.DataFrame:
    """Une pedidos com clientes e motoristas em um dataframe único."""
    df = orders.merge(customers, on="customer_id", how="left")
    df = df.merge(
        drivers[["driver_id", "driver_name", "age", "trips"]],
        on="driver_id",
        how="left",
        suffixes=("_customer", "_driver"),
    )
    return df
