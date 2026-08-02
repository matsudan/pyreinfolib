# Contributing

## 開発環境

```shell
uv sync --locked
uv run ruff check .
uv run ruff format --check .
uv run ty check
uv run pytest
```

CI が実行するのはこの5つです。

## 型チェック

型情報を同梱しているため（[PEP 561](https://peps.python.org/pep-0561/)）、**型注釈は公開APIの一部**です。破ればテストが通っていても利用者が壊れます。

型チェッカーは [ty](https://github.com/astral-sh/ty) です。mypy と Pyrefly と比較して選定し、実際に過去のバグを検出できることを確認した上で採用しています。

`pyproject.toml` で **バージョンを厳密に固定**しています（`ty==0.0.65`）。他の開発依存は下限指定ですが、ty は pre-1.0 で、診断内容を含む破壊的変更が任意の 0.0.x 間で起こりうると公式に明記されています。下限指定にすると、このリポジトリを変更していないのにパッチ更新で CI が赤くなります。更新は Dependabot に提案させて、そのとき差分を読んでください。

### `tests/typing_usage.py`

**`pyreinfolib` だけを検査しても不十分です。** #45 のズームレベルのバグは、パッケージ内部では整合していて実行時テストも全部通る一方、README が書いている `client.get_...(*tile)` と `tiles.covering()` のループが型チェッカーに拒否される状態でした。エラーは呼び出し側にしか現れません。

そのため `tests/typing_usage.py` に**利用者が書くとおりのコード**を置いて検査対象にしています。テストモジュールではなく、実行もされません。README が推奨する書き方を追加したら、ここにも足してください。ここが通らなくなったらドキュメントが嘘をついています。

拒否されるべきものは `# ty: ignore[...]` を付けて記録しています。`ty check` は何も抑制しなかった ignore を報告し、warning でも実行が失敗するため、**拒否されなくなったら CI が落ちます**。

```python
# 2つのコード表は交換可能ではない
client.get_real_estate_prices(
    year=2024,
    price_classification=LandPriceClassification.LAND_MARKET_VALUE_PUBLICATION,  # ty: ignore[invalid-argument-type]
)
```

## プルリクエスト

squash merge のみを使います。リポジトリ設定が `squash_merge_commit_title: PR_TITLE` / `squash_merge_commit_message: PR_BODY` なので、**PR のタイトルと説明文がそのまま `main` のコミットメッセージになります**。

- タイトルは [Conventional Commits](https://www.conventionalcommits.org/) 準拠。`.github/workflows/pr-title.yml` が検証します
- release-please がタイトルからバージョンと CHANGELOG を生成します。`feat` は minor、`fix` は patch、`!` 付きは破壊的変更（1.0 到達前は minor）
- 破壊的変更は説明文の末尾に `BREAKING CHANGE: <移行手順>` のフッタを書いてください。CHANGELOG の BREAKING CHANGES に載ります
- 説明文が git 履歴に残るため、レビュー用のチェックリストや議論の経緯は書かないでください

### 説明文の書式

冒頭にこの変更が必要だった理由を数行。続けて2節に分け、箇条書きで書いてください。

- `## Changes` — 何が変わったか。ファイル名と設定値を具体的に、1行1項目。理由は書きません
- `## Notes` — 却下した選択肢とその理由、非自明な制約、そのコードが存在する理由

`## Notes` に書くのは、**diff、コードコメント、このファイル、CI の結果のどれを見ても分からないこと**だけです。テスト数やカバレッジは CI が示すので書きません。「ズーム15では区一つが30タイル」のように設計判断の根拠になる数値は書きます。

テンプレートは置いていません。`PR_BODY` 設定では雛形がそのままコミットメッセージに残り、`--body-file` や Dependabot、release-please には届かないためです。

## 命名

メソッド名・引数名・enum 名は、**不動産情報ライブラリの[API操作説明](https://www.reinfolib.mlit.go.jp/help/apiManual/)に載っている API 名から機械的に導出します**。読みやすさを基準に選びません。

理由は3つあります。

API 名は外部にある唯一の安定した共有語彙です。利用者が読むのは MLIT のマニュアルであって、このライブラリのソースではありません。マニュアルの API 一覧を見ている人が対応するメソッドを推測できる状態に価値があります。

公開APIは35本あります。読みやすさを基準にすると35回の裁量判断が必要で、必ず途中でぶれます。

API 側が改称したとき、追随すべきかの判断がつきます。

### 導出手順

1. API 名から始める
2. **出典を落とす。** 国土数値情報、都市計画決定GISデータ、国土地理院GISデータ、国土調査、国土交通省都市局は、誰が公開したデータかを示すもので、何のデータかを示していない
3. **主題を言い換えただけの括弧を落とす。** 不動産価格（取引価格・成約価格）の括弧は 不動産価格 の内訳なので落とす
4. **括弧の中身がデータセット名なら残す。** 出典が主題の位置に来ている場合（手順2で頭を落とした場合）はこちら。国土数値情報（駅別乗降客数）→ 駅別乗降客数
5. **定型辞を落とす。** 情報、取得、一覧、API
6. **必須引数で表現されている限定を落とす。** 都道府県内市区町村一覧 の 都道府県内 は `area` 引数が表すので落とす
7. **トップレベルの「・」は `and` として残す。** 地価公示・地価調査 はどちらも独立したデータセットなので両方残す。手順3の括弧内の「・」とは違う。共通する語をまとめるかどうかは典拠を見て決めます
   - **典拠に並列形があればそのまま使う。** 防火・準防火地域 は建築基準法第5節の節名が `Fire Prevention Districts and Quasi-fire Prevention Districts` で、日本語が1回しか書いていない「地域」を2回書いています。`Fire Prevention District` が定義語なので、分解せず文字列のまま保ちます。検索でも届きます
   - **典拠に並列形がなければ共通部分をまとめてよい。** 地価公示・地価調査 は並列形の公式訳がなく、組織名（地価公示室 / 地価調査課）の完全形から `land_market_value_publication_and_research` を導いています
8. **「ポイント (点)」は `_point` として残す。** XPT001 と XPT002 だけが持つ
9. 残った語を用語集で訳す
10. `get_` を付ける

### 長さは基準にしません

手順の結果が長くても短縮しません。短縮するかを毎回判断すると、判断のぶれが名前のぶれになります。`get_land_market_value_publication_and_research_point` は規則を守った結果として正しい名前です。

### 単数・複数

- **メソッド名**は返り値に合わせます。一覧が返るなら複数（`get_municipalities`）
- **enum メンバー**は単数です（`RESIDENTIAL_LAND`、`LAND_AND_BUILDING`）

### 引数名は API のパラメータ名を snake_case にしただけにします

`administrativeAreaCode` → `administrative_area_code`、`welfareFacilityMiddleClassCode` → `welfare_facility_middle_class_code` です。メソッド名と違って導出手順はありません。

**同じコード表でも API の綴りが違えば引数名も分けます。** 市区町村コードは XIT001 では `city`、XKT004 などでは `administrativeAreaCode` です。同じ5桁のコード表ですが、片方に寄せると寄せなかった側の引数名が、利用者がマニュアルで読むパラメータ名と一致しなくなります。docstring で同じコード表だと伝えます。

例外は Python の予約語と衝突する場合です。XPT001 の `from` / `to` は `period_from` / `period_to` にしています。

### 導出例

規則が既存の6メソッドを再現することを確認済みです。

| ID | API 名 | 落とした部分 | メソッド名 |
|---|---|---|---|
| XIT001 | 不動産価格（取引価格・成約価格）情報取得API | 括弧（手順3）、情報取得 | `get_real_estate_prices` |
| XIT002 | 都道府県内市区町村一覧取得API | 都道府県内（手順6）、一覧取得 | `get_municipalities` |
| XCT001 | 鑑定評価書情報API | 情報 | `get_appraisal_reports` |
| XPT001 | 不動産価格（取引価格・成約価格）情報のポイント (点) API | 括弧（手順3）、情報 | `get_real_estate_prices_point` |
| XPT002 | 地価公示・地価調査のポイント (点) API | なし | `get_land_market_value_publication_and_research_point` |
| XKT015 | 国土数値情報（駅別乗降客数）API | 国土数値情報（手順2） | `get_number_of_passengers_per_station` |

### レスポンスの型名はメソッド名から導出します

`pyreinfolib.types` の型名は、**メソッド名から `get_` を落として PascalCase にし、接尾辞を付けるだけ**です。API 名からの導出は1回で済ませ、2回目をしません。

| 接尾辞 | 対象 | 例 |
|---|---|---|
| `Response` | メソッドの返り値そのもの | `UseDistrictsResponse` |
| `Properties` | タイル系の1フィーチャの `properties` | `UseDistrictsProperties` |
| `Item` | 非タイル系の `data` の1要素 | `RealEstatePricesItem` |

**単数化しません。** 1フィーチャを表す型なので意味的には単数が正しいのですが、`get_nursery_schools_and_kindergartens_etc` や `get_fire_prevention_districts_and_quasi_fire_prevention_districts` のような並列名を単数化すると `and` を `or` に変えるかどうかから判断が始まります。[長さは基準にしません](#長さは基準にしません)と同じ理由で、裁量が入る余地を作らない方を採ります。接尾辞が「1件分」を担っています。

この対応は `tests/test_types.py` が実行時に検証します。メソッドを追加して型を付け忘れる、あるいは隣のエンドポイントの型を貼ってしまう、というのはどちらも `ruff` と `ty` と `test_client.py` を通ってしまうためです。

## enum

### enum にするか `Literal` にするか

**コードそれ自体に意味が読み取れないものは enum にします。** `"02"` は 成約価格情報 を意味しますが、呼び出し側からは何も読み取れません。

**値に意味が読み取れるものは `Literal` のままにします。** `quarter: Literal[1, 2, 3, 4]`、`language: Literal["ja", "en"]`、`z: Literal[11, 12, 13, 14, 15]` はそのままで十分です。

`StrEnum` を使います。実行時は文字列としても動くので、型チェックだけが新しい制約になります。

### enum にするか `str` にするか

コード表が enum になる条件は2つあり、両方必要です。

- **数えられる規模である。** `UseDivision` は8件、`LandTypeCode` は5件です。都道府県コード（47件）と市区町村コード（約1900件）は `area`、`city`、`administrative_area_code` として `str` のままにし、docstring にコード表の URL を置いています
- **全メンバーに典拠のある訳語がある。** 一部しか訳せないコード表は enum にしません。呼び出し側が同じ引数に enum メンバーと生の文字列を混ぜることになり、enum を作った意味がなくなります

福祉施設大分類コード（XKT011）が2つ目に当たる例です。7件で規模は足りていますが、うち2件に公表された英訳がありません。

| コード | 用語 | 英訳 | 典拠 |
|---|---|---|---|
| 01 | 保護施設 | public assistance facility | 生活保護法 第六章、38条（[laws/view/24](https://www.japaneselawtranslation.go.jp/ja/laws/view/24/je)） |
| 02 | 老人福祉施設 | welfare facility for the elderly | 老人福祉法5条の3（[laws/view/3930](https://www.japaneselawtranslation.go.jp/ja/laws/view/3930/je)） |
| 03 | 障害者支援施設等 | support facility for persons with disabilities | 障害者総合支援法5条11項（[laws/view/4093](https://www.japaneselawtranslation.go.jp/ja/laws/view/4093/je)） |
| 04 | 身体障害者社会参加支援施設 | **なし** | 身体障害者福祉法5条。法令訳DBに収録なし |
| 05 | 児童福祉施設等 | child welfare institution | 児童福祉法7条1項（[laws/view/4035](https://www.japaneselawtranslation.go.jp/ja/laws/view/4035/je)） |
| 06 | 母子・父子福祉施設 | **なし** | 母子及び父子並びに寡婦福祉法38条。法令訳DBに収録なし |
| 99 | その他の社会福祉施設等 | social welfare facility | 社会福祉法62条（[laws/view/3813](https://www.japaneselawtranslation.go.jp/ja/laws/view/3813/je)） |

上の5件は[厚生労働白書の英語版](https://www.mhlw.go.jp/wp/hakusyo/kousei/11-2/kousei-data/PDF/23010804_en.pdf)でも同じ組み合わせで使われています。04 と 06 は厚生労働省の英語資料でも旧称で揺れていて（`rehabilitation facilities for people with physical disabilities` など）、現行名の定訳がありません。

**後から enum を足すのは非破壊的です。** `Sequence[str] | str | None` は `Sequence[WelfareFacilityClassCode | str] | WelfareFacilityClassCode | str | None` に広げられ、`str` を受け続けるので既存の呼び出しは壊れません。逆に `str` を enum だけに絞るのは壊れます。迷ったら `str` から始めてください。

### コード体系が別なら enum も分けます

API が同じパラメータ名を使っていても、コード表が違えば別の enum にします。`priceClassification` は XIT001/XPT001 では `01`/`02`、XPT002 では `0`/`1` です。1つにまとめると `01` を `0` の位置に送れてしまい、API はエラーではなく空の結果を返すため気づけません。

### メンバー名

用語集で訳し、日本語のコード表記をコメントで添えます。

```python
@unique
class PriceClassification(StrEnum):
    # 不動産取引価格情報
    REAL_ESTATE_TRANSACTION_PRICE = "01"

    # 成約価格情報
    CONTRACT_PRICE = "02"
```

## レスポンスの型

`pyreinfolib.types` に、各エンドポイントが返す本文の形を `TypedDict` で置いています。**静的な主張だけで、実行時の検証は一切しません。** `Client` はデコードした結果を型と照合しませんし、するつもりもありません。得られるのは `r["data"][0]` と `properties` が `Any` でなくなることで、キーの綴り間違いが `KeyError` ではなく型エラーになります。

### キーは API のタグ名をそのまま使います

各エンドポイントのマニュアル個別ページに `＜出力＞` の表があり、その **タグ名** の列が JSON のキーです。**整えずにそのまま写します。** 用語集は使いません。ここは訳す場所ではないからです。

結果として API 側の不統一が全部入ってきます。

- 国土数値情報の属性コード（`A27_001`、`P29_003`、`S12_009`）
- ローマ字（`kubun_id`、`youto_id`）
- `language` に追従するフィールドに付く `_ja` 接尾辞、表示整形済みの値に付く `u_` 接頭辞（`u_transaction_price_total_ja` は `"4,000万円"`）
- XCT001 だけは日本語のキーで、大半に U+3000 の全角スペースが入る
- API 自身の綴り間違い（XPT002 の `proximity_to_transportation_facilitites`）

**直すと存在しないキーになります。** 綴り間違いも直しません。

### 値型はマニュアルの宣言に従います

文字列型 → `str`、整数型 → `int`、実数型 → `float`、真偽型 → `bool`。

**マニュアルはフィールド名ごとではなくエンドポイントごとに型を書いていて、しかも自分と食い違っています。** `kubun_id` は XKT001・XKT003・XKT014・XKT030 で整数型、XKT023・XKT024 で文字列型です。同じ名前でも、そのページの記載通りに書いてください。[コードの桁数もエンドポイントごとに確認してください](#コードの桁数もエンドポイントごとに確認してください)と同じ構図です。

### 全フィールドを `total=False` にします

マニュアルは出力フィールドに必須の印を付けておらず、データ例の列が空のものも多いので、**どのキーが実際に来るかは記載がありません。** 読み取りは `total=False` でも型チェックを通ります。`total=False` が避けているのは、API がしていない保証をこちらが主張することです。

実レスポンスで確認できたフィールドは、1つずつ必須に締められます。

### nullability は表現しません

マニュアルに記載がないためです。ただし宣言型が文字列型でないフィールドはすべて具体的なデータ例を持っているので、その範囲では宣言型が裏付けられています。

**`| None` に広げるのは読み取り側にとって破壊的変更です。** 逆向き（`str | None` → `str`）は非破壊なので、[enum にするか `str` にするか](#enum-にするか-str-にするか)の「迷ったら広い方から」とは逆になります。推測で広げず、実レスポンスを見てから決めてください。

### 出力表はサーバ描画されていません

`＜パラメータ＞` の表と違い、`＜出力＞` の表はクライアント側で描画されます。表示されたテキストからの転記は空白が失われるので（XCT001 の U+3000 がこれで壊れます）、**生の HTML から取ってください。** RSC の flight payload の中に

```
<td id="api{ID}Output{N}Tag">タグ名</td>
<td id="api{ID}Output{N}DataType">文字列型</td>
```

という形で入っています。1つ目の行だけ添字がなく（`OutputTag`）、2行目以降が 0 から数えます。複数の出力形を持つエンドポイントはグループごとに接尾辞が付きます（XKT007 の2つ目の表が `apiXKT007_2Output...`）。

### 型にできない・型が2つあるエンドポイント

**XKT013（将来推計人口250mメッシュ）は `dict[str, Any]` です。** `MESH_ID` と `SHICODE` を除く34キーが年を含む名前で、マニュアルはその年を `20XX` というプレースホルダで書いています（`PT01_20XX`、`RTA_20XX`、`HITOKU20XX`）。実際に来る年は公表された推計次第なので、`TypedDict` にすると間違えるか年を発明することになります。周りの `FeatureCollection` は正確なままです。

**XCT001 は functional syntax で書きます。** 109キーのうち94個が Python の識別子になりません。クラス構文が使えないのはそのためです。

**XKT007 は2つの出力表を1つの型にマージしています。** 幼稚園・こども園なら学校系のフィールド、保育園なら福祉施設分類コードが付き、4フィールドが共通です。union にしていないのは、どうせ全フィールドが省略可能なので union が何も買わない上に、読む前に絞り込みを強制されるからです。**2つの形は共有フィールドの値ではなくキーの有無で分かれるので、絞り込む目印がありません。**

### 新しいエンドポイントを追加するとき

1. マニュアル個別ページの `＜出力＞` 表を生 HTML から取る
2. `<MethodName>Properties`（タイル系）または `<MethodName>Item`（非タイル系）を書く。`total=False`、キーはタグ名そのまま、値型は宣言通り、日本語の内容を行末コメントに添える
3. `<MethodName>Response` を `FeatureCollection[...]` か `DataResponse[...]` として定義する
4. メソッドの返り値に注釈を付ける。`tests/test_types.py` が対応を検証します
5. `tests/typing_usage.py` に読み取り側のコードを足す

### 実レスポンスとの照合が済んでいません

**現在の型はすべてマニュアルの `＜出力＞` 表だけを根拠にしています。** 実際のレスポンスと突き合わせていません。マニュアルが書いていないこと（キーが省略されるのか、null が来るのか）は[上記の通り](#全フィールドを-totalfalse-にします)保守的に倒してありますが、マニュアルが書いていることが実物と一致するかも未確認です。

APIキーが手元にあるときに、この順で確認してください。同じ確認を繰り返さないよう、済んだ項目は結果を書いてこの表から外します。

| 確認すること | 叩くもの | 違っていた場合 |
|---|---|---|
| XCT001 のキーが本当に日本語（U+3000 込み）か | `get_appraisal_reports` | `AppraisalReportsItem` の109キーを全面差し替え。**最も影響が大きい** |
| `proximity_to_transportation_facilitites` が本当に綴り違いのままか | `get_land_market_value_publication_and_research_point` | 型と、`types.py` / CONTRIBUTING / README の3箇所の記述を直す |
| `DataResponse` の封筒が `status` / `data` か、`status` が `"OK"` 以外を取るか | 非タイル系のどれか | マニュアルに記載がない部分。取らないなら `Literal["OK"]` に締められる |
| 整数型・実数型・真偽型のフィールドが `null` で来ることがあるか | 全般。XKT013 の `GASSAN20XX` はデータ例が空 | `\| None` へ広げる。**読み取り側にとって破壊的** なので、ここだけは実物を見ないと動かせない |
| キーが省略されるのか空文字で来るのか | `get_real_estate_prices` で農地・林地と中古マンションを比べる | 常に来るキーは `total=False` から必須に締められる（非破壊） |
| エンドポイントごとのジオメトリ種別 | タイル系全般。XKT029 は「ポリゴンとライン混在」とマニュアルが明記 | `Geometry` の合併型をエンドポイント別に狭められる |
| XKT013 のキーに入る年 | `get_future_population_estimates_by_250m_mesh` | 年が固定なら `dict[str, Any]` を `TypedDict` にできる |
| XKT007 の2つの形が共有フィールドの値で判別できるか | `get_nursery_schools_and_kindergartens_etc` | 判別できるなら union + 絞り込みにできる |

締める方向（`total=False` → 必須、合併型を狭める、`Literal` にする）は読み取り側にとって非破壊です。広げる方向（`None` を足す）は破壊的なので、`feat!:` が必要になります。

## 用語集

### 典拠の優先順位

1. **[日本法令外国語訳データベースシステム](https://www.japaneselawtranslation.go.jp/)**（法務省）。今回必要な語の多くは法令用語で、政府公式訳が条文単位で日英対応しています
2. **[地価に関する国際的な情報発信の強化に向けた検討業務 調査報告書](https://www.mlit.go.jp/common/000214955.pdf)**（国土交通省 土地・建設産業局、平成24年3月）。地価公示・鑑定評価の語彙について、MLIT が統一的な英訳を提示する目的で作成した用語集です。地価関連語は法令訳DBより詳しく、DBの訳に対する明示的な注記もあります
3. **所管省庁の英語版資料**。法令用語でないもの（統計用語、データセット名）
4. **既にこのライブラリで使っている訳語**。1〜3で確認できないもの

### 優先順位のどこにも訳語がないとき

根拠法が法令訳DBに未収録で、所管省庁の英語資料も旧称のまま揺れている語があります。**どの段階でも訳語を発明しないでください。** 次の順に試します。

1. **その語を名前にしない設計を選ぶ。** コード表なら `str` のままにできます（[enum にするか `str` にするか](#enum-にするか-str-にするか)）。メソッド名は避けようがないので、この手は使えません
2. **典拠のある部品から合成する。** 根拠法自身の造語パターンに従ってください。都市計画道路 は同法の 都市計画施設 = `city planning facility`、都市計画事業 = `city planning project` というパターンに、11条1項1号の 道路 = `roads` を入れて `city planning road` としています。部品のどちらかに典拠がなければ使えません
3. **二次資料で定着している訳語を採る。** 政府資料が原典として挙げられていて、かつ競合候補がない場合に限ります。立地適正化計画 = `location normalization plan` がこれです
4. **実装を保留する。** 上のどれも使えないとき

**どの段階で決めたか、そして空振りした当たり先を用語集に書いてください。** 原典が後から出てきたときに見直せます。当たり先を書き残さないと、次の人が同じ検索を繰り返します。

### API 名と公定訳が食い違うときは API 名に従います

XKT021 のデータセット名は 地すべり防止**地区** ですが、実体は地すべり等防止法3条の 地すべり防止**区域** で、公定訳は `landslide prevention area` です。メソッド名は `get_landslide_prevention_districts` にしています。

[命名](#命名)に書いた理由の通り、利用者が読むのは MLIT のマニュアルです。マニュアルの語からメソッドに辿り着ける方を採ります。**食い違いは docstring に書いてください。** 名前だけでは、公定訳を知っている人が誤りだと思います。

### 確定

| 日本語 | English | 典拠 |
|---|---|---|
| 用途地域 | use district | 建築基準法48条（[/laws/view/4024](https://www.japaneselawtranslation.go.jp/ja/laws/view/4024/je)） |
| 防火地域 | fire prevention district | 建築基準法53条3項 |
| 準防火地域 | quasi-fire prevention district | 建築基準法53条3項 |
| 高度利用地区 | high-level use district | 建築基準法59条 |
| 高度地区 | height control district | 建築基準法58条 |
| 都市計画区域 | city planning area | 都市計画法5条（[/laws/view/3841](https://www.japaneselawtranslation.go.jp/ja/laws/view/3841/je)） |
| 区域区分 | area classification | 都市計画法7条 |
| 市街化区域 | urbanization promotion area | 都市計画法7条 |
| 市街化調整区域 | urbanization control area | 都市計画法7条 |
| 地区計画 | district plan | 都市計画法12条の4 |
| 地価公示 | land market value publication | MLIT 用語集 200, 201（地価公示室 / 地価公示法） |
| 地価調査 | land market value research | MLIT 用語集 205（地価調査課） |
| 都道府県地価調査 | prefectural land market value research | MLIT 用語集 259 |
| 標準地 | standard site | MLIT 用語集 275 |
| 基準地 | standard site published by the prefectural government | MLIT 用語集 48 |
| 土地鑑定委員会 | Land Appraisal Committee | [MLIT 英語ページ](https://www.mlit.go.jp/en/totikensangyo/totikensangyo_fr4_000001.html) |
| 自然公園 | natural park | 自然公園法2条1号（[laws/view/3060](https://www.japaneselawtranslation.go.jp/ja/laws/view/3060/je)） |
| 国立公園 | national park | 自然公園法2条2号 |
| 国定公園 | quasi-national park | 自然公園法2条3号 |
| 都道府県立自然公園 | prefectural natural park | 自然公園法2条4号 |
| 特別地域 | special area | 自然公園法20条 |
| 普通地域 | ordinary area | 自然公園法33条 |
| 指定緊急避難場所 | designated emergency evacuation site | 災害対策基本法第7章2節、49条の4（[laws/view/4171](https://www.japaneselawtranslation.go.jp/ja/laws/view/4171/je)） |
| 指定避難所 | designated shelter | 災害対策基本法49条の7 |
| 災害危険区域 | disaster risk area | 建築基準法39条（[laws/view/4024](https://www.japaneselawtranslation.go.jp/ja/laws/view/4024/je)） |
| 都市計画施設 | city planning facility | 都市計画法4条6項 |
| 都市計画事業 | city planning project | 都市計画法4条15項 |
| 都市施設 | urban facility | 都市計画法4条5項 |
| 都市計画道路 | city planning road | 都市計画法に定義なし。下記の通り合成 |
| 人口集中地区 | densely inhabited district | [総務省統計局 英語ページ](https://www.stat.go.jp/english/data/jyutaku/25021.html) |
| 地すべり防止区域 | landslide prevention area | 都市計画法33条1項8号（[laws/view/3841](https://www.japaneselawtranslation.go.jp/ja/laws/view/3841/je)） |
| 土砂災害警戒区域 | sediment disaster alert area | 土砂災害防止法の英語題名。都市計画法33条1項8号で引用 |
| 土砂災害特別警戒区域 | sediment disaster special alert area | 都市計画法33条1項8号 |
| 立地適正化計画 | location normalization plan | 二次資料のみ。下記の通り |

### 立地適正化計画は二次資料で決めています

[優先順位のどこにも訳語がないとき](#優先順位のどこにも訳語がないとき)の手順3に当たる唯一の語です。`適正化` 単体の訳語典拠がないため、手順2の合成も使えませんでした。

**採った根拠**

- [ジャパンシステムのコラム](https://www.japan-systems.co.jp/column/%E9%83%BD%E5%B8%82%E8%A8%88%E7%94%BB%E3%81%A8%E5%85%AC%E5%85%B1%E6%96%BD%E8%A8%AD%E3%83%9E%E3%83%8D%E3%82%B8%E3%83%A1%E3%83%B3%E3%83%88%E3%82%B3%E3%83%A9%E3%83%A0%E2%91%A1%E3%80%8C%E7%AB%8B%E5%9C%B0/)（2016年、首都大学東京の都市計画研究者）が「国交省資料によると英語では Location Normalization Plan と呼ばれる」と書き、脚注で `Major Efforts Made in the Fields of National Land and Transportation` という MLIT の英語ページを原典に挙げています
- 査読文献で定着しています。[Sustainability 2020](https://www.mdpi.com/2071-1050/12/3/989/xml)、[Sustainability 2021](https://www.mdpi.com/2071-1050/13/23/13107/xml)（`the Location Normalization Plan (LNP)` と略称まで定義）
- 競合候補がありません。政府資料にも査読文献にも別の訳は見つかりませんでした

**空振りした当たり先**（原典の MLIT ページには到達できていません）

MLIT 英語トップ（現行と2016年9月3日の Wayback スナップショット）、City Bureau 英語索引 `/en/toshi/index.html`、同索引がリンクする `/common/000996976.pdf`、`/en/toshi/city_plan/compactcity_network.html` と配下の `/en/` PDF（中身は日本語）、英訳パンフ `/common/001048781.pdf`（低炭素まちづくり計画の資料）、Wayback CDX の `mlit.go.jp/en/*effort*`（0件）。

なお City Bureau 英語索引は `Act on Special Measures Concerning Urban Renaissance` と `City Planning Act` を掲げていて、法令訳DBの引用から取った題名と一致します。法令名の方は二重に典拠が付いています。

### 未翻訳の法令の英語題名は、翻訳済みの法令の引用から取れます

法令訳DBに収録されていない法令でも、収録されている法令が条文中で引用していれば公式の英語題名が判明します。**照合には法令番号を使ってください。** 1つの条文が複数の法令を引用していることがあり、条文単位で対応させると別の法令の題名を拾います。

| 法令 | 英語題名 | 引用元 |
|---|---|---|
| 水防法（昭和24年法律第193号） | Flood Prevention Act | 災害対策基本法 |
| 地すべり等防止法（昭和33年法律第30号） | Landslide Prevention Act | 災害対策基本法、都市計画法 |
| 土砂災害防止法（平成12年法律第57号） | Act for Promotion of Measures to Prevent Sediment Disasters in Sediment Disaster Alert Areas | 都市計画法33条1項8号 |
| 津波防災地域づくり法（平成23年法律第123号） | Act on Regional Development for Tsunami Disaster Prevention | 建築基準法 |
| 都市再生特別措置法（平成14年法律第22号） | Act on Special Measures Concerning Urban Renaissance | 都市計画法 |
| 海岸法 | Coast Act | 災害対策基本法 |

**都市計画法33条1項8号は特に当たり所です。** 開発許可の基準として、災害危険区域・地すべり防止区域・土砂災害特別警戒区域を並べて引用しています。

**都市計画道路は合成した訳語です。** 都市計画法は 都市計画道路 を定義しておらず、都市計画施設として定められた道路の通称です。同法の訳が 都市計画施設 を `city planning facility`、都市計画事業 を `city planning project` としているので、`city planning` + 名詞 は同法自身の造語パターンです。道路 は11条1項1号の都市施設の一覧で `roads` です。12条の11には `roads that are city planning facilities` という言い方も出てきます。

MLIT 用語集は `Land （Market） Value` と括弧付きで記載していますが、識別子に括弧は使えず、[MLIT の英語ページ](https://www.mlit.go.jp/en/totikensangyo/totikensangyo_fr4_000001.html)が括弧なしで運用しているため、括弧を外した形を採用します。

**`public notice` は使いません。** MLIT 用語集 201 に「Public notice という訳もあるようだが、通達と紛らわしい」と、退けた理由が明記されています。英語ページも `Land price public notice system` を「以前の呼称」としています。

**公示と調査は Publication と Research で区別します。** 用語集 259 の 都道府県地価調査 の訳は説明的な文章で、地価公示と同じ "publication" を使っています。そのまま識別子にすると2つのデータセットがほぼ同名になるため、組織名（地価公示室 / 地価調査課）の固有名詞形から採ります。

用途地域の内訳（13種）も同じ典拠から取れます。第一種低層住居専用地域 = category 1 low-rise exclusive residential district、準住居地域 = quasi-residential district、田園住居地域 = countryside residential district、準工業地域 = quasi-industrial district、工業専用地域 = exclusive industrial district、ほか。

### 注意: 用途地域と用途区分は別の語彙です

鑑定評価書API（XCT001）の `division`（`UseDivision`）は**地価公示の用途区分**で、都市計画法の**用途地域**ではありません。

- 準工業**地**（`QUASI_INDUSTRIAL_LAND`）≠ 準工業**地域**（quasi-industrial district）
- 現況林地、宅地見込地 も用途地域には存在しません

用語集を機械的に当てて `UseDivision` を district に「直す」のは誤りです。

### 未確定

根拠法・典拠候補まで特定済みです。確定したらこの表から上の表へ移してください。

| 用語 | 典拠を探す先 | 用途 |
|---|---|---|
| 大規模盛土造成地マップ | 国土交通省 | XKT020 |
| 急傾斜地崩壊危険区域 | 急傾斜地法（法令訳DBに収録なし。翻訳済み法令からの引用も見つからない） | XKT022 |
| 地形区分に基づく液状化の発生傾向図 | 国土交通省都市局 | XKT025 |
| 洪水浸水想定区域 | 水防法（法令訳DBに収録なし） | XKT026 |
| 高潮浸水想定区域 | 水防法（法令訳DBに収録なし） | XKT027 |
| 津波浸水想定 | 津波防災地域づくり法（法令訳DBに収録なし） | XKT028 |

| 災害履歴 | 国土調査（土地履歴調査） | XST001 |

**「法令訳DBに収録なし」は確認済みです。** 法令検索で法令名を引いて0件でした。同じ確認を繰り返さないよう結果を残しています。

収録がなくても、まず[翻訳済みの法令からの引用](#未翻訳の法令の英語題名は翻訳済みの法令の引用から取れます)を探してください。それでも出てこなければ優先順位3（所管省庁の英語版資料）に降りることになります。

法令訳DBの引き方は、法令名から翻訳IDを引いて `https://www.japaneselawtranslation.go.jp/ja/laws/view/{id}/je` を開きます。対訳ページは日本語と英語の div が交互に並ぶので、定義条（「この法律において『○○』とは」）を見ると定義語の訳が取れます。辞書検索（標準対訳辞書）は一般的な法令用語しか収録しておらず、施設名や区域名は引けません。

XKT004〜018 の施設系（小学校区、学校、保育園・幼稚園等、医療機関、福祉施設、図書館、市区町村役場及び集会施設等）は一般語なので法令典拠は不要です。国土数値情報は英語のデータセット名を公開していないため、当たる先もありません。

### 「等」は `_ETC` にします

`LandTypeCode.PRE_OWNED_CONDOMINIUMS_ETC`（中古マンション等）が先例です。メソッド名でも同じで、保育園・幼稚園**等** → `get_nursery_schools_and_kindergartens_etc`。

### ズーム範囲は必ずマニュアルの個別ページで確認してください

`/help/apiManual/{endpoint_id}/`（小文字）がサーバ描画されており、`＜パラメータ＞` の表に `z` の行があります。「11（市）～15（詳細）で指定可能」のように書かれています。

**エンドポイントごとに違います。** 実測した範囲は 9-15、11-15、13-15、14-15 の4種類でした。既定の `range(11, 16)` から外れるものは `_get_tile` に `zoom_levels` を渡してください。

範囲を間違えても**リクエストは飛びません**。狭すぎればAPIが対応する縮尺を手元で拒否し、広すぎればAPIがエラーを返します。前者はレスポンスに何も現れないので、記載を必ず確認してください。

### コードの桁数もエンドポイントごとに確認してください

同じコード表でも、桁数の書き方がエンドポイントで違います。都道府県コードは XKT019 が `9`（先頭の0を除く）、XKT021 が `09`（2桁）です。引数名も型も同じなので、コードからは区別が付きません。

XKT019 側は先頭0付きを `ValueError` で断っています（`_join_unpadded_codes`）。ズーム範囲と同じで、マニュアルが定める形式外の値は手元で断る扱いです。**これをライブラリ全体の規則にしないでください。** XKT021 が求める形式を拒否することになります。
