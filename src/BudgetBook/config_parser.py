import enum
import yaml

from BudgetBook.helper import CURRENCY_SYMBOL


class ConfigKeywords:
    CATGORY_MAPPING_TOPLEVEL = "category_mapping"

    CATEGORY_RULE_AND = "and"
    CATEGORY_RULE_OR = "or"

    CSV_STATEMENT_PARSER_TOPLEVEL = "statement_parser"
    CSV_COLUMNS_TOPLEVEL = "csv_columns"

    CSV_DATE_FORMAT = "date_format"


class DataColumns:
    PAYMENT_PARTY = "payment_party"
    AMOUNT = "amount"
    TYPE_OF_TRANSFER = "type_of_transfer"
    DESCRIPTION = "description"
    DATE = "date"
    CATEGORY = "category"


DATA_COLUMN_TO_DISPLAY_NMAE = {
    DataColumns.PAYMENT_PARTY: "Payment Party",
    DataColumns.AMOUNT: f"Amount {CURRENCY_SYMBOL}",
    DataColumns.TYPE_OF_TRANSFER: "Type Of Transfer",
    DataColumns.DESCRIPTION: "Description",
    DataColumns.DATE: "Date",
    DataColumns.CATEGORY: "Category",
}


class ConfigParser:
    def __init__(self, yaml_file_path: str) -> None:
        with open(yaml_file_path, "r") as stream:
            self._config = yaml.safe_load(stream)

        self._category_mapping = self._config[ConfigKeywords.CATGORY_MAPPING_TOPLEVEL]
        self._statement_parser = self._config[
            ConfigKeywords.CSV_STATEMENT_PARSER_TOPLEVEL
        ]
        self._csv_statement_columns = self._statement_parser[
            ConfigKeywords.CSV_COLUMNS_TOPLEVEL
        ]

    def get_csv_date_format(self) -> str:
        return self._statement_parser[ConfigKeywords.CSV_DATE_FORMAT]

    def get_category_mapping(self) -> dict:
        return self._category_mapping

    def get_csv_columns_mapping(self) -> dict:
        return self._csv_statement_columns

    def get_csv_column_payment_party(self):
        return self._csv_statement_columns[DataColumns.PAYMENT_PARTY]

    def get_csv_column_amount(self):
        return self._csv_statement_columns[DataColumns.AMOUNT]

    def get_csv_column_type_of_transfer(self):
        return self._csv_statement_columns[DataColumns.TYPE_OF_TRANSFER]

    def get_csv_column_description(self):
        return self._csv_statement_columns[DataColumns.DESCRIPTION]

    def get_csv_column_date(self):
        return self._csv_statement_columns[DataColumns.DATE]
