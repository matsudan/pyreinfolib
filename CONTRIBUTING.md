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

型情報を同梱しているため（[PEP 561](https://peps.python.org/pep-0561/)）、**型注釈は公開APIの一部**です。

型チェッカーは [ty](https://github.com/astral-sh/ty) です。pre-1.0 で、0.0.x 間でも診断内容を含む破壊的変更が起こりうるため、`pyproject.toml` で**バージョンを厳密に固定**しています。更新は Dependabot の PR で、差分を読んでから取り込んでください。

### `tests/typing_usage.py`

`pyreinfolib` の内部だけを検査しても、呼び出し側のエラーは見つかりません。そのため `tests/typing_usage.py` に**利用者が書くとおりのコード**を置いて型チェックの対象にしています（実行はされません）。README が推奨する書き方を追加したら、ここにも足してください。

拒否されるべきものには `# ty: ignore[...]` を付けます。拒否されなくなると、使われなかった ignore が報告されて CI が落ちます。

```python
client.get_real_estate_prices(
    year=2024,
    price_classification=LandPriceClassification.LAND_MARKET_VALUE_PUBLICATION,  # ty: ignore[invalid-argument-type]
)
```

## プルリクエスト

squash merge のみを使い、**PR のタイトルと説明文がそのまま `main` のコミットメッセージになります**。

- タイトルは [Conventional Commits](https://www.conventionalcommits.org/) 準拠で、`.github/workflows/pr-title.yml` が検証します
- release-please がタイトルからバージョンと CHANGELOG を生成します。`feat` は minor、`fix` は patch、`!` 付きは破壊的変更です（1.0 到達前は minor）
- 説明文が git 履歴に残るため、レビュー用のチェックリストや議論の経緯は書きません

### 説明文の書式

冒頭にこの変更が必要だった理由を数行書き、続けて2節に分けて箇条書きにします。

- `## Changes` — 何が変わったか。ファイル名と設定値を具体的に、1行1項目。理由は書きません
- `## Notes` — 却下した選択肢とその理由、非自明な制約。diff、コードコメント、CI の結果から分かることは書きません

### 破壊的変更

`BREAKING CHANGE:` フッタを **PR 本文**に書きます。ローカルのコミットメッセージは squash で捨てられるため届きません。移行方法はこのフッタにしか書けず、ないと CHANGELOG と GitHub Release に subject 行だけが載ります。

```
BREAKING CHANGE: `get_old_name` is now `get_new_name`. ...
```

リリース PR を直す場合は、マージ前に CHANGELOG とリリース PR 本文の両方を直してください。`main` に別のコミットが入ると release-please がどちらも作り直します。

## 命名

メソッド名・引数名・enum 名は、**[API操作説明](https://www.reinfolib.mlit.go.jp/help/apiManual/)に載っている API 名から機械的に導出します**。読みやすさは基準にしません。利用者が読むのは MLIT のマニュアルなので、マニュアルの API 名からメソッドを推測できることを優先します。

### メソッド名の導出手順

1. API 名から始める
2. **出典を落とす。** 国土数値情報、都市計画決定GISデータ、国土地理院GISデータ、国土調査、国土交通省都市局は、何のデータかを示していない
3. **主題を言い換えただけの括弧を落とす。** 不動産価格（取引価格・成約価格）の括弧は内訳なので落とす
4. **括弧の中身がデータセット名なら残す。** 手順2で頭を落とした場合がこれ。国土数値情報（駅別乗降客数）→ 駅別乗降客数
5. **括弧の中身がデータの限定なら残す。** 洪水浸水想定区域（想定最大規模）→ `expected_flood_inundation_areas_at_maximum_scale`。**何が返らないかを docstring に書く**（XKT026 なら 計画規模）
6. **定型辞を落とす。** 情報、取得、一覧、API、マップ。マップ を落とすのは、返るのが地図ではなく地物だから
7. **引数で表現されている限定を落とす。** 都道府県内市区町村一覧 の 都道府県内 は `area` 引数が表す。手順5との違いは引数の有無
8. **トップレベルの「・」は `and` として残す。** 地価公示・地価調査 は両方残す
   - 典拠に並列形があればそのまま使う（防火・準防火地域 → `Fire Prevention Districts and Quasi-fire Prevention Districts`）
   - なければ共通部分をまとめてよい（`land_market_value_publication_and_research`）
9. **「ポイント (点)」は `_point` として残す。** XPT001 と XPT002 だけ
10. 残った語を [GLOSSARY.md](GLOSSARY.md) で訳す
11. **同じ語が2回出てきたら、訳は1回でよい。** 洪水浸水想定区域（想定最大規模）の 想定 は `expected` 1回
12. `get_` を付ける

**長さは基準にしません。** 結果が長くても短縮しません。

### 単数・複数

- **メソッド名**は返り値に合わせます。一覧が返るなら複数（`get_municipalities`）
- **enum メンバー**は単数です（`RESIDENTIAL_LAND`）
- **API 名が数えられない語なら単数のままです。** 津波浸水想定 は想定そのものの名前なので、フィーチャを複数返しても `get_expected_tsunami_inundation` です

### 引数名

API のパラメータ名を snake_case にするだけです。**綴りは直しません**（XST001 の `disastertype_code`）。

- 同じコード表でも API の綴りが違えば引数名も分けます（市区町村コードは XIT001 が `city`、XKT004 などが `administrative_area_code`）。docstring で同じコード表だと伝えます
- Python の予約語と衝突する場合は例外です（XPT001 の `from` / `to` → `period_from` / `period_to`）

### 「等」は `_ETC`

`LandTypeCode.PRE_OWNED_CONDOMINIUMS_ETC`、`get_nursery_schools_and_kindergartens_etc`。

### API 名と公定訳が食い違うときは API 名に従う

XKT021 は 地すべり防止**地区** ですが、実体は 地すべり防止**区域**（`landslide prevention area`）です。メソッド名は `get_landslide_prevention_districts` にしています。マニュアルの語から辿り着けることを優先します。**食い違いは docstring に1文で書いてください。**

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
  - 数えられる規模である。都道府県コード（47件）と市区町村コード（約1900件）は `str` のままにし、docstring にコード表の URL を置く
  - 全メンバーに典拠のある訳語がある。一部しか訳せないと、同じ引数に enum と生の文字列が混ざる。福祉施設大分類コード（XKT011）は7件中2件、災害分類コード（XST001）は12件中4件が訳せないため `str` です

**迷ったら `str` から始めます。** 後から enum を足しても既存の呼び出しは壊れませんが、`str` を enum だけに絞ると壊れます。

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
- **`| None` は付けません。** 実レスポンスで `null` は確認されていません。**`| None` に広げるのは読み取り側にとって破壊的変更**なので、推測で広げず、実レスポンスを見てから決めてください
- 締める方向（必須にする、合併型を狭める、`Literal` にする）は非破壊です

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
- **XKT007** は2つの出力表を1つの型にマージしています。2つの形は共有フィールドの値ではなくキーの有無で分かれ、絞り込む目印がないため union にしません

### 新しいエンドポイントを追加するとき

1. 個別ページの `＜出力＞` 表を生 HTML から取る
2. `<MethodName>Properties`（タイル系）または `<MethodName>Item`（非タイル系）を書く。`total=False`、キーはタグ名そのまま、値型は宣言どおり、日本語の内容を行末コメントに添える
3. `<MethodName>Response` を `FeatureCollection[...]` か `DataResponse[...]` として定義する
4. メソッドの返り値に注釈を付ける
5. `tests/typing_usage.py` に読み取り側のコードを足す

### 実レスポンスとの照合

**マニュアルと実レスポンスが食い違ったら、実レスポンスを採ります。** 全35本を1回ずつ確認済みで、食い違ったのは XCT001 のキー名（109個中63個）だけです。キーが実際に欠落するのは XKT007 の学校分類系3フィールドと XKT013 の `GASSAN20XX` だけでした。

データ更新後は次の2本で再確認できます。

```shell
REINFOLIB_API_KEY=... uv run python scripts/fetch_responses.py
uv run python scripts/verify_response_types.py
```

1本目が各マニュアルページの curl 例をそのまま使ってレスポンスを `.reinfolib-responses/` に落とし、2本目が突き合わせます。2本目はネットワークも API キーも使いません。

## API の癖

エンドポイントごとに扱いが違い、**間違えてもリクエストが飛ばないか、静かに違う結果が返ります。**

- **ズーム範囲:** マニュアルの個別ページ `/help/apiManual/{endpoint_id}/`（小文字）の `＜パラメータ＞` 表にある `z` の行で確認します。9-15、11-15、13-15、14-15 の4種類があり、既定の `range(11, 16)` から外れるものは `_get_tile` に `zoom_levels` を渡します
- **都道府県コードの桁数:** XKT019 は `9`（先頭の0なし）、XKT021・XKT022 は `09`（2桁）です。XKT019 だけ先頭0付きを `ValueError` で断っています（`_join_unpadded_codes`）。**これをライブラリ全体の規則にしないでください。** どちらの形式かは docstring に書きます
