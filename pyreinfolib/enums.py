from enum import StrEnum, unique


@unique
class PriceClassification(StrEnum):
    """Price classification for the real estate price endpoints, XIT001 and XPT001.

    Leaving the argument unset asks for both.
    """

    # 不動産取引価格情報
    REAL_ESTATE_TRANSACTION_PRICE = "01"

    # 成約価格情報
    CONTRACT_PRICE = "02"


@unique
class LandPriceClassification(StrEnum):
    """Land price classification for the land price endpoint, XPT002.

    A separate code table from `PriceClassification`, numbered from `0` rather than `01`, so
    the two are not interchangeable even though the API spells both `priceClassification`.
    Leaving the argument unset asks for both.
    """

    # 地価公示
    LAND_PRICE_PUBLIC_NOTICE = "0"

    # 都道府県地価調査
    PREFECTURAL_LAND_PRICE_SURVEY = "1"


@unique
class UseDivision(StrEnum):
    # 住宅地
    RESIDENTIAL_LAND = "00"

    # 宅地見込地
    BUILDING_SITE_WITH_AN_INTERIM_USE = "03"

    # 商業地
    COMMERCIAL_LAND = "05"

    # 準工業地
    QUASI_INDUSTRIAL_LAND = "07"

    # 工業地
    INDUSTRIAL_LAND = "09"

    # 調整区域内宅地
    BUILDING_SITE_WITHIN_URBANIZATION_CONTROL_AREA = "10"

    # 現況林地
    CURRENT_FOREST_LAND = "13"

    # 林地（都道府県地価調査）
    FOREST_LAND = "20"


@unique
class LandTypeCode(StrEnum):
    # 宅地(土地)
    LAND = "01"

    # 宅地(土地と建物)
    LAND_AND_BUILDING = "02"

    # 中古マンション等
    PRE_OWNED_CONDOMINIUMS_ETC = "07"

    # 農地
    AGRICULTURAL_LAND = "10"

    # 林地
    FOREST_LAND = "11"
