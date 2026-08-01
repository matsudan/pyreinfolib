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

公開APIは38本あります。読みやすさを基準にすると38回の裁量判断が必要で、必ず途中でぶれます。

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

## enum

### enum にするか `Literal` にするか

**コードそれ自体に意味が読み取れないものは enum にします。** `"02"` は 成約価格情報 を意味しますが、呼び出し側からは何も読み取れません。

**値に意味が読み取れるものは `Literal` のままにします。** `quarter: Literal[1, 2, 3, 4]`、`language: Literal["ja", "en"]`、`z: Literal[11, 12, 13, 14, 15]` はそのままで十分です。

`StrEnum` を使います。実行時は文字列としても動くので、型チェックだけが新しい制約になります。

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

## 用語集

### 典拠の優先順位

1. **[日本法令外国語訳データベースシステム](https://www.japaneselawtranslation.go.jp/)**（法務省）。今回必要な語の多くは法令用語で、政府公式訳が条文単位で日英対応しています
2. **[地価に関する国際的な情報発信の強化に向けた検討業務 調査報告書](https://www.mlit.go.jp/common/000214955.pdf)**（国土交通省 土地・建設産業局、平成24年3月）。地価公示・鑑定評価の語彙について、MLIT が統一的な英訳を提示する目的で作成した用語集です。地価関連語は法令訳DBより詳しく、DBの訳に対する明示的な注記もあります
3. **所管省庁の英語版資料**。法令用語でないもの（統計用語、データセット名）
4. **既にこのライブラリで使っている訳語**。1〜3で確認できないもの

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
| 立地適正化計画 | 都市再生特別措置法 | XKT003 |
| 災害危険区域 | 建築基準法39条 | XKT016 |
| 自然公園地域 | 自然公園法 | XKT019 |
| 大規模盛土造成地 | 国土交通省 | XKT020 |
| 地すべり防止区域 | 地すべり等防止法 | XKT021 |
| 急傾斜地崩壊危険区域 | 急傾斜地法 | XKT022 |
| 地形区分に基づく液状化の発生傾向図 | 国土交通省都市局 | XKT025 |
| 洪水浸水想定区域 | 水防法 | XKT026 |
| 高潮浸水想定区域 | 水防法 | XKT027 |
| 津波浸水想定 | 津波防災地域づくり法 | XKT028 |
| 土砂災害警戒区域 | 土砂災害防止法 | XKT029 |
| 都市計画道路 | 都市計画法（簡潔な定訳がなく判断が必要） | XKT030 |
| 人口集中地区 | 総務省統計局（国勢調査英語版で Densely Inhabited District / DID が定着） | XKT031 |
| 指定緊急避難場所 | 災害対策基本法 | XGT001 |
| 災害履歴 | 国土調査（土地履歴調査） | XST001 |

XKT004〜018 の施設系（小学校区、学校、保育園・幼稚園等、医療機関、福祉施設、図書館、市区町村役場及び集会施設等）は一般語なので法令典拠は不要です。
