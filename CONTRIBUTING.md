# Contributing

訳語と典拠は [GLOSSARY.md](GLOSSARY.md) にあります。

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
- 破壊的変更は[説明文にフッタを書いてください](#破壊的変更は-breaking-change-を-pr-本文に書いてください)
- 説明文が git 履歴に残るため、レビュー用のチェックリストや議論の経緯は書かないでください

### 説明文の書式

冒頭にこの変更が必要だった理由を数行。続けて2節に分け、箇条書きで書いてください。

- `## Changes` — 何が変わったか。ファイル名と設定値を具体的に、1行1項目。理由は書きません
- `## Notes` — 却下した選択肢とその理由、非自明な制約、そのコードが存在する理由

`## Notes` に書くのは、**diff、コードコメント、このファイル、CI の結果のどれを見ても分からないこと**だけです。テスト数やカバレッジは CI が示すので書きません。「ズーム15では区一つが30タイル」のように設計判断の根拠になる数値は書きます。

テンプレートは置いていません。`PR_BODY` 設定では雛形がそのままコミットメッセージに残り、`--body-file` や Dependabot、release-please には届かないためです。

### 破壊的変更は `BREAKING CHANGE:` を PR 本文に書いてください

```
BREAKING CHANGE: `get_old_name` is now `get_new_name`. ...
```

**ローカルのコミットメッセージに書いても届きません。** マージコミットの本文は PR 本文になり、ローカルのコミットメッセージは捨てられます。

タイトルの `feat!:` は版数を上げるのに足ります。しかし**移行方法は本文のフッタにしか書けません**。フッタがないと CHANGELOG と GitHub Release のノートに subject 行だけが載り、利用者は何が何に変わったか分かりません。0.7.0 で実際に起きました（#69）。

**リリース PR を直す場合は、マージ前に CHANGELOG とリリース PR 本文の両方を直してください。** main に別のコミットが入ると release-please がどちらも作り直します。

## 命名

メソッド名・引数名・enum 名は、**不動産情報ライブラリの[API操作説明](https://www.reinfolib.mlit.go.jp/help/apiManual/)に載っている API 名から機械的に導出します**。読みやすさを基準に選びません。理由は3つあります。

- API 名は外部にある唯一の安定した共有語彙です。利用者が読むのは MLIT のマニュアルであって、このライブラリのソースではありません。マニュアルの API 一覧を見ている人が対応するメソッドを推測できる状態に価値があります
- 公開APIは35本あります。読みやすさを基準にすると35回の裁量判断が必要で、必ず途中でぶれます
- API 側が改称したとき、追随すべきかの判断がつきます

### 導出手順

1. API 名から始める
2. **出典を落とす。** 国土数値情報、都市計画決定GISデータ、国土地理院GISデータ、国土調査、国土交通省都市局は、誰が公開したデータかを示すもので、何のデータかを示していない
3. **主題を言い換えただけの括弧を落とす。** 不動産価格（取引価格・成約価格）の括弧は 不動産価格 の内訳なので落とす
4. **括弧の中身がデータセット名なら残す。** 出典が主題の位置に来ている場合（手順2で頭を落とした場合）はこちら。国土数値情報（駅別乗降客数）→ 駅別乗降客数
5. **括弧の中身がデータの限定なら残す。** 洪水浸水想定区域（想定最大規模）→ `expected_flood_inundation_areas_at_maximum_scale`。同名のデータのうちどれかを絞る語なので、落とすと何が返るか名前から分からなくなります。**何が返らないかを docstring に書いてください。** XKT026 なら 計画規模 の方です
6. **定型辞を落とす。** 情報、取得、一覧、API、マップ。マップ を落とすのは、返るのが地図ではなく地物だからです。XKT020 の原典データ名は 大規模盛土造成地**データ** で、土地白書の英語版も `large-scale developed embankment` を対象、`map of ...` を公表物として書き分けています
7. **引数で表現されている限定を落とす。** 都道府県内市区町村一覧 の 都道府県内 は `area` 引数が表すので落とす。手順5との違いは引数の有無です。XKT026 に 想定最大規模 を選ぶ引数はないので、名前でしか区別できません
8. **トップレベルの「・」は `and` として残す。** 地価公示・地価調査 はどちらも独立したデータセットなので両方残す。手順3の括弧内の「・」とは違う。共通する語をまとめるかどうかは典拠を見て決めます
   - **典拠に並列形があればそのまま使う。** 防火・準防火地域 は建築基準法第5節の節名が `Fire Prevention Districts and Quasi-fire Prevention Districts` で、日本語が1回しか書いていない「地域」を2回書いています。`Fire Prevention District` が定義語なので、分解せず保ちます
   - **典拠に並列形がなければ共通部分をまとめてよい。** 地価公示・地価調査 は並列形の公式訳がなく、組織名の完全形から `land_market_value_publication_and_research` を導いています
9. **「ポイント (点)」は `_point` として残す。** XPT001 と XPT002 だけが持つ
10. 残った語を [GLOSSARY.md](GLOSSARY.md) で訳す
11. **同じ語が2回出てきたら、訳は1回でよい。** 洪水浸水想定区域（想定最大規模）は 想定 を2回含みますが `expected` は1回です。手順8の「典拠に並列形がなければまとめてよい」と同じ扱いで、doubled form に典拠がないためです
12. `get_` を付ける

### 長さは基準にしません

手順の結果が長くても短縮しません。短縮するかを毎回判断すると、判断のぶれが名前のぶれになります。`get_land_market_value_publication_and_research_point` は規則を守った結果として正しい名前です。

### 単数・複数

- **メソッド名**は返り値に合わせます。一覧が返るなら複数（`get_municipalities`）
- **enum メンバー**は単数です（`RESIDENTIAL_LAND`、`LAND_AND_BUILDING`）

**API 名が数えられない語なら単数のままにします。** `get_expected_tsunami_inundation`（XKT028）はフィーチャを複数返しますが、津波浸水想定 は区域の名前ではなく想定そのものの名前なので複数形にしません。返り値に合わせる規則より API 名が優先します。

### 引数名は API のパラメータ名を snake_case にしただけにします

`administrativeAreaCode` → `administrative_area_code`、`welfareFacilityMiddleClassCode` → `welfare_facility_middle_class_code` です。メソッド名と違って導出手順はありません。**API の綴りを直しません。** XST001 の `disastertype_code` は `disaster` の後にアンダースコアが入らないままです。

**同じコード表でも API の綴りが違えば引数名も分けます。** 市区町村コードは XIT001 では `city`、XKT004 などでは `administrativeAreaCode` です。同じ5桁のコード表ですが、片方に寄せると寄せなかった側の引数名が、利用者がマニュアルで読むパラメータ名と一致しなくなります。docstring で同じコード表だと伝えます。

例外は Python の予約語と衝突する場合です。XPT001 の `from` / `to` は `period_from` / `period_to` にしています。

### 「等」は `_ETC` にします

`LandTypeCode.PRE_OWNED_CONDOMINIUMS_ETC`（中古マンション等）が先例です。メソッド名でも同じで、保育園・幼稚園**等** → `get_nursery_schools_and_kindergartens_etc`。

### API 名と公定訳が食い違うときは API 名に従います

XKT021 のデータセット名は 地すべり防止**地区** ですが、実体は地すべり等防止法3条の 地すべり防止**区域** で、公定訳は `landslide prevention area` です。メソッド名は `get_landslide_prevention_districts` にしています。

利用者が読むのは MLIT のマニュアルなので、マニュアルの語からメソッドに辿り着ける方を採ります。**食い違いは docstring に1文で書いてください。** 書かないと、公定訳を知っている利用者が `districts` を訳し間違いと受け取ります。

### 導出例

規則が非タイル系とポイント系の6本を再現することを確認済みです。

| ID | API 名 | 落とした部分 | メソッド名 |
|---|---|---|---|
| XIT001 | 不動産価格（取引価格・成約価格）情報取得API | 括弧（手順3）、情報取得 | `get_real_estate_prices` |
| XIT002 | 都道府県内市区町村一覧取得API | 都道府県内（手順7）、一覧取得 | `get_municipalities` |
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

**単数化しません。** 1フィーチャを表す型なので意味的には単数が正しいのですが、`get_nursery_schools_and_kindergartens_etc` のような並列名を単数化すると `and` を `or` に変えるかどうかから判断が始まります。[長さは基準にしません](#長さは基準にしません)と同じ理由で、裁量が入る余地を作らない方を採ります。接尾辞が「1件分」を担っています。

この対応は `tests/test_types.py` が実行時に検証します。メソッドを追加して型を付け忘れる、あるいは隣のエンドポイントの型を貼ってしまう、というのはどちらも `ruff` と `ty` と `test_client.py` を通ってしまうためです。

## enum

### enum にするか `Literal` にするか

**コードそれ自体に意味が読み取れないものは enum にします。** `"02"` は 成約価格情報 を意味しますが、呼び出し側からは何も読み取れません。

**値に意味が読み取れるものは `Literal` のままにします。** `quarter: Literal[1, 2, 3, 4]`、`language: Literal["ja", "en"]` はそのままで十分です。

`StrEnum` を使います。実行時は文字列としても動くので、型チェックだけが新しい制約になります。

### enum にするか `str` にするか

コード表が enum になる条件は2つあり、両方必要です。

- **数えられる規模である。** `UseDivision` は8件、`LandTypeCode` は5件です。都道府県コード（47件）と市区町村コード（約1900件）は `area`、`city`、`administrative_area_code` として `str` のままにし、docstring にコード表の URL を置いています
- **全メンバーに典拠のある訳語がある。** 一部しか訳せないコード表は enum にしません。呼び出し側が同じ引数に enum メンバーと生の文字列を混ぜることになり、enum を作った意味がなくなります

2つ目に当たる例が2つあります。**福祉施設大分類コード（XKT011）** は7件で規模は足りていますが、うち2件に公表された英訳がありません。**災害分類コード（XST001）** は12件のうち4件（河道閉塞、津波高、浸水域、地震土砂災害）に典拠がありません。

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

[GLOSSARY.md](GLOSSARY.md) で訳し、日本語のコード表記をコメントで添えます。

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

各エンドポイントのマニュアル個別ページに `＜出力＞` の表があり、その **タグ名** の列が JSON のキーです。**整えずにそのまま写します。** GLOSSARY.md は使いません。ここは訳す場所ではないからです。

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
| `proximity_to_transportation_facilitites` が本当に綴り違いのままか | `get_land_market_value_publication_and_research_point` | 型と、`types.py` / このファイル / README の3箇所の記述を直す |
| `DataResponse` の封筒が `status` / `data` か、`status` が `"OK"` 以外を取るか | 非タイル系のどれか | マニュアルに記載がない部分。取らないなら `Literal["OK"]` に締められる |
| 整数型・実数型・真偽型のフィールドが `null` で来ることがあるか | 全般。XKT013 の `GASSAN20XX` はデータ例が空 | `\| None` へ広げる。**読み取り側にとって破壊的** なので、ここだけは実物を見ないと動かせない |
| キーが省略されるのか空文字で来るのか | `get_real_estate_prices` で農地・林地と中古マンションを比べる | 常に来るキーは `total=False` から必須に締められる（非破壊） |
| エンドポイントごとのジオメトリ種別 | タイル系全般。XKT029 は「ポリゴンとライン混在」とマニュアルが明記 | `Geometry` の合併型をエンドポイント別に狭められる |
| XKT013 のキーに入る年 | `get_population_projections_in_250m_grid_squares` | 年が固定なら `dict[str, Any]` を `TypedDict` にできる |
| XKT007 の2つの形が共有フィールドの値で判別できるか | `get_nursery_schools_and_kindergartens_etc` | 判別できるなら union + 絞り込みにできる |

締める方向（`total=False` → 必須、合併型を狭める、`Literal` にする）は読み取り側にとって非破壊です。広げる方向（`None` を足す）は破壊的なので、`feat!:` が必要になります。

## API の癖

同じコード表や同じ種類の値でも、エンドポイントごとに扱いが違います。**どちらも間違えてもリクエストは飛ばないか、静かに違う結果が返ります。**

### ズーム範囲は必ずマニュアルの個別ページで確認してください

`/help/apiManual/{endpoint_id}/`（小文字）がサーバ描画されており、`＜パラメータ＞` の表に `z` の行があります。「11（市）～15（詳細）で指定可能」のように書かれています。

**エンドポイントごとに違います。** 9-15、11-15、13-15、14-15 の4種類があります。既定の `range(11, 16)` から外れるものは `_get_tile` に `zoom_levels` を渡してください。

範囲を間違えても**リクエストは飛びません**。狭すぎればAPIが対応する縮尺を手元で拒否し、広すぎればAPIがエラーを返します。前者はレスポンスに何も現れないので、記載を必ず確認してください。

### コードの桁数もエンドポイントごとに確認してください

都道府県コードは XKT019 が `9`（先頭の0を除く）、XKT021 と XKT022 が `09`（2桁）です。引数名も型も同じなので、コードからは区別が付きません。

XKT019 側は先頭0付きを `ValueError` で断っています（`_join_unpadded_codes`）。ズーム範囲と同じで、マニュアルが定める形式外の値は手元で断る扱いです。**これをライブラリ全体の規則にしないでください。** XKT021 が求める形式を拒否することになります。

**どちらの形式かを docstring に書いてください。** 引数名も型も同じなので、書かなければ利用者はマニュアルを開くまで分かりません。
