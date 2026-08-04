"""The shape of the bodies the API returns.

These are `TypedDict`s and nothing more: no member is checked at runtime, and `Client` does not
validate what it decoded. What they buy is that `r["data"][0]` and a feature's `properties` stop
being `Any`, so a misspelled key is a type error rather than a `KeyError` found by whoever runs
the code next.

**Keys are the API's own tag names, verbatim**, so its inconsistencies come with them: 国土数値情報
attribute codes (`A27_001`), romanised Japanese (`kubun_id`), a `_ja` suffix on the fields that
follow the `language` argument, Japanese keys with spaces in XCT001, and one misspelling of the
API's own (`proximity_to_transportation_facilitites` in XPT002). Correcting any of them would name
a key that no response contains.

**Every record field is optional.** Which keys a response carries is undocumented, and two
endpoints do omit some. Reading one still type checks, so this costs nothing to use. Nothing is
annotated `| None` either.

**A field the manual declares 実数型 arrives as `int` when its value is whole**, JSON having one
number type. It is annotated `float` anyway, which is what arithmetic wants, but it does mean
`isinstance(value, float)` can be `False`, and that a float-only call such as `.hex()` is reported
by some type checkers and not others.

CONTRIBUTING.md has the rules these types follow, and what has been checked against a live
response.
"""

from typing import Any, Generic, Literal, NotRequired, TypedDict, TypeVar

# GeoJSON, as the tile endpoints return it when asked for `response_format=geojson`.
#
# A position is `[longitude, latitude]`, optionally with an altitude. `list` rather than a
# tuple because that is what `json` produces, and `float` covers the integers a decoder may
# hand back for a whole-numbered coordinate.
Position = list[float]


class Point(TypedDict):
    type: Literal["Point"]
    coordinates: Position


class MultiPoint(TypedDict):
    type: Literal["MultiPoint"]
    coordinates: list[Position]


class LineString(TypedDict):
    type: Literal["LineString"]
    coordinates: list[Position]


class MultiLineString(TypedDict):
    type: Literal["MultiLineString"]
    coordinates: list[list[Position]]


class Polygon(TypedDict):
    type: Literal["Polygon"]
    coordinates: list[list[Position]]


class MultiPolygon(TypedDict):
    type: Literal["MultiPolygon"]
    coordinates: list[list[list[Position]]]


# A union rather than one type per endpoint, because a single tile can carry more than one
# shape: several endpoints mix Polygon with MultiPolygon, and XKT029 answers with Polygon,
# MultiPolygon and LineString together. The manual's output tables say nothing about geometry.
#
# The shape is not always the one the subject suggests either. XKT015, 駅別乗降客数, answers
# with LineStrings, because a station is drawn as its platform line rather than as a point.
#
# Narrow on `type` to read `coordinates`; the tag is what makes that possible.
Geometry = Point | MultiPoint | LineString | MultiLineString | Polygon | MultiPolygon


class CoordinateReferenceSystem(TypedDict):
    """The `crs` member of a feature collection, in the form GeoJSON used before RFC 7946.

    **Worth reading rather than assuming.** The API does not put every endpoint on one datum.
    Most name EPSG:6668, which is JGD2011, but XKT017 (図書館) and XKT019 (自然公園地域) name
    EPSG:4612, which is JGD2000. Coordinates from those two do not line up exactly with the
    rest, and the gap is widest in Tohoku, where the 2011 earthquake moved the ground between
    the two realisations.
    """

    type: Literal["name"]
    properties: dict[str, str]


class TileProperties(TypedDict, total=False):
    """Two keys every tile endpoint's `properties` may carry, neither of them documented.

    `_id` and `_index` are Elasticsearch document metadata showing through, and they lead the
    key order. Every tile endpoint sends both except XPT001, which sends neither. Nothing in
    the manual mentions them, so they are not a field to build on.
    """

    _id: str
    _index: str


P = TypeVar("P")


class Feature(TypedDict, Generic[P]):
    """One GeoJSON feature. `P` is the endpoint's properties type.

    `geometry` is `| None` because GeoJSON allows a null geometry.
    """

    type: Literal["Feature"]
    geometry: Geometry | None
    properties: P


class FeatureCollection(TypedDict, Generic[P]):
    """What a tile endpoint returns. Empty `features` is the normal answer for an empty tile.

    Endpoints addressed by tile coordinates answer 200 with no features rather than 404, so
    this arrives rather than `NoResultsError` whenever a tile holds nothing.

    `name` and `crs` are not in the manual and are not required by GeoJSON, hence optional, but
    every tile endpoint sends both. `name` names the source layers, and its type is not
    consistent: most send a string, XKT001 comma joins the two layers it merges into one string
    as `'urban_plan_area, area_classification'`, and XPT001 sends a list.

    `crs` is worth reading; see `CoordinateReferenceSystem` for why.
    """

    type: Literal["FeatureCollection"]
    features: list[Feature[P]]
    name: NotRequired[str | list[str]]
    crs: NotRequired[CoordinateReferenceSystem]


T = TypeVar("T")


class DataResponse(TypedDict, Generic[T]):
    """What the three endpoints that do not take tile coordinates return.

    Unlike everything below, this envelope is not in the manual: its output tables describe one
    record and stop. The two keys are what the API sends.

    `status` is a `str` rather than a `Literal["OK"]`, the full set of values it can take being
    unknown. An error status does not arrive here in any case, a non-2xx response raising.
    """

    status: str
    data: list[T]


# XKT013 is the one endpoint whose keys are not written down. All but `MESH_ID` and `SHICODE`
# are named after the year they hold, and the manual writes that year as a placeholder:
# `PT01_20XX`, `RTA_20XX`, `HITOKU20XX`.
#
# Which years arrive is not a clean product of the field prefixes and a fixed set of years, and
# it follows whichever projection is published, so a `TypedDict` would go wrong on the next
# release and reading a key that does exist would then be an error. An open mapping is the
# honest type; the feature collection around it is still precise.
PopulationProjectionsIn250mGridSquaresProperties = dict[str, Any]
PopulationProjectionsIn250mGridSquaresResponse = FeatureCollection[PopulationProjectionsIn250mGridSquaresProperties]


class RealEstatePricesItem(TypedDict, total=False):
    """One record of `data` from XIT001, 不動産価格（取引価格・成約価格）情報取得API.

    See https://www.reinfolib.mlit.go.jp/help/apiManual/xit001/
    """

    Type: str  # 取引の種類
    Region: str  # 地域
    MunicipalityCode: str  # 市区町村コード
    Prefecture: str  # 都道府県名
    Municipality: str  # 市区町村名
    DistrictName: str  # 地区名
    TradePrice: str  # 取引価格（総額）
    PricePerUnit: str  # 坪単価
    FloorPlan: str  # 間取り
    Area: str  # 面積（平方メートル）
    UnitPrice: str  # 取引価格（平方メートル単価）
    LandShape: str  # 土地の形状
    Frontage: str  # 間口
    TotalFloorArea: str  # 延床面積（平方メートル）
    BuildingYear: str  # 建築年
    Structure: str  # 建物の構造
    Use: str  # 用途
    Purpose: str  # 今後の利用目的
    Direction: str  # 前面道路：方位
    Classification: str  # 前面道路：種類
    Breadth: str  # 前面道路：幅員（m）
    CityPlanning: str  # 都市計画
    CoverageRatio: str  # 建蔽率（%）
    FloorAreaRatio: str  # 容積率（%）
    Period: str  # 取引時点
    Renovation: str  # 改装
    Remarks: str  # 取引の事情等
    PriceCategory: str  # 価格情報区分
    DistrictCode: str  # 地区コード


RealEstatePricesResponse = DataResponse[RealEstatePricesItem]


class MunicipalitiesItem(TypedDict, total=False):
    """One record of `data` from XIT002, 都道府県内市区町村一覧取得API.

    See https://www.reinfolib.mlit.go.jp/help/apiManual/xit002/
    """

    id: str  # 市区町村コード
    # The manual lists `name` twice, once as 市区町村名（日本語） and once as
    # 市区町村名（英語）. It is one key either way; which language it holds follows the
    # `language` argument.
    name: str  # 市区町村名


MunicipalitiesResponse = DataResponse[MunicipalitiesItem]


# One record of `data` from XCT001, 鑑定評価書情報API.
#
# Written with the functional syntax because the keys are not identifiers: this endpoint names
# its fields in Japanese, and all but 13 of them contain a space separating the levels of the
# source spreadsheet's column headings.
#
# **These are the keys the response carries, not the ones the manual prints.** The manual's
# output table renders every separator as U+3000 where the response uses a plain U+0020, and six
# names differ by more than whitespace: it writes 用途区分コード and 構造コード for what arrive as
# 用途区分 and 構造, 建蔽率 for 建ぺい率, and 緯度 and 経度 for 位置座標 緯度 and 位置座標 経度.
# A key copied out of the manual will not be found here, or in a response.
#
# See https://www.reinfolib.mlit.go.jp/help/apiManual/xct001/
AppraisalReportsItem = TypedDict(
    "AppraisalReportsItem",
    {
        "価格時点": str,
        "標準地番号 市区町村コード 県コード": str,
        "標準地番号 市区町村コード 市区町村コード": str,
        "標準地番号 地域名": str,
        "標準地番号 用途区分": str,
        "標準地番号 連番": str,
        "1㎡当たりの価格": str,
        "路線価 年": str,
        "路線価 相続税路線価": str,
        "路線価 倍率": str,
        "路線価 倍率種別": str,
        "標準地 所在地 所在地番": str,
        "標準地 所在地 住居表示": str,
        "標準地 所在地 仮換地番号": str,
        "標準地 地積 地積": str,
        "標準地 地積 内私道分": str,
        "標準地 形状 形状": str,
        "標準地 形状 形状比 間口": str,
        "標準地 形状 形状比 奥行": str,
        "標準地 形状 方位": str,
        "標準地 形状 平坦": str,
        "標準地 形状 傾斜度": str,
        "標準地 土地利用の現況 現況": str,
        "標準地 土地利用の現況 構造": str,
        "標準地 土地利用の現況 地上階数": str,
        "標準地 土地利用の現況 地下階数": str,
        "標準地 周辺の利用状況": str,
        "標準地 接面道路の状況 前面道路 方位": str,
        "標準地 接面道路の状況 前面道路 駅前区分": str,
        "標準地 接面道路の状況 前面道路 高低位置": str,
        "標準地 接面道路の状況 前面道路 道路幅員": str,
        "標準地 接面道路の状況 前面道路 舗装状況": str,
        "標準地 接面道路の状況 前面道路 道路種別": str,
        "標準地 接面道路の状況 側道方位": str,
        "標準地 接面道路の状況 側道等接面状況": str,
        "標準地 供給処理施設 水道": str,
        "標準地 供給処理施設 ガス": str,
        "標準地 供給処理施設 下水道": str,
        "標準地 交通施設の状況 交通施設": str,
        "標準地 交通施設の状況 距離": str,
        "標準地 交通施設の状況 近接区分": str,
        "標準地 法令上の規制等 区域区分": str,
        "標準地 法令上の規制等 用途地域": str,
        "標準地 法令上の規制等 指定建ぺい率": str,
        "標準地 法令上の規制等 指定容積率": str,
        "標準地 法令上の規制等 防火地域": str,
        "標準地 法令上の規制等 森林法": str,
        "標準地 法令上の規制等 自然公園法": str,
        "標準地 法令上の規制等 その他 その他地域地区等1": str,
        "標準地 法令上の規制等 その他 その他地域地区等2": str,
        "標準地 法令上の規制等 その他 その他地域地区等3": str,
        "標準地 法令上の規制等 その他 高度地区1 種": str,
        "標準地 法令上の規制等 その他 高度地区1 高度区分": str,
        "標準地 法令上の規制等 その他 高度地区1 高度": str,
        "標準地 法令上の規制等 その他 高度地区2 種": str,
        "標準地 法令上の規制等 その他 高度地区2 高度区分": str,
        "標準地 法令上の規制等 その他 高度地区2 高度": str,
        "標準地 法令上の規制等 その他 基準建ぺい率": str,
        "標準地 法令上の規制等 その他 基準容積率": str,
        "標準地 法令上の規制等 自然環境等コード1": str,
        "標準地 法令上の規制等 自然環境等コード2": str,
        "標準地 法令上の規制等 自然環境等コード3": str,
        "標準地 法令上の規制等 自然環境等文言": str,
        "鑑定評価手法の適用 取引事例比較法比準価格": str,
        "鑑定評価手法の適用 控除法 控除後価格": str,
        "鑑定評価手法の適用 収益還元法 収益価格": str,
        "鑑定評価手法の適用 原価法 積算価格": str,
        "鑑定評価手法の適用 開発法 開発法による価格": str,
        "比準価格算定内訳事例a 取引価格": str,
        "比準価格算定内訳事例a 推定価格": str,
        "比準価格算定内訳事例a 標準価格": str,
        "比準価格算定内訳事例a 査定価格": str,
        "比準価格算定内訳事例b 取引価格": str,
        "比準価格算定内訳事例b 推定価格": str,
        "比準価格算定内訳事例b 標準価格": str,
        "比準価格算定内訳事例b 査定価格": str,
        "比準価格算定内訳事例c 取引価格": str,
        "比準価格算定内訳事例c 推定価格": str,
        "比準価格算定内訳事例c 標準価格": str,
        "比準価格算定内訳事例c 査定価格": str,
        "比準価格算定内訳事例d 取引価格": str,
        "比準価格算定内訳事例d 推定価格": str,
        "比準価格算定内訳事例d 標準価格": str,
        "比準価格算定内訳事例d 査定価格": str,
        "比準価格算定内訳事例e 取引価格": str,
        "比準価格算定内訳事例e 推定価格": str,
        "比準価格算定内訳事例e 標準価格": str,
        "比準価格算定内訳事例e 査定価格": str,
        "積算価格算定内訳素地の取得価格": str,
        "積算価格算定内訳造成工事費": str,
        "積算価格算定内訳再調達原価": str,
        "収益価格算定内訳総収益": str,
        "収益価格算定内訳総費用": str,
        "収益価格算定内訳純収益": str,
        "収益価格算定内訳建物に帰属する純収益": str,
        "収益価格算定内訳土地に帰属する純収益": str,
        "収益価格算定内訳未収入期間修正後の純収益": str,
        "収益価格算定内訳還元利回り": str,
        "開発法価格算定内訳 収入の現価の総和": str,
        "開発法価格算定内訳 支出の現価の総和": str,
        "開発法価格算定内訳 投下資本収益率": str,
        "開発法価格算定内訳 販売単価(住宅)": str,
        "開発法価格算定内訳 分譲可能床面積": str,
        "開発法価格算定内訳 建築工事費": str,
        "開発法価格算定内訳 延床面積": str,
        "公示価格": str,
        "変動率": str,
        "位置座標 緯度": str,
        "位置座標 経度": str,
    },
    total=False,
)

AppraisalReportsResponse = DataResponse[AppraisalReportsItem]


class RealEstatePricesPointProperties(TileProperties, total=False):
    """One feature's `properties` from XPT001, 不動産価格（取引価格・成約価格）情報のポイント (点) API.

    See https://www.reinfolib.mlit.go.jp/help/apiManual/xpt001/
    """

    price_information_category_name_ja: str  # 価格情報区分
    district_code: str  # 地区コード
    city_code: str  # 市区町村コード
    prefecture_name_ja: str  # 都道府県名
    city_name_ja: str  # 市区町村名
    district_name_ja: str  # 地区名
    u_transaction_price_total_ja: str  # 取引価格（総額）
    u_unit_price_per_tsubo_ja: str  # 坪単価
    floor_plan_name_ja: str  # 間取り
    u_area_ja: str  # 面積
    u_transaction_price_unit_price_square_meter_ja: str  # 取引価格（平方メートル単価）
    land_shape_name_ja: str  # 土地の形状
    u_land_frontage_ja: str  # 間口
    u_building_total_floor_area_ja: str  # 建物の延床面積
    u_construction_year_ja: str  # 建築年
    building_structure_name_ja: str  # 建物の構造
    land_use_name_ja: str  # 用途地域
    future_use_purpose_name_ja: str  # 今後の利用目的
    front_road_azimuth_name_ja: str  # 前面道路の方位
    front_road_type_name_ja: str  # 前面道路の種類
    u_front_road_width_ja: str  # 前面道路の幅員
    u_building_coverage_ratio_ja: str  # 建蔽率
    u_floor_area_ratio_ja: str  # 容積率
    point_in_time_name_ja: str  # 取引時点
    remark_renovation_name_ja: str  # 改装
    remark_name_ja: str  # 取引の事情等
    land_type_name_ja: str  # 取引の種類
    use_category_name_ja: str  # 地域
    building_use_name_ja: str  # 用途


RealEstatePricesPointResponse = FeatureCollection[RealEstatePricesPointProperties]


class LandMarketValuePublicationAndResearchPointProperties(TileProperties, total=False):
    """One feature's `properties` from XPT002, 地価公示・地価調査のポイント (点) API.

    See https://www.reinfolib.mlit.go.jp/help/apiManual/xpt002/
    """

    point_id: int  # 地点ID
    target_year_name_ja: str  # 対象年
    land_price_type: int  # 地価区分
    prefecture_code: str  # 都道府県コード
    prefecture_name_ja: str  # 都道府県名
    city_code: str  # 市区町村コード
    use_category_name_ja: str  # 用途区分名
    standard_lot_number_ja: str  # 標準地/基準地番号
    city_county_name_ja: str  # 市郡名
    ward_town_village_name_ja: str  # 区町村名
    place_name_ja: str  # 地名
    residence_display_name_ja: str  # 住居表示
    location_number_ja: str  # 所在及び地番
    u_current_years_price_ja: str  # 当年価格
    last_years_price: int  # 前年価格
    year_on_year_change_rate: str  # 対前年変動率
    u_cadastral_ja: str  # 地積
    frontage_ratio: int  # 間口比率
    depth_ratio: int  # 奥行き比率
    building_structure_name_ja: str  # 構造
    u_ground_hierarchy_ja: str  # 地上階層
    u_underground_hierarchy_ja: str  # 地下階層
    front_road_name_ja: str  # 前面道路区分
    front_road_azimuth_name_ja: str  # 前面道路の方位区分
    front_road_width: int  # 前面道路の幅員
    front_road_pavement_condition: str  # 前面道路の舗装状況
    side_road_azimuth_name_ja: str  # 側道の方位区分
    side_road_name_ja: str  # 側道区分
    gas_supply_availability: bool  # ガスの有無
    water_supply_availability: bool  # 水道の有無
    sewer_supply_availability: bool  # 下水道の有無
    nearest_station_name_ja: str  # 最寄り駅名
    # `facilitites` is the API's spelling, not a typo introduced here: it carries an extra `t`
    # where the word is `facilities`.
    proximity_to_transportation_facilitites: int  # 交通施設との近接区分
    u_road_distance_to_nearest_station_name_ja: str  # 最寄り駅までの道路距離
    usage_status_name_ja: str  # 利用現況
    current_usage_status_of_surrounding_land_name_ja: str  # 周辺の土地の利用現況
    area_division_name_ja: str  # 区域区分
    regulations_use_category_name_ja: str  # 法規制・用途区分
    regulations_altitude_district_name_ja: str  # 法規制・高度地区
    regulations_fireproof_name_ja: str  # 法規制・防火・準防火
    u_regulations_building_coverage_ratio_ja: str  # 法規制・建蔽率
    u_regulations_floor_area_ratio_ja: str  # 法規制・容積率
    regulations_forest_law_name_ja: str  # 法規制・森林法
    regulations_park_law_name_ja: str  # 法規制・公園法
    pause_flag: int  # 休止フラグ
    usage_category_name_ja: str  # 利用区分名
    location: str  # 所在及び地番
    shape: str  # 形状（間口：奥行き）
    front_road_condition: str  # 前面道路の状況
    side_road_condition: str  # その他の接面道路
    park_forest_law: str  # 森林法、公園法、自然環境等


LandMarketValuePublicationAndResearchPointResponse = FeatureCollection[
    LandMarketValuePublicationAndResearchPointProperties
]


class CityPlanningAreasAndAreaClassificationProperties(TileProperties, total=False):
    """One feature's `properties` from XKT001, 都市計画決定GISデータ（都市計画区域/区域区分）API.

    See https://www.reinfolib.mlit.go.jp/help/apiManual/xkt001/
    """

    prefecture: str  # 都道府県名
    city_code: str  # 市区町村コード
    city_name: str  # 市区町村名
    kubun_id: int  # 区分コード
    decision_date: str  # 設定年月日
    decision_classification: str  # 設定区分
    decision_maker: str  # 設定者名
    notice_number: str  # 告示番号
    area_classification_ja: str  # 区域区分
    first_decision_date: str  # 当初決定日
    notice_number_s: str  # 告示番号S


CityPlanningAreasAndAreaClassificationResponse = FeatureCollection[CityPlanningAreasAndAreaClassificationProperties]


class UseDistrictsProperties(TileProperties, total=False):
    """One feature's `properties` from XKT002, 都市計画決定GISデータ（用途地域）API.

    See https://www.reinfolib.mlit.go.jp/help/apiManual/xkt002/
    """

    youto_id: int  # 用途地域分類
    prefecture: str  # 都道府県名
    city_code: str  # 市区町村コード
    city_name: str  # 市区町村名
    decision_date: str  # 区域設定年月日
    decision_classification: str  # 設定区分
    decision_maker: str  # 設定者名
    notice_number: str  # 告示番号
    use_area_ja: str  # 用途地域名
    u_floor_area_ratio_ja: str  # 容積率
    u_building_coverage_ratio_ja: str  # 建蔽率
    first_decision_date: str  # 当初決定日
    notice_number_s: str  # 告示番号S


UseDistrictsResponse = FeatureCollection[UseDistrictsProperties]


class LocationNormalizationPlansProperties(TileProperties, total=False):
    """One feature's `properties` from XKT003, 都市計画決定GISデータ（立地適正化計画）API.

    See https://www.reinfolib.mlit.go.jp/help/apiManual/xkt003/
    """

    prefecture: str  # 都道府県名
    city_code: str  # 行政区域コード
    city_name: str  # 市区町村名
    decision_date: str  # 区域設定年月日
    decision_classification: str  # 設定区分
    decision_maker: str  # 設定者名
    notice_number: str  # 告示番号
    kubun_id: int  # 区域コード
    kubun_name_ja: str  # 区域名
    area_classification_ja: str  # 区域区分
    first_decision_date: str  # 当初決定日
    notice_number_s: str  # 告示番号S


LocationNormalizationPlansResponse = FeatureCollection[LocationNormalizationPlansProperties]


class ElementarySchoolDistrictsProperties(TileProperties, total=False):
    """One feature's `properties` from XKT004, 国土数値情報（小学校区）API.

    See https://www.reinfolib.mlit.go.jp/help/apiManual/xkt004/
    """

    A27_001: str  # 行政区域コード
    A27_002: str  # 設置主体
    A27_003: str  # 学校コード
    A27_004_ja: str  # 名称
    A27_005: str  # 所在地


ElementarySchoolDistrictsResponse = FeatureCollection[ElementarySchoolDistrictsProperties]


class JuniorHighSchoolDistrictsProperties(TileProperties, total=False):
    """One feature's `properties` from XKT005, 国土数値情報（中学校区）API.

    See https://www.reinfolib.mlit.go.jp/help/apiManual/xkt005/
    """

    A32_001: str  # 行政区域コード
    A32_002: str  # 設置主体
    A32_003: str  # 学校コード
    A32_004_ja: str  # 名称
    A32_005: str  # 所在地


JuniorHighSchoolDistrictsResponse = FeatureCollection[JuniorHighSchoolDistrictsProperties]


class SchoolsProperties(TileProperties, total=False):
    """One feature's `properties` from XKT006, 国土数値情報（学校）API.

    See https://www.reinfolib.mlit.go.jp/help/apiManual/xkt006/
    """

    P29_001: str  # 行政区域コード
    P29_002: str  # 学校コード
    P29_003: int  # 学校分類コード
    P29_003_name_ja: str  # 学校分類名
    P29_004_ja: str  # 名称
    P29_005_ja: str  # 所在地
    P29_006: int  # 管理者コード
    P29_007: int  # 休校区分
    P29_008: str  # キャンパスコード
    P29_009_ja: str  # 学校名備考


SchoolsResponse = FeatureCollection[SchoolsProperties]


class NurserySchoolsAndKindergartensEtcProperties(TileProperties, total=False):
    """One feature's `properties` from XKT007, 国土数値情報（保育園・幼稚園等）API.

    The dataset is built by merging 国土数値情報「学校」 and 「福祉施設」, and the manual documents one
    output table per side, 幼稚園 and こども園 against 保育園. One type covers both: most keys of
    both sides arrive on either, blank rather than absent. Only `schoolClassCode`,
    `schoolClassCode_name_ja` and `closeSchoolCode` are confined to the 幼稚園 side.

    **Tell the two apart by a value, not by a key.** `welfareFacilityClassCode` arrives on every
    feature: `05` on the 保育園 side, blank on the other.

    See https://www.reinfolib.mlit.go.jp/help/apiManual/xkt007/
    """

    # Common to both shapes.
    administrativeAreaCode: str  # 行政区域コード
    preSchoolName_ja: str  # 名称
    location_ja: str  # 所在地
    administratorCode: int  # 管理者コード

    # From the 学校 side. `schoolCode` arrives on either, blank on the 保育園 side; the other
    # three are absent there.
    schoolCode: str  # 学校コード
    schoolClassCode: int  # 学校分類コード
    schoolClassCode_name_ja: str  # 学校分類名
    closeSchoolCode: int  # 休校コード

    # From the 福祉施設 side, blank on the 幼稚園 side. The same three-level classification
    # `get_welfare_facilities` filters on.
    welfareFacilityClassCode: str  # 福祉施設大分類コード
    welfareFacilityMiddleClassCode: str  # 福祉施設中分類コード
    welfareFacilityMinorClassCode: str  # 福祉施設小分類コード


NurserySchoolsAndKindergartensEtcResponse = FeatureCollection[NurserySchoolsAndKindergartensEtcProperties]


class MedicalInstitutionsProperties(TileProperties, total=False):
    """One feature's `properties` from XKT010, 国土数値情報（医療機関）API.

    See https://www.reinfolib.mlit.go.jp/help/apiManual/xkt010/
    """

    P04_001: int  # 医療機関分類
    P04_001_name_ja: str  # 医療機関分類名
    P04_002_ja: str  # 施設名称
    P04_003_ja: str  # 所在地
    P04_004: str  # 診療科目１
    P04_005: str  # 診療科目２
    P04_006: str  # 診療科目３
    P04_007: int  # 開設者分類
    P04_008: int  # 病床数
    P04_009: int  # 救急告示病院
    P04_010: int  # 災害拠点病院
    medical_subject_ja: str  # 診療科目


MedicalInstitutionsResponse = FeatureCollection[MedicalInstitutionsProperties]


class WelfareFacilitiesProperties(TileProperties, total=False):
    """One feature's `properties` from XKT011, 国土数値情報（福祉施設）API.

    See https://www.reinfolib.mlit.go.jp/help/apiManual/xkt011/
    """

    P14_001: str  # 都道府県名
    P14_002: str  # 市区町村名
    P14_003: str  # 行政区域コード
    P14_004_ja: str  # 所在地
    P14_005: str  # 福祉施設大分類コード
    P14_005_name_ja: str  # 福祉施設大分類名
    P14_006: str  # 福祉施設中分類コード
    P14_006_name_ja: str  # 福祉施設中分類名
    P14_007: str  # 福祉施設小分類コード
    P14_008_ja: str  # 名称
    P14_009: int  # 管理者コード
    P14_010: int  # 位置正確度コード


WelfareFacilitiesResponse = FeatureCollection[WelfareFacilitiesProperties]


class FirePreventionDistrictsAndQuasiFirePreventionDistrictsProperties(TileProperties, total=False):
    """One feature's `properties` from XKT014, 都市計画決定GISデータ（防火・準防火地域）API.

    See https://www.reinfolib.mlit.go.jp/help/apiManual/xkt014/
    """

    fire_prevention_ja: str  # 防火・準防火地域名
    kubun_id: int  # 区分コード
    prefecture: str  # 都道府県名
    city_code: str  # 市区町村コード
    city_name: str  # 市区町村名
    decision_date: str  # 設定年月日
    decision_classification: str  # 設定区分
    decision_maker: str  # 設定者名
    notice_number: str  # 告示番号
    first_decision_date: str  # 当初決定日
    notice_number_s: str  # 告示番号S


FirePreventionDistrictsAndQuasiFirePreventionDistrictsResponse = FeatureCollection[
    FirePreventionDistrictsAndQuasiFirePreventionDistrictsProperties
]


class NumberOfPassengersPerStationProperties(TileProperties, total=False):
    """One feature's `properties` from XKT015, 国土数値情報（駅別乗降客数）API.

    See https://www.reinfolib.mlit.go.jp/help/apiManual/xkt015/
    """

    S12_001_ja: str  # 駅名
    S12_001c: str  # 駅コード
    S12_001g: str  # グループコード
    S12_002_ja: str  # 運営会社
    S12_003_ja: str  # 路線名
    S12_004: str  # 鉄道区分
    S12_005: str  # 事業者種別
    S12_006: str  # 重複コード2011
    S12_007: str  # データ有無コード2011
    S12_008: str  # 備考2011
    S12_009: int  # 乗降客数2011
    S12_010: str  # 重複コード2012
    S12_011: str  # データ有無コード2012
    S12_012: str  # 備考2012
    S12_013: int  # 乗降客数2012
    S12_014: str  # 重複コード2013
    S12_015: str  # データ有無コード2013
    S12_016: str  # 備考2013
    S12_017: int  # 乗降客数2013
    S12_018: str  # 重複コード2014
    S12_019: str  # データ有無コード2014
    S12_020: str  # 備考2014
    S12_021: int  # 乗降客数2014
    S12_022: str  # 重複コード2015
    S12_023: str  # データ有無コード2015
    S12_024: str  # 備考2015
    S12_025: int  # 乗降客数2015
    S12_026: str  # 重複コード2016
    S12_027: str  # データ有無コード2016
    S12_028: str  # 備考2016
    S12_029: int  # 乗降客数2016
    S12_030: str  # 重複コード2017
    S12_031: str  # データ有無コード2017
    S12_032: str  # 備考2017
    S12_033: int  # 乗降客数2017
    S12_034: str  # 重複コード2018
    S12_035: str  # データ有無コード2018
    S12_036: str  # 備考2018
    S12_037: int  # 乗降客数2018
    S12_038: str  # 重複コード2019
    S12_039: str  # データ有無コード2019
    S12_040: str  # 備考2019
    S12_041: int  # 乗降客数2019
    S12_042: str  # 重複コード2020
    S12_043: str  # データ有無コード2020
    S12_044: str  # 備考2020
    S12_045: int  # 乗降客数2020
    S12_046: str  # 重複コード2021
    S12_047: str  # データ有無コード2021
    S12_048: str  # 備考2021
    S12_049: int  # 乗降客数2021
    S12_050: str  # 重複コード2022
    S12_051: str  # データ有無コード2022
    S12_052: str  # 備考2022
    S12_053: int  # 乗降客数2022
    S12_054: str  # 重複コード2023
    S12_055: str  # データ有無コード2023
    S12_056: str  # 備考2023
    S12_057: int  # 乗降客数2023


NumberOfPassengersPerStationResponse = FeatureCollection[NumberOfPassengersPerStationProperties]


class DisasterRiskAreasProperties(TileProperties, total=False):
    """One feature's `properties` from XKT016, 国土数値情報（災害危険区域）API.

    See https://www.reinfolib.mlit.go.jp/help/apiManual/xkt016/
    """

    A48_001: str  # 都道府県名
    A48_002: str  # 市町村名
    A48_003: str  # 代表行政コード
    A48_004: int  # 指定主体区分
    A48_005_ja: str  # 区域名
    A48_006: str  # 所在地
    A48_007: int  # 指定理由コード
    A48_007_name_ja: str  # 指定理由
    A48_008_ja: str  # 指定理由詳細
    A48_009: str  # 告示年月日
    A48_010: str  # 告示番号
    A48_011: str  # 根拠条例
    A48_012: float  # 面積
    A48_013: str  # 縮尺
    A48_014: str  # その他


DisasterRiskAreasResponse = FeatureCollection[DisasterRiskAreasProperties]


class LibrariesProperties(TileProperties, total=False):
    """One feature's `properties` from XKT017, 国土数値情報（図書館）API.

    See https://www.reinfolib.mlit.go.jp/help/apiManual/xkt017/
    """

    P27_001: str  # 行政区域コード
    P27_002: str  # 公共施設大分類
    P27_003: str  # 公共施設小分類
    P27_003_name_ja: str  # 公共施設小分類名
    P27_004: str  # 文化施設分類
    P27_004_name_ja: str  # 文化施設分類名
    P27_005_ja: str  # 名称
    P27_006_ja: str  # 所在地
    P27_007: int  # 管理者コード
    P27_008: int  # 階数
    P27_009: int  # 建築年


LibrariesResponse = FeatureCollection[LibrariesProperties]


class MunicipalOfficesAndMeetingFacilitiesEtcProperties(TileProperties, total=False):
    """One feature's `properties` from XKT018, 国土数値情報（市区町村役場及び集会施設等）API.

    See https://www.reinfolib.mlit.go.jp/help/apiManual/xkt018/
    """

    P05_001: str  # 行政区域コード
    P05_002: str  # 施設分類コード
    P05_002_name_ja: str  # 施設分類名
    P05_003_ja: str  # 名称
    P05_004_ja: str  # 所在地


MunicipalOfficesAndMeetingFacilitiesEtcResponse = FeatureCollection[MunicipalOfficesAndMeetingFacilitiesEtcProperties]


class NaturalParkAreasProperties(TileProperties, total=False):
    """One feature's `properties` from XKT019, 国土数値情報（自然公園地域）API.

    See https://www.reinfolib.mlit.go.jp/help/apiManual/xkt019/
    """

    OBJECTID: int  # シェープID
    PREFEC_CD: str  # 都道府県コード
    AREA_CD: str  # 地区コード
    CTV_NAME: str  # 市町村名
    FIS_YEAR: str  # 年度
    THEMA_NO: int  # 主題番号
    LAYER_NO: int  # レイヤ番号
    AREA_SIZE: float  # ポリゴン面積(ha)
    IOSIDE_DIV: int  # 内外区分
    REMARK_STR: str  # 備考
    Shape_Leng: float  # シェープの長さ
    Shape_Area: float  # シェープの面積
    OBJ_NAME_ja: str  # シェープ名


NaturalParkAreasResponse = FeatureCollection[NaturalParkAreasProperties]


class LandslidePreventionDistrictsProperties(TileProperties, total=False):
    """One feature's `properties` from XKT021, 国土数値情報（地すべり防止地区）API.

    See https://www.reinfolib.mlit.go.jp/help/apiManual/xkt021/
    """

    prefecture_code: str  # 都道府県コード
    group_code: str  # 行政コード
    city_name: str  # 市町村名
    region_name: str  # 区域名
    address: str  # 所在地
    notice_date: str  # 告示年月日
    notice_number: str  # 告示番号
    landslide_area: str  # 指定面積（ha）
    charge_ministry_code: int  # 所管省庁コード
    prefecture_name: str  # 都道府県名
    charge_ministry_name: str  # 所管省庁名


LandslidePreventionDistrictsResponse = FeatureCollection[LandslidePreventionDistrictsProperties]


class LargeScaleDevelopedEmbankmentsProperties(TileProperties, total=False):
    """One feature's `properties` from XKT020, 国土数値情報（大規模盛土造成地マップ）API.

    See https://www.reinfolib.mlit.go.jp/help/apiManual/xkt020/
    """

    embankment_classification: str  # 盛土区分
    prefecture_code: str  # 都道府県コード
    prefecture_name: str  # 都道府県名
    city_code: str  # 市区町村コード
    city_name: str  # 市区町村名
    embankment_number: str  # 盛土番号


LargeScaleDevelopedEmbankmentsResponse = FeatureCollection[LargeScaleDevelopedEmbankmentsProperties]


class SteepSlopeFailureHazardAreasProperties(TileProperties, total=False):
    """One feature's `properties` from XKT022, 国土数値情報（急傾斜地崩壊危険区域）API.

    Close to XKT021 but not the same keys: the notice fields are `public_notice_*` here and
    `notice_*` there, and this endpoint carries no 所管省庁. `landslide_area` is the API's name
    for 指定面積 on both.

    See https://www.reinfolib.mlit.go.jp/help/apiManual/xkt022/
    """

    prefecture_code: str  # 都道府県コード
    group_code: str  # 行政コード
    city_name: str  # 市町村名
    region_name: str  # 区域名
    address: str  # 所在地
    public_notice_date: str  # 公示年月日
    public_notice_number: str  # 公示番号
    landslide_area: str  # 指定面積（ha）
    prefecture_name: str  # 都道府県名


SteepSlopeFailureHazardAreasResponse = FeatureCollection[SteepSlopeFailureHazardAreasProperties]


class DistrictPlansProperties(TileProperties, total=False):
    """One feature's `properties` from XKT023, 都市計画決定GISデータ（地区計画）API.

    See https://www.reinfolib.mlit.go.jp/help/apiManual/xkt023/
    """

    plan_name: str  # 計画名
    plan_type_ja: str  # 計画区分名
    kubun_id: str  # 区分コード
    group_code: str  # 行政コード
    decision_date: str  # 設定年月日
    decision_type_ja: str  # 設定区分名
    decision_maker: str  # 設定者名
    notice_number: str  # 告示番号
    prefecture: str  # 都道府県名
    city_name: str  # 市町村名
    first_decision_date: str  # 当初決定日
    notice_number_s: str  # 告示番号S


DistrictPlansResponse = FeatureCollection[DistrictPlansProperties]


class HighLevelUseDistrictsProperties(TileProperties, total=False):
    """One feature's `properties` from XKT024, 都市計画決定GISデータ（高度利用地区）API.

    See https://www.reinfolib.mlit.go.jp/help/apiManual/xkt024/
    """

    advanced_name: str  # 高度名称
    advanced_type_ja: str  # 高度区分名
    kubun_id: str  # 区分コード
    group_code: str  # 行政コード
    decision_date: str  # 設定年月日
    decision_type_ja: str  # 設定区分名
    decision_maker: str  # 設定者名
    notice_number: str  # 告示番号
    prefecture: str  # 都道府県名
    city_name: str  # 市町村名
    first_decision_date: str  # 当初決定日
    notice_number_s: str  # 告示番号S


HighLevelUseDistrictsResponse = FeatureCollection[HighLevelUseDistrictsProperties]


class ExpectedFloodInundationAreasAtMaximumScaleProperties(TileProperties, total=False):
    """One feature's `properties` from XKT026, 国土数値情報（洪水浸水想定区域（想定最大規模））API.

    Keyed `A31a_*`: 国土数値情報 splits its 洪水浸水想定区域 data into four categories and this
    endpoint serves one of them.

    See https://www.reinfolib.mlit.go.jp/help/apiManual/xkt026/
    """

    A31a_201: str  # 河川番号
    A31a_202: str  # 河川名
    A31a_203: str  # 河川管理番号
    A31a_204: str  # 河川管理者
    A31a_205: int  # 浸水深ランク


ExpectedFloodInundationAreasAtMaximumScaleResponse = FeatureCollection[
    ExpectedFloodInundationAreasAtMaximumScaleProperties
]


class ExpectedStormSurgeInundationAreasProperties(TileProperties, total=False):
    """One feature's `properties` from XKT027, 国土数値情報（高潮浸水想定区域）API.

    See https://www.reinfolib.mlit.go.jp/help/apiManual/xkt027/
    """

    A49_001: str  # 都道府県名
    A49_002: str  # 都道府県コード
    A49_003: str  # 浸水深区分
    target_year: int  # 対象年


ExpectedStormSurgeInundationAreasResponse = FeatureCollection[ExpectedStormSurgeInundationAreasProperties]


class ExpectedTsunamiInundationProperties(TileProperties, total=False):
    """One feature's `properties` from XKT028, 国土数値情報（津波浸水想定）API.

    See https://www.reinfolib.mlit.go.jp/help/apiManual/xkt028/
    """

    A40_001: str  # 都道府県名
    A40_002: str  # 都道府県コード
    A40_003: str  # 津波浸水深の区分
    target_year: int  # 対象年


ExpectedTsunamiInundationResponse = FeatureCollection[ExpectedTsunamiInundationProperties]


class LiquefactionTendencyBasedOnTopographicalClassificationProperties(TileProperties, total=False):
    """One feature's `properties` from XKT025, 国土交通省都市局（地形区分に基づく液状化の発生傾向図）API.

    The classification is finer than the dataset name suggests: `topographic_classification_code`
    is one of 28 微地形区分, and `liquefaction_tendency_level` grades the tendency on six levels.

    See https://www.reinfolib.mlit.go.jp/help/apiManual/xkt025/
    """

    mesh_code: str  # メッシュコード
    topographic_classification_code: int  # 微地形区分（28区分）
    topographic_classification_name_ja: str  # 微地形区分の名称
    liquefaction_tendency_level: int  # 液状化発生傾向の強弱(6段階区分)
    note: str  # 説明


LiquefactionTendencyBasedOnTopographicalClassificationResponse = FeatureCollection[
    LiquefactionTendencyBasedOnTopographicalClassificationProperties
]


class SedimentDisasterAlertAreasProperties(TileProperties, total=False):
    """One feature's `properties` from XKT029, 国土数値情報（土砂災害警戒区域）API.

    See https://www.reinfolib.mlit.go.jp/help/apiManual/xkt029/
    """

    A33_001: int  # 現象の種類
    A33_002: int  # 区域区分
    A33_003: str  # 都道府県コード
    A33_004: str  # 区域番号
    A33_005: str  # 区域名
    A33_006: str  # 所在地
    A33_007: str  # 公示日
    A33_008: int  # 特別警戒未指定フラグ


SedimentDisasterAlertAreasResponse = FeatureCollection[SedimentDisasterAlertAreasProperties]


class CityPlanningRoadsProperties(TileProperties, total=False):
    """One feature's `properties` from XKT030, 都市計画決定GISデータ（都市計画道路）API.

    See https://www.reinfolib.mlit.go.jp/help/apiManual/xkt030/
    """

    planning_road_ja: str  # 都市計画道路種類名
    kubun_id: int  # 区分コード
    prefecture: str  # 都道府県名
    city_code: str  # 市区町村コード
    city_name: str  # 市区町村名
    first_decision_date: str  # 当初決定日
    decision_date: str  # 設定年月日
    decision_type_ja: str  # 設定区分名
    decision_maker: str  # 設定者名
    notice_number_s: str  # 告示番号S
    notice_number: str  # 告示番号


CityPlanningRoadsResponse = FeatureCollection[CityPlanningRoadsProperties]


class DenselyInhabitedDistrictsProperties(TileProperties, total=False):
    """One feature's `properties` from XKT031, 国土数値情報（人口集中地区）API.

    See https://www.reinfolib.mlit.go.jp/help/apiManual/xkt031/
    """

    A16_001: str  # DIDid
    A16_002: str  # 行政区域コード
    A16_003: str  # 市区町村名称
    A16_004: int  # 人口集中地区符合
    A16_005: int  # 人口
    A16_006: float  # 面積
    A16_007: int  # 前回人口
    A16_008: float  # 前回面積
    A16_009: float  # 全域に占める人口集中地区の人口割合
    A16_010: float  # 全域に占める人口集中地区の面積割合
    A16_011: int  # 国勢調査年度
    A16_012: int  # 人口（男）
    A16_013: int  # 人口（女）
    A16_014: int  # 世帯数（総数）


DenselyInhabitedDistrictsResponse = FeatureCollection[DenselyInhabitedDistrictsProperties]


class DisasterHistoryProperties(TileProperties, total=False):
    """One feature's `properties` from XST001, 国土調査（災害履歴）API.

    `disastertype_code` is the API's spelling, without an underscore between `disaster` and
    `type`, and it is both the filter and an output field.

    See https://www.reinfolib.mlit.go.jp/help/apiManual/xst001/
    """

    disastertype_code: str  # 災害分類コード
    disaster_name_ja: str  # 分類の呼称（災害種別等）
    disaster_date: str  # 西暦年月日
    disaster_source: str  # 資料名（発行者）


DisasterHistoryResponse = FeatureCollection[DisasterHistoryProperties]


class DesignatedEmergencyEvacuationSitesProperties(TileProperties, total=False):
    """One feature's `properties` from XGT001, 国土地理院GISデータ（指定緊急避難場所）API.

    See https://www.reinfolib.mlit.go.jp/help/apiManual/xgt001/
    """

    common_id: str  # 共通ID
    prefecture_and_city: str  # 都道府県名及び市町村名
    facility_name_ja: str  # 施設・場所名
    address_ja: str  # 住所
    flood_flag: bool  # 洪水
    landslide_flag: bool  # 崖崩れ、土石流及び地滑り
    high_tide_flag: bool  # 高潮
    earthquake_flag: bool  # 地震
    tsunami_flag: bool  # 津波
    large_fire_flag: bool  # 大規模な火事
    inland_flooding_flag: bool  # 内水氾濫
    volcanic_phenomenon_flag: bool  # 火山現象
    same_address_flag: bool  # 指定避難所との住所同一
    remarks: str  # 備考


DesignatedEmergencyEvacuationSitesResponse = FeatureCollection[DesignatedEmergencyEvacuationSitesProperties]
