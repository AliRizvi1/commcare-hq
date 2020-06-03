from collections import namedtuple

FOOD_CONSUMPTION = 'food_consumption_indicators'

AgeRange = namedtuple("AgeRange", "name slug column lower_bound upper_bound")
# note: these slugs are intended for internal use only (you can change them)
AGE_RANGES = [
    AgeRange("0-5.9 months", 'lt6months', 'age_months_calculated', 0, 6),
    AgeRange("06-59 months", 'lt60months', 'age_months_calculated', 6, 60),
    AgeRange("5-6 years", 'lt7years', 'age_years_calculated', 5, 7),
    AgeRange("7-10 years", 'lt11years', 'age_years_calculated', 7, 11),
    AgeRange("11-14 years", 'lt15years', 'age_years_calculated', 11, 15),
    AgeRange("15-49 years", 'lt50years', 'age_years_calculated', 15, 50),
    AgeRange("50-64 years", 'lt65years', 'age_years_calculated', 0, 65),
    AgeRange("65+ years", 'gte65years', 'age_years_calculated', 65, 200),
]

FOOD_ITEM = 'food_item'
NON_STANDARD_FOOD_ITEM = 'non_std_food_item'
STANDARD_RECIPE = 'std_recipe'
NON_STANDARD_RECIPE = 'non_std_recipe'


class FctGaps:
    slug = 'fct'
    name = "Food Composition Table"
    AVAILABLE = 1
    BASE_TERM = 2
    REFERENCE = 3
    INGREDIENT_GAPS = 7
    NOT_AVAILABLE = 8
    DESCRIPTIONS = {
        AVAILABLE: "FCT data available",
        BASE_TERM: "Using FCT data from base term food code",
        REFERENCE: "Using FCT data from reference food code",
        INGREDIENT_GAPS: "Ingredients contain FCT data gaps",
        NOT_AVAILABLE: "No FCT data available",
    }


class ConvFactorGaps:
    slug = 'conv_factor'
    name = "Conversion Factor"
    AVAILABLE = 1
    BASE_TERM = 2
    NOT_AVAILABLE = 8
    DESCRIPTIONS = {
        AVAILABLE: "Conversion Factor available",
        BASE_TERM: "Using Conversion Factor from base term food code",
        NOT_AVAILABLE: "No Conversion Factor available",
    }
