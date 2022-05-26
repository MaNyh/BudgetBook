import base64
import io
import os.path
import sys
import plotly
from datetime import date, datetime
import pandas as pd
from dateutil.relativedelta import relativedelta

import dash_bootstrap_components as dbc
from dash import Dash, dcc, html, dash_table, no_update
import dash
from dash.dash_table.Format import Format, Scheme, Symbol
from dash.dependencies import Input, Output, State


SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "src"))
sys.path.append(SRC_DIR)

from BudgetBook.account_statement_parser import AccountStatementCsvParser
from BudgetBook.transaction_visualizer import TransactionVisualizer
from BudgetBook.config_parser import (
    DATA_COLUMN_TO_DISPLAY_NAME,
    ConfigParser,
    DataColumns,
)
from BudgetBook.regular_transaction_predictor import RegularTransactionPredictor


def year(year: int) -> date:
    return date(year=year, month=1, day=1)


# builder = ReocurringBankTransferBuilder()
# builder.set_first_ocurrence(2022)
# builder.set_last_ocurrence(2023)
# for i in range(10):
#     amount = (random.random() - 0.5) * 1000.0
#     cat = (
#         Category.SALERY#         if amount > 0
#         else Category(random.randint(1, len(Category) - 1))
#     )
#     builder.set_category(cat)
#     builder.set_interval(0, random.randint(1, 5), 0)
#     builder.schedule_bank_transfer(f"dummy {i}", amount)

# scheduled_transactions = builder.get_scheduled_transactions()

default_start_date = date(year=2021, month=5, day=1)
default_end_date = date(year=2022, month=5, day=1)

config = ConfigParser("configuration.yaml")
csv_parser = AccountStatementCsvParser(
    r"C:\Users\Andreas Rottach\Google Drive\Umsaetze_2022.05.01.csv",
    config,
)
scheduled_transactions = csv_parser.to_dated_transactions()

global_transaction_visualizer = TransactionVisualizer(config)
global_transaction_visualizer.add_transactions(scheduled_transactions)
global_transaction_visualizer.set_analysis_interval(
    default_start_date, default_end_date
)


def generate_tabs(manager: TransactionVisualizer):
    tab1_content = generate_overview_tab(manager)
    tab2_content = generate_transactions_per_category_tab(manager)
    tab3_content = generate_detailed_transactions_tab(manager)
    tab4_content = generate_dataset_table_tab(manager)
    tab5_content = generate_prediction_tab(manager)

    return [
        dbc.Tab(tab1_content, label="Overview"),
        dbc.Tab(tab2_content, label="Transfers"),
        dbc.Tab(tab3_content, label="Individual Transfers"),
        dbc.Tab(tab4_content, label="Dataset"),
        dbc.Tab(tab5_content, label="Predictions"),
    ]


def hex_to_rgb(value):
    value = value.lstrip("#")
    lv = len(value)
    return tuple(int(value[i : i + lv // 3], 16) for i in range(0, lv, lv // 3))


def rgb_to_gray(rgb):
    return (rgb[0] + rgb[1] + rgb[2]) / 3


def generate_dataset_table_tab(manager: TransactionVisualizer):
    df = manager.plot_statement_dataframe()
    columns = [
        {
            "id": c,
            "name": c,
            "type": "numeric",
            "format": Format(precision=2, scheme=Scheme.fixed),
        }
        for c in df.columns
    ]
    id_amount_column = DATA_COLUMN_TO_DISPLAY_NAME[DataColumns.AMOUNT]
    id_category_column = DATA_COLUMN_TO_DISPLAY_NAME[DataColumns.CATEGORY]

    style_rules_for_categories = [
        {
            "if": {
                "filter_query": f"{{{id_category_column}}} = '{category}'",
                "column_id": id_category_column,
            },
            "backgroundColor": color,
            "color": "white" if rgb_to_gray(hex_to_rgb(color)) < 128 else "black",
        }
        for category, color in manager.category_to_color_map.items()
    ]
    tab4_content = dbc.Card(
        dbc.CardBody(
            [
                dash_table.DataTable(
                    id="statement-table",
                    columns=columns,
                    data=df.to_dict("records"),
                    filter_action="native",
                    sort_action="native",
                    sort_mode="multi",
                    page_action="native",
                    page_current=0,
                    page_size=20,
                    style_cell={
                        "whiteSpace": "pre-line",
                        "height": "auto",
                        "textAlign": "left",
                    },
                    style_table={
                        "width": "100%",
                    },
                    style_data_conditional=[
                        {
                            "if": {
                                "filter_query": f"{{{id_amount_column}}} < 0",
                                "column_id": id_amount_column,
                            },
                            "backgroundColor": "tomato",
                            "color": "white",
                        },
                        {
                            "if": {
                                "filter_query": f"{{{id_amount_column}}} > 0",
                                "column_id": id_amount_column,
                            },
                            "backgroundColor": "green",
                            "color": "white",
                        },
                        *style_rules_for_categories,
                    ],
                )
            ]
        ),
        className="mt-3",
    )

    return tab4_content


def generate_detailed_transactions_tab(manager: TransactionVisualizer):

    fig = plotly.subplots.make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        subplot_titles=(
            "Income Per Month",
            "Payments Per Month",
            "Internal Transfers Per Month",
        ),
    )

    manager.plot_income_per_month(fig=fig, row=1, col=1)
    manager.plot_payments_per_month(fig=fig, row=2, col=1)
    manager.plot_internal_transactions_per_month(fig=fig, row=3, col=1)

    fig.update_layout(legend=dict(yanchor="top", y=0.70, xanchor="left", x=1.01))

    tab3_content = dbc.Card(
        dbc.CardBody(
            [
                dcc.Graph(
                    id="plot_details",
                    figure=fig,
                    style={"height": "1400px"},
                ),
            ]
        ),
        className="mt-3",
    )

    return tab3_content


def generate_transactions_per_category_tab(manager: TransactionVisualizer):
    tab_content = dbc.Card(
        dbc.CardBody(
            [
                dcc.Graph(
                    id="transactions_per_month",
                    figure=manager.plot_transactions_per_month(),
                    style={"height": "80vh"},
                ),
            ]
        ),
        className="mt-3",
    )
    return tab_content


def generate_overview_tab(manager: TransactionVisualizer):
    tab_content = dbc.Card(
        dbc.CardBody(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            dcc.Graph(
                                id="balance_per_month",
                                figure=manager.plot_balance_per_month(),
                            )
                        ),
                        dbc.Col(
                            dcc.Graph(
                                id="pie_chart_per_cateogry",
                                figure=manager.plot_pie_chart_per_cateogry(),
                            )
                        ),
                    ]
                ),
                dbc.Row(
                    dbc.Col(
                        dcc.Graph(
                            id="category_variance",
                            figure=manager.plot_cateogory_variance(),
                            style={"height": "900px"},
                        )
                    )
                ),
            ]
        ),
        className="mt-3",
    )

    return tab_content


def generate_prediction_tab(manager: TransactionVisualizer):
    predictor = RegularTransactionPredictor(config)
    regular_transactions = predictor.to_regular_transactions(manager.get_transactions())
    df = pd.DataFrame.from_records([t.to_dict() for t in regular_transactions])

    df.rename(columns=DATA_COLUMN_TO_DISPLAY_NAME, inplace=True)

    columns = [
        {
            "id": c,
            "name": c,
            "type": "numeric",
            "format": Format(precision=2, scheme=Scheme.fixed),
        }
        for c in df.columns
    ]

    id_amount_column = DATA_COLUMN_TO_DISPLAY_NAME[DataColumns.AMOUNT]
    id_category_column = DATA_COLUMN_TO_DISPLAY_NAME[DataColumns.CATEGORY]

    style_rules_for_categories = [
        {
            "if": {
                "filter_query": f"{{{id_category_column}}} = '{category}'",
                "column_id": id_category_column,
            },
            "backgroundColor": color,
            "color": "white" if rgb_to_gray(hex_to_rgb(color)) < 128 else "black",
        }
        for category, color in manager.category_to_color_map.items()
    ]

    tab5_content = dbc.Card(
        dbc.CardBody(
            [
                dash_table.DataTable(
                    id="prediction-table",
                    columns=columns,
                    data=df.to_dict("records"),
                    filter_action="native",
                    sort_action="native",
                    sort_mode="multi",
                    page_action="native",
                    page_current=0,
                    page_size=20,
                    style_cell={
                        "whiteSpace": "pre-line",
                        "height": "auto",
                        "textAlign": "left",
                    },
                    style_table={
                        "width": "100%",
                    },
                    style_data_conditional=[
                        {
                            "if": {
                                "filter_query": f"{{{id_amount_column}}} < 0",
                                "column_id": id_amount_column,
                            },
                            "backgroundColor": "tomato",
                            "color": "white",
                        },
                        {
                            "if": {
                                "filter_query": f"{{{id_amount_column}}} > 0",
                                "column_id": id_amount_column,
                            },
                            "backgroundColor": "green",
                            "color": "white",
                        },
                        *style_rules_for_categories,
                    ],
                )
            ]
        ),
        className="mt-3",
    )

    return tab5_content


def generate_input_form(default_start_date, default_end_date):
    input_form = dbc.Form(
        [
            dbc.Row(
                [
                    dbc.Label(
                        "Statement Dataset",
                        html_for="upload-data",
                        width=2,
                    ),
                    dbc.Col(
                        dcc.Upload(
                            id="upload-data",
                            children=html.Div("Click to upload a csv file."),
                            style={
                                "width": "284px",
                                "height": "60px",
                                "lineHeight": "60px",
                                "borderWidth": "1px",
                                "borderStyle": "dashed",
                                "borderRadius": "5px",
                                "textAlign": "center",
                            },
                        )
                    ),
                ],
                class_name="mb-3",
            ),
            dbc.Row(
                [
                    dbc.Label(
                        "Select a date range to evaluate",
                        html_for="date-picker-range",
                        width=2,
                    ),
                    dbc.Col(
                        dcc.DatePickerRange(
                            id="date-picker-range",
                            initial_visible_month=datetime.now(),
                            start_date=default_start_date,
                            end_date=default_end_date,
                            display_format="DD/MM/YYYY",
                        ),
                        width=8,
                    ),
                ],
                class_name="mb-3",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Button("Update", id="update-button"),
                        width=2,
                    ),
                    dbc.Col(
                        dbc.Label("", id="error"),
                        width=8,
                    ),
                ],
                class_name="mb-3",
            ),
        ],
        class_name="m-2",
    )

    return input_form


from flask import Flask

server = Flask(__name__)
app = Dash(__name__, server=server, external_stylesheets=[dbc.themes.COSMO])
app.layout = dbc.Container(
    [
        html.H1("Budget Book Dashboard", style={"textAlign": "center"}),
        dbc.Button(
            "Open collapse",
            id="collapse-button",
            className="mb-3",
            color="primary",
            n_clicks=0,
        ),
        dbc.Collapse(
            dbc.Card(
                dbc.CardBody(generate_input_form(default_start_date, default_end_date))
            ),
            id="collapse",
            class_name="pb-1",
        ),
        dbc.Tabs(generate_tabs(global_transaction_visualizer), id="tabs"),
    ],
    style={"width": "80vw", "min-width": "80vw"},
)


def parse_uploaded_csv(contents, filename):
    content_type, content_string = contents.split(",")

    decoded = base64.b64decode(content_string)
    if "csv" in filename:
        iostream = io.StringIO(decoded.decode("utf-8"))
        csv_parser = AccountStatementCsvParser(
            iostream,
            config,
        )

        global_transaction_visualizer.clear_transactions()
        global_transaction_visualizer.add_transactions(
            csv_parser.to_dated_transactions()
        )
        global_transaction_visualizer.set_analysis_interval(
            csv_parser._csv_data[DataColumns.DATE].min(),
            csv_parser._csv_data[DataColumns.DATE].max() + relativedelta(days=1),
        )


@app.callback(
    [Output("collapse", "is_open"), Output("collapse-button", "children")],
    [Input("collapse-button", "n_clicks")],
    [State("collapse", "is_open")],
)
def toggle_collapse(n, is_open):
    if n:
        return not is_open, "Hide Settings" if not is_open else "Show Settings"
    return is_open, "Show Settings"


@app.callback(
    [
        Output("tabs", "children"),
        Output("date-picker-range", "start_date"),
        Output("date-picker-range", "end_date"),
        Output("error", "children"),
    ],
    State("date-picker-range", "start_date"),
    State("date-picker-range", "end_date"),
    Input("update-button", "n_clicks"),
    Input("upload-data", "contents"),
    State("upload-data", "filename"),
)
def update_output(start_date, end_date, n_clicks, contents, filename):
    ctx = dash.callback_context

    if not ctx.triggered:
        return dash.no_update

    error_msg = dash.no_update

    # File uploaded?
    if ctx.triggered[0]["prop_id"] == "upload-data.contents":
        if not filename.endswith(".csv"):
            error_msg = "Invalid file type selected. Only CSV is supported!"
        else:
            parse_uploaded_csv(contents, filename)
            if global_transaction_visualizer.dataset_is_valid():
                start_date = (
                    global_transaction_visualizer.get_first_transaction_date_in_analysis_interval()
                )
                end_date = (
                    global_transaction_visualizer.get_last_transaction_date_in_analysis_interval()
                )

                end_date = end_date.strftime("%Y-%m-%d")
                start_date = start_date.strftime("%Y-%m-%d")
                return (
                    dash.no_update,
                    start_date,
                    end_date,
                    "File Uploaded, adjust the date range and click on update!",
                )
            else:
                error_msg = "Internal error!"

    elif ctx.triggered[0]["prop_id"] == "update-button.n_clicks":
        if start_date is not None and end_date is not None and start_date < end_date:
            if global_transaction_visualizer.dataset_is_valid():
                global_transaction_visualizer.set_analysis_interval(
                    datetime.strptime(start_date, "%Y-%m-%d").date(),
                    datetime.strptime(end_date, "%Y-%m-%d").date()
                    + relativedelta(days=1),
                )
                return (
                    generate_tabs(global_transaction_visualizer),
                    dash.no_update,
                    dash.no_update,
                    "Data updated!",
                )
            else:
                error_msg = "Internal error!"
        else:
            error_msg = "Date Range not valid!"
    else:
        error_msg = "Invalid trigger!"

    return dash.no_update, dash.no_update, dash.no_update, error_msg


if __name__ == "__main__":

    app.run_server(debug=True)
