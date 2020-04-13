from itertools import chain

from custom.inddex import filters
from custom.inddex.food import FoodData

from .utils import MultiTabularReport, format_row


class NutrientIntakeReport(MultiTabularReport):
    name = 'Output 3 - Disaggregated Intake Data by Food and Aggregated Daily Intake Data by Respondent'
    slug = 'nutrient_intake'
    export_only = True

    @property
    def fields(self):
        return [
            filters.CaseOwnersFilter,
            filters.DateRangeFilter,
            filters.GenderFilter,
            filters.AgeRangeFilter,
            filters.PregnancyFilter,
            filters.BreastFeedingFilter,
            filters.SettlementAreaFilter,
            filters.SupplementsFilter,
            filters.FaoWhoGiftFoodGroupDescriptionFilter,
            filters.RecallStatusFilter,
        ]

    @property
    def report_config(self):
        report_config = {}  # TODO port to FoodData.from_request
        request_slugs = [
            'gender',
            'age_range',
            'pregnant',
            'breastfeeding',
            'urban_rural',
            'supplements',
            'recall_status',
            'fao_who_gift_food_group_description',
        ]
        report_config.update({slug: self.request.GET.get(slug, '')
                              for slug in request_slugs})
        return report_config

    @property
    def data_providers(self):
        food_data = FoodData.from_request(self.domain, self.request)
        return [
            DailyIntakeData(food_data),
        ]


class DailyIntakeData:
    title = 'Aggregated Daily Intake By Respondent'
    slug = 'aggr_daily_intake_by_rspndnt'
    _metadata_columns = [
        'unique_respondent_id',
        'location_id',
        'respondent_id',
        'recall_case_id',
        'opened_by_username',
        'owner_name',
        'recalled_date',
        'recall_status',
        'gender',
        'age_years_calculated',
        'age_months_calculated',
        'age_range',
        'supplements',
        'urban_rural',
        'pregnant',
        'breastfeeding',
    ]

    def __init__(self, food_data):
        self._food_data = food_data
        self._nutrient_names = self._food_data.fixtures.nutrient_names

    @property
    def headers(self):
        return self._metadata_columns + list(self._nutrient_names)

    @property
    def rows(self):
        rows = {}
        for row in self._food_data.rows:
            nutrients = [row.get_nutrient_amt(name) for name in self._nutrient_names]
            key = (row.unique_respondent_id, row.recalled_date)
            if key not in rows:
                rows[key] = {
                    'static_cols': [getattr(row, col) for col in self._metadata_columns],
                    'nutrients': nutrients
                }
            else:
                rows[key]['nutrients'] = map(_sum, zip(rows[key]['nutrients'], nutrients))

        for key, row in sorted(rows.items()):
            yield format_row(chain(row['static_cols'], row['nutrients']))


def _sum(items):
    return sum(filter(None, items))
