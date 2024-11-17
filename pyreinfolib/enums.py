from enum import StrEnum, unique


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