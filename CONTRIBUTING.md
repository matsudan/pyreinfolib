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

CI でも上記のコマンドを実行します。

## 型チェック

型情報を同梱しているため（[PEP 561](https://peps.python.org/pep-0561/)）、**型注釈は公開APIの一部**です。

型チェッカーには [ty](https://github.com/astral-sh/ty) を使います。ty は pre-1.0 で、0.0.x のパッチリリース間でも診断を含む破壊的変更がありえます。そのため `pyproject.toml` で**バージョンを厳密に固定**しています。更新は Dependabot の PR で、差分を読んでから取り込んでください。

### `tests/typing_usage.py`

`pyreinfolib` の内部だけを検査しても、呼び出し側のエラーは見つかりません。そのため `tests/typing_usage.py` に**利用者が書くとおりのコード**を置いて型チェックの対象にしています（実行はされません）。README.md または README.en.md の利用例を追加・変更したら、ここにも反映してください。

拒否されるべきものには `# ty: ignore[...]` を付けます。拒否されなくなると、使われなかった ignore が報告されて CI が落ちます。

```python
client.get_real_estate_prices(
    year=2024,
    price_classification=LandPriceClassification.LAND_MARKET_VALUE_PUBLICATION,  # ty: ignore[invalid-argument-type]
)
```

## プルリクエスト

squash merge のみを使い、**PR のタイトルが `main` のコミットの subject、PR 本文が body になります**。

- タイトルは [Conventional Commits](https://www.conventionalcommits.org/) 準拠で、`.github/workflows/pr-title.yml` が検証します
- release-please がタイトルからバージョンと CHANGELOG を生成します。`feat` は minor、`fix` は patch、`!` 付きは破壊的変更です（1.0 到達前は minor）
- PR 本文は git 履歴に残るため、レビュー用のチェックリストや議論の経緯は書きません

### PR 本文の書式

冒頭に変更が必要な理由を数行書き、続けて2節に分けて箇条書きにします。

- `## Changes` — 何が変わったか。ファイル名と設定値を具体的に、1行1項目。理由は書きません
- `## Notes` — 却下した選択肢とその理由、非自明な制約。diff、コードコメント、CI の結果から分かることは書きません。訳語を追加・変更した場合は、採用した典拠と、訳語を確認できなかった調査先も記録します

### 破壊的変更

`BREAKING CHANGE:` フッタを **PR 本文**に書きます。ローカルのコミットメッセージは squash で捨てられるため届きません。移行方法はこのフッタにしか書けず、ないと CHANGELOG と GitHub Release に subject 行だけが載ります。

```
BREAKING CHANGE: `get_old_name` is now `get_new_name`. ...
```

リリース PR を直す場合は、マージ前に CHANGELOG とリリース PR 本文の両方を直してください。`main` に別のコミットが入ると release-please がどちらも作り直します。

## 命名

公開名は、**[API操作説明](https://www.reinfolib.mlit.go.jp/help/apiManual/)の記載から機械的に導出します**。メソッド名は API 名、引数名はパラメータ名、enum メンバー名は日本語のコード表記を起点にします。読みやすさや短さよりも、MLIT のマニュアルから名前を推測できることを優先します。

### メソッド名の導出手順

1. API 名から始める
2. **データ提供元を示す語を落とす。** 国土数値情報、都市計画決定GISデータ、国土地理院GISデータ、国土調査、国土交通省都市局、内閣府重要土地等調査法は、データの主題を示していない
3. **主題を言い換えただけの括弧を落とす。** 不動産価格（取引価格・成約価格）の括弧は内訳なので落とす
4. **括弧の中身がデータセット名なら残す。** 手順2で頭を落とした場合がこれ。国土数値情報（駅別乗降客数）→ 駅別乗降客数
5. **括弧の中身がデータの限定なら残す。** 洪水浸水想定区域（想定最大規模）→ `expected_flood_inundation_areas_at_maximum_scale`。**何が返らないかを docstring に書く**（XKT026 なら 計画規模）
6. **データ内容を表さない定型語を落とす。** 情報、取得、一覧、API、マップ。マップを落とすのは、返るのが地図ではなく地物だから
7. **引数で表現されている限定を落とす。** 都道府県内市区町村一覧 の 都道府県内 は `area` 引数が表す。手順5との違いは引数の有無
8. **トップレベルの「・」は `and` として残す。** 地価公示・地価調査 は両方残す
   - 典拠に並列形があればそのまま使う（防火・準防火地域 → `Fire Prevention Districts and Quasi-fire Prevention Districts`）
   - なければ共通部分をまとめてよい（`land_market_value_publication_and_research`）
9. **「ポイント (点)」は `_point` として残す。** XPT001 と XPT002 だけ
10. 残った語を [GLOSSARY.md](GLOSSARY.md) で訳す
11. **同じ語が2回出てきたら、訳は1回でよい。** 洪水浸水想定区域（想定最大規模）の 想定 は `expected` 1回
12. `get_` を付ける

### 単数・複数

- **メソッド名**は返り値に合わせます。一覧が返るなら複数（`get_municipalities`）
- **enum メンバー**は単数です（`RESIDENTIAL_LAND`）
- **API 名が数えられない語なら単数のままです。** 津波浸水想定 は想定そのものの名前なので、フィーチャを複数返しても `get_expected_tsunami_inundation` です

### 引数名

API のパラメータ名を snake_case にするだけです。**綴りは直しません**（XST001 の `disastertype_code`）。

- 同じコード表でも API の綴りが違えば引数名も分けます（市区町村コードは XIT001 が `city`、XKT004 などが `administrative_area_code`）。docstring で同じコード表だと伝えます
- Python の予約語と衝突する場合は例外です（XPT001 の `from` / `to` → `period_from` / `period_to`）

### 「等」は名前に `etc` として残す

enum メンバーでは `_ETC`、メソッドでは `_etc` とします。例は `LandTypeCode.PRE_OWNED_CONDOMINIUMS_ETC` と `get_nursery_schools_and_kindergartens_etc` です。

### API 名と公定訳が食い違うときは API 名に従う

XKT021 は 地すべり防止**地区** ですが、実体は 地すべり防止**区域**（`landslide prevention area`）です。メソッド名は `get_landslide_prevention_districts` にしています。**食い違いは docstring に1文で書いてください。**

### レスポンスの型名

`pyreinfolib.types` の型名は、メソッド名から `get_` を落として PascalCase にし、接尾辞を付けます。**単数化はしません**（並列名の単数化に裁量が入るため）。

| 接尾辞 | 対象 | 例 |
|---|---|---|
| `Response` | メソッドの返り値そのもの | `UseDistrictsResponse` |
| `Properties` | タイル系の1フィーチャの `properties` | `UseDistrictsProperties` |
| `Item` | 非タイル系の `data` の1要素 | `RealEstatePricesItem` |

この対応は `tests/test_types.py` が検証します。

## enum

### enum / `Literal` / `str`

- **コードそれ自体に意味が読み取れないものは enum** にします（`"02"` は 成約価格情報）。`StrEnum` を使います
- **値に意味が読み取れるものは `Literal`** です（`quarter: Literal[1, 2, 3, 4]`、`language: Literal["ja", "en"]`）
- **コード表が enum になるのは、次の両方を満たすときだけ**です
  - 全メンバーを列挙して保守できる規模である。都道府県コード（47件）と市区町村コード（約1900件）は `str` のままにし、docstring にコード表の URL を置く
  - 全メンバーに典拠のある訳語がある。一部しか訳せないと、同じ引数に enum と生の文字列が混ざる。福祉施設大分類コード（XKT011）は7件中2件、災害分類コード（XST001）は12件中4件が訳せないため `str` です

**迷ったら `str` から始めます。** 後から `str` を受け入れたまま enum を追加できますが、受理型を enum だけに狭めると破壊的変更になります。

### コード体系が別なら enum も分ける

API が同じパラメータ名でもコード表が違えば別の enum にします。`priceClassification` は XIT001/XPT001 が `01`/`02`、XPT002 が `0`/`1` です。まとめると取り違えても API は空の結果を返すだけで気づけません。

### メンバー名

[GLOSSARY.md](GLOSSARY.md) で訳し、**日本語のコード表記を代入の直後に docstring として置きます。** エディタがホバーと補完で表示するのはこの位置の文字列だけです。

```python
@unique
class PriceClassification(StrEnum):
    REAL_ESTATE_TRANSACTION_PRICE = "01"
    """不動産取引価格情報"""

    CONTRACT_PRICE = "02"
    """成約価格情報"""
```

日本語はコード表の表記をそのまま写します。全角と半角の括弧が混在していても揃えません（写し間違いを見つける手がかりになります）。

## レスポンスの型

`pyreinfolib.types` の `TypedDict` は**静的な主張だけで、実行時の検証はしません。**

### キー

各エンドポイントのマニュアル個別ページの `＜出力＞` 表の **タグ名** をそのまま写します。GLOSSARY.md は使いません。国土数値情報の属性コード（`A27_001`）、ローマ字（`kubun_id`）、`_ja` 接尾辞、`u_` 接頭辞、XCT001 の日本語キー（半角スペース入り）、API 自身の綴り間違い（XPT002 の `proximity_to_transportation_facilitites`）も直しません。**直すと存在しないキーになります。**

### 値の型

マニュアルの宣言に従います（文字列型 → `str`、整数型 → `int`、実数型 → `float`、真偽型 → `bool`）。**同じ名前のフィールドでも、そのページの記載どおりに書きます。** `kubun_id` は XKT001 などで整数型、XKT023・024 で文字列型です。

実数型は値が整数だと `int` で届きますが、`float` と注釈します。`int | float` にすると利用側に絞り込みを強いるためです。`float` 専用の操作（`.hex()` など）を報告するかは型チェッカー次第です。

### `total=False` と nullability

- **全フィールドを `total=False` にします。** マニュアルに必須の記載がないため、API がしていない保証をこちらが主張しないためです
- **`| None` は付けません。** 実レスポンスで `null` は確認されていません。**`| None` に広げるのは読み取り側にとって破壊的変更**なので、実レスポンスで確認してから広げてください
- 読み取り側に対して型を締める変更（必須化、合併型の縮小、`Literal` 化）は非破壊です。公開型を使って値を構築するコードへの影響は別途確認してください

### 出力表は生の HTML から取る

`＜出力＞` 表はクライアント側で描画されるため、表示テキストからの転記では空白が失われます。RSC の flight payload 内の次の形から取ってください。

```
<td id="api{ID}Output{N}Tag">タグ名</td>
<td id="api{ID}Output{N}DataType">文字列型</td>
```

1行目だけ添字がなく（`OutputTag`）、2行目以降が 0 から数えます。複数の出力形を持つエンドポイントはグループごとに接尾辞が付きます（XKT007 の2つ目の表は `apiXKT007_2Output...`）。

### 型が特殊なエンドポイント

- **XKT013** は `dict[str, Any]` です。年を含むキーをマニュアルが `20XX` で書いており、実際の年は推計次第だからです
- **XCT001** は functional syntax で書きます。109キーのうち94個が識別子になりません
- **XKT015** は年ごとの項目（`2024_passenger_count` など）だけを functional syntax で書き、`TileProperties` とともに継承します。キーが年で始まるため識別子になりません。マニュアルの表は2012年で「以下略」になるため、年の範囲は実レスポンスから取ります
- **XKT007** は2つの出力表を1つの型にマージしています。2つの形は共有フィールドの値ではなくキーの有無で分かれ、絞り込む目印がないため union にしません

### 新しいエンドポイントを追加するとき

1. 個別ページの `＜出力＞` 表を生 HTML から取る
2. `<MethodName>Properties`（タイル系）または `<MethodName>Item`（非タイル系）を書く。`total=False`、キーはタグ名そのまま、値型は宣言どおり、日本語の内容を行末コメントに添える
3. `<MethodName>Response` を `FeatureCollection[...]` か `DataResponse[...]` として定義する
4. メソッドの返り値に注釈を付ける
5. `tests/typing_usage.py` に読み取り側のコードを足す

### 実レスポンスとの照合

**マニュアルと実レスポンスが食い違ったら、実レスポンスを採ります。** 差異の理由は、該当する型のコメントに記録します。

データ更新後は次の2本で再確認できます。

```shell
REINFOLIB_API_KEY=... uv run python scripts/fetch_responses.py
uv run python scripts/verify_response_types.py
```

1本目が各マニュアルページの curl 例をそのまま使ってレスポンスを `.reinfolib-responses/` に落とし、2本目が突き合わせます。2本目はネットワークも API キーも使いません。

## エンドポイント固有の注意点

エンドポイントごとに入力の扱いが異なります。誤った入力が送信前に `ValueError` になる場合と、空の結果が返って間違いに気づけない場合があるため、次を個別に確認します。

- **ズーム範囲:** マニュアルの個別ページ `/help/apiManual/{endpoint_id}/`（小文字）の `＜パラメータ＞` 表で `z` の行を確認します。既定の `range(11, 16)` と異なる場合は、`_get_tile` に `zoom_levels` を渡します
- **都道府県コードの桁数:** XKT019 は `9`（先頭の0なし）、XKT021・XKT022 は `09`（2桁）です。XKT019 だけ先頭0付きを `ValueError` で断っています（`_join_unpadded_codes`）。**これをライブラリ全体の規則にしないでください。** どちらの形式かは docstring に書きます
