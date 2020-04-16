from collections import defaultdict
from math import ceil
from statistics import mean, median, stdev

from custom.inddex import filters
from custom.inddex.food import FoodData

from .utils import MultiTabularReport, format_row


class NutrientStatsReport(MultiTabularReport):
    name = 'Output 4 - Nutrient Intake Summary Statistics'
    slug = 'nutrient_stats'

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
            filters.RecallStatusFilter
        ]

    @property
    def data_providers(self):
        food_data = FoodData.from_request(self.domain, self.request)
        return [NutrientStatsData(food_data)]


class NutrientStatsData:
    title = 'Nutrient Intake Summary Stats'
    slug = 'nutr_intake_summary_stats'

    def __init__(self, food_data):
        self._food_data = food_data
        self._nutrient_names = self._food_data.fixtures.nutrient_names

    @property
    def headers(self):
        return [
            'nutrient', 'mean', 'median', 'std_dev', 'percentile_05',
            'percentile_25', 'percentile_50', 'percentile_75', 'percentile_95'
        ]

    @property
    def rows(self):
        for nutrient, amts in self._get_recall_totals():
            yield format_row([
                nutrient,
                mean(amts) if len(amts) >= 1 else None,
                median(amts) if len(amts) >= 1 else None,
                stdev(amts) if len(amts) >= 2 else None,
                percentile(amts, .05),
                percentile(amts, .25),
                percentile(amts, .5),
                percentile(amts, .75),
                percentile(amts, .95),
            ])

    def _get_recall_totals(self):
        totals = defaultdict(lambda: defaultdict(int))
        for row in self._food_data.rows:
            for nutrient in self._nutrient_names:
                totals[nutrient][row.recall_case_id] += row.get_nutrient_amt(nutrient) or 0

        for nutrient in self._nutrient_names:
            yield nutrient, list(sorted(totals[nutrient].values()))


def percentile(items, q):
    """
    Compute the q-th percentile of the elements in 'items' by nearest-rank

    :param items: pre-sorted array of numbers

    >>> percentile([15, 20, 35, 40, 50], .05)
    15
    >>> percentile([15, 20, 35, 40, 50], .3)
    20
    >>> percentile([15, 20, 35, 40, 50], .4)
    20
    >>> percentile([15, 20, 35, 40, 50], .5)
    35
    >>> percentile([3, 10], .5)
    3
    >>> percentile([], .5)
    """
    if not items:
        return None
    index = ceil(q * len(items)) - 1
    return items[index]
