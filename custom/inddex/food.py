from .fixtures import FixtureAccessor

MISSING = ''

IN_UCR = 'in_ucr'
IN_FOOD_FIXTURE = 'in_food_fixture'
IS_RECALL_META = 'is_recall_meta'


class I:
    def __init__(self, slug, *tags):
        self.slug = slug
        tags = set(tags)
        self.in_ucr = IN_UCR in tags
        self.in_food_fixture = IN_FOOD_FIXTURE in tags
        self.is_recall_meta = IS_RECALL_META in tags


INDICATORS = [
    I('unique_respondent_id', IN_UCR, IS_RECALL_META),
    I('location_id'),
    I('respondent_id', IN_UCR, IS_RECALL_META),
    I('recall_case_id', IN_UCR, IS_RECALL_META),
    I('opened_date', IN_UCR, IS_RECALL_META),
    I('opened_by_username', IN_UCR, IS_RECALL_META),
    I('owner_name', IN_UCR, IS_RECALL_META),
    I('recalled_date', IN_UCR, IS_RECALL_META),
    I('recall_status', IN_UCR, IS_RECALL_META),
    I('gender', IN_UCR, IS_RECALL_META),
    I('age_years_calculated', IN_UCR, IS_RECALL_META),
    I('age_months_calculated', IN_UCR, IS_RECALL_META),
    I('age_range', IS_RECALL_META),
    I('pregnant', IN_UCR, IS_RECALL_META),
    I('breastfeeding', IN_UCR, IS_RECALL_META),
    I('supplements', IN_UCR, IS_RECALL_META),
    I('urban_rural', IN_UCR, IS_RECALL_META),
    I('food_code', IN_UCR),
    I('food_name', IN_UCR, IN_FOOD_FIXTURE),
    I('recipe_name', IN_UCR),
    I('caseid'),
    I('reference_food_code', IN_UCR),
    I('base_term_food_code'),
    I('food_type', IN_UCR, IN_FOOD_FIXTURE),
    I('include_in_analysis', IN_UCR),
    I('food_status', IN_UCR),
    I('eating_time', IN_UCR),
    I('time_block', IN_UCR),
    I('fao_who_gift_food_group_code'),
    I('fao_who_gift_food_group_description'),
    I('user_food_group'),
    I('already_reported_food', IN_UCR),
    I('already_reported_food_case_id', IN_UCR),
    I('already_reported_recipe'),
    I('already_reported_recipe_case_id'),
    I('already_reported_recipe_name'),
    I('is_ingredient', IN_UCR),
    I('recipe_case_id', IN_UCR),
    I('ingr_recipe_code', IN_UCR),
    I('ingr_fraction'),
    I('ingr_recipe_total_grams_consumed'),
    I('short_name', IN_UCR),
    I('food_base_term', IN_UCR, IN_FOOD_FIXTURE),
    I('tag_1', IN_UCR, IN_FOOD_FIXTURE),
    I('other_tag_1', IN_UCR),
    I('tag_2', IN_UCR, IN_FOOD_FIXTURE),
    I('other_tag_2', IN_UCR),
    I('tag_3', IN_UCR, IN_FOOD_FIXTURE),
    I('other_tag_3', IN_UCR),
    I('tag_4', IN_UCR, IN_FOOD_FIXTURE),
    I('other_tag_4', IN_UCR),
    I('tag_5', IN_UCR, IN_FOOD_FIXTURE),
    I('other_tag_5', IN_UCR),
    I('tag_6', IN_UCR, IN_FOOD_FIXTURE),
    I('other_tag_6', IN_UCR),
    I('tag_7', IN_UCR, IN_FOOD_FIXTURE),
    I('other_tag_7', IN_UCR),
    I('tag_8', IN_UCR, IN_FOOD_FIXTURE),
    I('other_tag_8', IN_UCR),
    I('tag_9', IN_UCR, IN_FOOD_FIXTURE),
    I('other_tag_9', IN_UCR),
    I('tag_10', IN_UCR, IN_FOOD_FIXTURE),
    I('other_tag_10', IN_UCR),
    I('conv_method_code', IN_UCR),
    I('conv_method_desc', IN_UCR),
    I('conv_option_code', IN_UCR),
    I('conv_option_desc', IN_UCR),
    I('measurement_amount', IN_UCR),
    I('conv_units', IN_UCR),
    I('portions', IN_UCR),
    I('nsr_conv_method_code_post_cooking', IN_UCR),
    I('nsr_conv_method_desc_post_cooking'),
    I('nsr_conv_option_code_post_cooking', IN_UCR),
    I('nsr_conv_option_desc_post_cooking', IN_UCR),
    I('nsr_measurement_amount_post_cooking', IN_UCR),
    I('nsr_consumed_cooked_fraction'),
    I('recipe_num_ingredients'),
    I('conv_factor_food_code'),
    I('conv_factor_base_term_food_code'),
    I('conv_factor_used'),
    I('conv_factor'),
    I('fct_food_code_exists'),
    I('fct_base_term_food_code_exists'),
    I('fct_reference_food_code_exists'),
    I('fct_data_used'),
    I('fct_code'),
    I('total_grams'),
    I('energy_kcal_per_100g'),
    I('energy_kcal'),
    I('water_G_per_100g'),
    I('water_g'),
    I('protein_g_per_100g'),
    I('protein_g'),
    I('conv_factor_gap_code'),
    I('conv_factor_gap_desc'),
    I('fct_gap_code'),
    I('fct_gap_desc'),
]


class FoodRow:
    location_id = 'report'
    age_range = ''
    caseid = ''  # should just return doc_id
    # base_term_food_code = ''
    # fao_who_gift_food_group_code = ''
    # fao_who_gift_food_group_description = ''
    # user_food_group = ''
    # already_reported_recipe = ''
    # already_reported_recipe_case_id = ''
    # already_reported_recipe_name = ''
    # ingr_fraction = ''
    # ingr_recipe_total_grams_consumed = ''
    # nsr_conv_method_desc_post_cooking = ''  # TODO this one should be added to the UCR
    # nsr_consumed_cooked_fraction = ''  # TODO this one should be added to the UCR
    # recipe_num_ingredients = ''
    # conv_factor_food_code = ''
    # conv_factor_base_term_food_code = ''
    # conv_factor_used = ''
    # conv_factor = ''
    # fct_food_code_exists = ''
    # fct_base_term_food_code_exists = ''
    # fct_reference_food_code_exists = ''
    # fct_data_used = ''
    # fct_code = ''
    # total_grams = ''
    # energy_kcal_per_100g = ''
    # energy_kcal = ''
    # water_G_per_100g = ''
    # water_g = ''
    # protein_g_per_100g = ''
    # protein_g = ''
    # conv_factor_gap_code = ''
    # conv_factor_gap_desc = ''
    # fct_gap_code = ''
    # fct_gap_desc = ''

    def __init__(self, ucr_row):
        self.ucr_row = ucr_row
        for indicator in INDICATORS:
            if indicator.in_ucr and self._include_ucr_indicator(indicator):
                setattr(self, indicator.slug, ucr_row[indicator.slug])
            else:
                setattr(self, indicator.slug, MISSING)

    def _include_ucr_indicator(self, indicator):
        return indicator.is_recall_meta

    def as_list(self):
        return [getattr(self, column.slug) for column in INDICATORS]


class FoodCaseRow(FoodRow):
    """A food item directly corresponding to a case in the UCR"""

    def _include_ucr_indicator(self, indicator):
        return True


class RecipeIngredientRow(FoodRow):
    """A food item inferred from a recipe"""

    def __init__(self, ucr_row, food_data, ingredient):
        # ucr_row is data from the parent food case
        # food_data is static info from the fixture,
        # ingredient is static info for this ingredient
        super().__init__(ucr_row)
        self.ingredient = ingredient
        self.food_code = ingredient.ingr_code
        for indicator in INDICATORS:
            if indicator.in_food_fixture:
                setattr(self, indicator.slug, getattr(food_data, indicator.slug))


class FoodData:
    def __init__(self, domain, ucr_rows):
        self.ucr_rows = ucr_rows
        self.fixtures = FixtureAccessor(domain)

    @property
    def headers(self):
        return [i.slug for i in INDICATORS]

    @property
    def rows(self):
        for ucr_row in self.ucr_rows:
            food = FoodCaseRow(ucr_row)
            yield food.as_list()
            if food.food_type == 'std_recipe':
                for ingredient_data in self.fixtures.recipes[food.food_code]:
                    food_data = self.fixtures.foods[ingredient_data.ingr_code]
                    ingr_row = RecipeIngredientRow(ucr_row, food_data, ingredient_data)
                    yield ingr_row.as_list()
