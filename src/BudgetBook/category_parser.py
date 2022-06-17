from BudgetBook.config_parser import DataColumns, ConfigKeywords, Config


class CategoryParser:
    def __init__(self, config: Config) -> None:
        self._config = config
        self._category_mapping = config.get_category_mapping()
        self._csv_columns_mapping = config.get_csv_columns_mapping()

    def get_category_for_record(self, record):
        if DataColumns.CATEGORY in record:
            return record[DataColumns.CATEGORY]

        for category, mapping_rules in self._category_mapping.items():
            if self._check_category_match(record, mapping_rules):
                return category

        return "Unknown Income" if record[DataColumns.AMOUNT] > 0 else "Unknown Payment"

    @staticmethod
    def _check_category_match(record, mapping_rules):
        has_and = ConfigKeywords.CATEGORY_RULE_AND in mapping_rules
        has_or = ConfigKeywords.CATEGORY_RULE_OR in mapping_rules

        if has_and:
            return CategoryParser._check_and(record, mapping_rules)
        elif has_or:
            return CategoryParser._check_or(record, mapping_rules)
        else:
            for filter_key, filter_values in mapping_rules.items():
                if CategoryParser._field_contains_any(
                    record[filter_key], filter_values
                ):
                    return True

        return False

    @staticmethod
    def _field_contains_any(field, candiates):
        return any(v.lower() in field.lower() for v in candiates)

    @staticmethod
    def _check_and(record, mapping_rules):
        for filter_key, filter_values in mapping_rules[
            ConfigKeywords.CATEGORY_RULE_AND
        ].items():
            if not CategoryParser._check_category_match(
                record,
                {filter_key: filter_values},
            ):
                return False
        return True

    @staticmethod
    def _check_or(record, mapping_rules):
        for filter_key, filter_values in mapping_rules[
            ConfigKeywords.CATEGORY_RULE_OR
        ].items():
            if CategoryParser._check_category_match(
                record,
                {filter_key: filter_values},
            ):
                return True
        return False
