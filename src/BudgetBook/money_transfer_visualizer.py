import datetime
from typing import List

import pandas as pd
import plotly.graph_objects as go
from BudgetBook.helper import CURRENCY_SYMBOL, Category

from BudgetBook.regular_money_transfer import RegularMoneyTransfer


import plotly.express as px

CATEGORY_TO_COLOR_MAP = {
    c.name: px.colors.qualitative.Plotly[idx] for idx, c in enumerate(Category)
}


class MoneyTransferVisualizer:
    def __init__(self) -> None:
        self._scheduled_transfers: List[RegularMoneyTransfer] = []
        self._from_date = None
        self._to_date = None
        self._dataframe_cache = None

    def clear_transfers(self):
        self._scheduled_transfers.clear()
        self._dataframe_cache = None
        self._from_date = None
        self._to_date = None

    def add_transfer(self, transfer: RegularMoneyTransfer):
        self._scheduled_transfers.append(transfer)

    def add_transfers(self, transfers: List[RegularMoneyTransfer]):
        self._scheduled_transfers.extend(transfers)

    def set_analysis_interval(self, from_date, to_date):
        self._from_date = from_date
        self._to_date = to_date
        self._to_dataframe()

    def _to_dataframe(self):
        indivdual_transfers = []

        for scheduled_transfer in self._scheduled_transfers:
            transfers = [
                (
                    transfer.get_date(),
                    transfer.get_category().name,
                    transfer.get_name(),
                    transfer.get_desc(),
                    transfer.get_amount(),
                )
                for transfer in scheduled_transfer.iterate(
                    from_date=self._from_date, up_to=self._to_date
                )
            ]
            indivdual_transfers.extend(transfers)

        self._dataframe_cache = pd.DataFrame(
            indivdual_transfers, columns=["date", "category", "name", "desc", "amount"]
        )
        self._dataframe_cache["category"] = [
            str(s) for s in self._dataframe_cache["category"]
        ]
        self._dataframe_cache["date"] = pd.to_datetime(self._dataframe_cache["date"])
        self._dataframe_cache.set_index("date", inplace=True)

        self._dataframe_cache["date_without_day"] = [
            datetime.date(year=d.year, month=d.month, day=1)
            for d in self._dataframe_cache.index
        ]
        print("to_df_called")

    def plot_payments_per_month(self):
        df = self._dataframe_cache.reset_index()
        df = df[df["amount"] < 0]
        df["abs_amount"] = -df["amount"]

        fig = go.Figure()

        for category in df["category"].unique():
            mask = df["category"] == category
            curr_df = df[mask]
            fig.add_trace(
                go.Bar(
                    name=category,
                    x=curr_df["date_without_day"],
                    y=curr_df["abs_amount"],
                    text=[
                        f"{d['date']: %d.%m.%Y}<br>{d['name'][:40]}"
                        for idx, d in curr_df.iterrows()
                    ],
                    marker_color=CATEGORY_TO_COLOR_MAP[category],
                    hovertemplate=f"%{{y:.2f}} {CURRENCY_SYMBOL}<br>%{{text}}<extra>{category}</extra>",
                ),
            )
        fig.update_layout(
            barmode="stack",
            title="Payments Per Month",
            xaxis_title="[Date]",
            yaxis_title=f"Payments Per Month [{CURRENCY_SYMBOL}]",
        )

        return fig

    def plot_balance_per_month(self):
        fig = go.Figure()
        average_balance_per_month = (
            self._dataframe_cache["amount"].groupby(by=pd.Grouper(freq="M")).sum()
        )
        average_balance_per_month.index = pd.DatetimeIndex(
            datetime.date(year=d.year, month=d.month, day=1)
            for d in average_balance_per_month.index
        )
        fig.add_trace(
            go.Scatter(
                name="Average",
                x=average_balance_per_month.index,
                y=average_balance_per_month,
                hovertemplate=f"%{{y:.2f}} {CURRENCY_SYMBOL}<br>%{{x}}<extra></extra>",
            ),
        )

        fig.update_layout(
            barmode="group",
            title="Balance Per Month",
            xaxis_title="[Date]",
            yaxis_title=f"Average Balance Per Month [{CURRENCY_SYMBOL}]",
        )

        return fig

    def plot_transfers_per_month(self):
        df = (
            self._dataframe_cache.reset_index()
            .groupby(["date_without_day", "category"])
            .sum()
            .reset_index()
        )

        fig = go.Figure()

        for category in df["category"].unique():
            mask = df["category"] == category
            curr_df = df[mask]
            fig.add_trace(
                go.Bar(
                    name=category,
                    x=curr_df["date_without_day"],
                    y=curr_df["amount"],
                    marker_color=CATEGORY_TO_COLOR_MAP[category],
                    hovertemplate=f"%{{y:.2f}} {CURRENCY_SYMBOL}<br>%{{x}}<extra>{category}</extra>",
                ),
            )
        fig.update_layout(
            barmode="group",
            title="Transfers Per Month",
            xaxis_title="[Date]",
            yaxis_title=f"Transfers Per Month [{CURRENCY_SYMBOL}]",
        )
        return fig

    def plot_pie_chart_per_cateogry(self):
        grouped_per_category = self._dataframe_cache[
            self._dataframe_cache["amount"] < 0
        ].groupby(by="category")
        amount_per_category = grouped_per_category["amount"].sum().abs()

        fig = go.Figure()
        fig.add_trace(
            go.Pie(
                values=amount_per_category,
                labels=amount_per_category.index,
            )
        )
        fig.update_traces(
            marker=dict(
                colors=[CATEGORY_TO_COLOR_MAP[c] for c in amount_per_category.index]
            )
        )
        fig.update_layout(title="Payments per Category")
        return fig
