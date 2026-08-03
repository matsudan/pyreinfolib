from enum import StrEnum, unique


@unique
class PriceClassification(StrEnum):
    """Price classification for the real estate price endpoints, XIT001 and XPT001.

    Leaving the argument unset asks for both.
    """

    REAL_ESTATE_TRANSACTION_PRICE = "01"
    """不動産取引価格情報"""

    CONTRACT_PRICE = "02"
    """成約価格情報"""


@unique
class LandPriceClassification(StrEnum):
    """Land price classification for the land price endpoint, XPT002.

    A separate code table from `PriceClassification`, numbered from `0` rather than `01`, so
    the two are not interchangeable even though the API spells both `priceClassification`.
    Leaving the argument unset asks for both.

    MLIT distinguishes the two by 公示 and 調査: the first is a publication, the second is
    research. Rendering both as "publication" would leave the members nearly identical.
    """

    LAND_MARKET_VALUE_PUBLICATION = "0"
    """地価公示"""

    PREFECTURAL_LAND_MARKET_VALUE_RESEARCH = "1"
    """都道府県地価調査"""


@unique
class UseDivision(StrEnum):
    """Use division for the appraisal report and land price endpoints, XCT001 and XPT002.

    XCT001 takes one, XPT002 takes any number of them.
    """

    RESIDENTIAL_LAND = "00"
    """住宅地"""

    BUILDING_SITE_WITH_AN_INTERIM_USE = "03"
    """宅地見込地"""

    COMMERCIAL_LAND = "05"
    """商業地"""

    QUASI_INDUSTRIAL_LAND = "07"
    """準工業地"""

    INDUSTRIAL_LAND = "09"
    """工業地"""

    BUILDING_SITE_WITHIN_URBANIZATION_CONTROL_AREA = "10"
    """調整区域内宅地"""

    CURRENT_FOREST_LAND = "13"
    """現況林地"""

    FOREST_LAND = "20"
    """林地（都道府県地価調査）"""


@unique
class LandTypeCode(StrEnum):
    """Land type for the real estate price point endpoint, XPT001."""

    LAND = "01"
    """宅地(土地)"""

    LAND_AND_BUILDING = "02"
    """宅地(土地と建物)"""

    PRE_OWNED_CONDOMINIUMS_ETC = "07"
    """中古マンション等"""

    AGRICULTURAL_LAND = "10"
    """農地"""

    FOREST_LAND = "11"
    """林地"""
