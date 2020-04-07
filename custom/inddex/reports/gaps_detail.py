from custom.inddex.filters import (
    FaoWhoGiftFoodGroupDescriptionFilter,
    FoodTypeFilter,
    GapDescriptionFilter,
    GapTypeFilter,
    RecallStatusFilter,
)
from custom.inddex.ucr.data_providers.gaps_report_by_item_data import (
    GapsReportByItemDetailsData,
    GapsReportByItemSummaryData,
)
from custom.inddex.utils import MultiTabularReport


class GapsDetailReport(MultiTabularReport):
    title = 'Output 2b - Detailed Information on Gaps'
    name = title
    slug = 'gaps_detail'

    @property
    def fields(self):
        fields = super().fields
        fields += [
            GapTypeFilter,
            GapDescriptionFilter,
            FaoWhoGiftFoodGroupDescriptionFilter,
            FoodTypeFilter,
            RecallStatusFilter,
        ]
        return fields


    @property
    def report_config(self):
        report_config = super().report_config
        report_config.update(
            gap_type=self.request.GET.get('gap_type') or '',
            recall_status=self.request.GET.get('recall_status') or '',
            fao_who_gift_food_group_description=self.fao_who_gift_food_group_description,
            gap_description=self.gap_description,
            food_type=self.food_type,
        )
        return report_config

    @property
    def fao_who_gift_food_group_description(self):
        return self.request.GET.get('fao_who_gift_food_group_description') or ''

    @property
    def gap_description(self):
        return self.request.GET.get('gap_description') or ''

    @property
    def food_type(self):
        return self.request.GET.get('food_type') or ''

    @property
    def data_providers(self):
        return [
            GapsReportByItemSummaryData(config=self.report_config),
            GapsReportByItemDetailsData(config=self.report_config)
        ]
