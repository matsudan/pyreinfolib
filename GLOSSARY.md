# 用語集

メソッド名・引数名・enum 名に使う訳語と、その典拠です。導出の手順は [CONTRIBUTING.md の「命名」](CONTRIBUTING.md#命名)にあります。

**訳語を発明しないでください。** ここにない語は、下記の典拠を当たってから決めてください。

## 典拠の優先順位

1. **[日本法令外国語訳データベースシステム](https://www.japaneselawtranslation.go.jp/)**（法務省）。必要な語の多くは法令用語で、政府公式訳が条文単位で日英対応しています
2. **[地価に関する国際的な情報発信の強化に向けた検討業務 調査報告書](https://www.mlit.go.jp/common/000214955.pdf)**（国土交通省 土地・建設産業局、平成24年3月）。地価公示・鑑定評価の語彙について MLIT が統一的な英訳を提示する目的で作った用語集です。地価関連語は法令訳DBより詳しく、DBの訳に対する注記もあります
3. **所管省庁の英語版資料**。法令用語でないもの（統計用語、データセット名）。[土地白書の英語版](https://www.mlit.go.jp/totikensangyo/content/001428844.pdf)は宅地・防災系が載っていて当たり所です
4. **[不動産情報ライブラリの地図の英語ラベル](#不動産情報ライブラリの地図の英語ラベル)**。データセット名がここで確定することがありますが、質にばらつきがあるので上位3つの下に置きます
5. **既にこのライブラリで使っている訳語**

## 典拠の調べ方

### 法令訳DB

法令名から翻訳IDを引いて `https://www.japaneselawtranslation.go.jp/ja/laws/view/{id}/je` を開きます。対訳ページは日本語と英語の div が交互に並ぶので、定義条（「この法律において『○○』とは」）を見ると定義語の訳が取れます。

**辞書検索（標準対訳辞書）では引けません。** 一般的な法令用語しか収録しておらず、施設名や区域名は入っていません。

### 未翻訳の法令の英語題名は、翻訳済みの法令の引用から取れます

収録されていない法令でも、収録されている法令が条文中で引用していれば公式の英語題名が判明します。**照合には法令番号を使ってください。** 1つの条文が複数の法令を引用していることがあり、条文単位で対応させると別の法令の題名を拾います。実際に 都市再生特別措置法 を `Urban Railway Promotion Act`（都市鉄道等利便増進法）と誤って拾いました。

| 法令 | 英語題名 | 引用元 |
|---|---|---|
| 水防法（昭和24年法律第193号） | Flood Prevention Act | 災害対策基本法 |
| 地すべり等防止法（昭和33年法律第30号） | Landslide Prevention Act | 災害対策基本法、都市計画法 |
| 土砂災害防止法（平成12年法律第57号） | Act for Promotion of Measures to Prevent Sediment Disasters in Sediment Disaster Alert Areas | 都市計画法33条1項8号 |
| 津波防災地域づくり法（平成23年法律第123号） | Act on Regional Development for Tsunami Disaster Prevention | 建築基準法 |
| 都市再生特別措置法（平成14年法律第22号） | Act on Special Measures Concerning Urban Renaissance | 都市計画法 |
| 海岸法 | Coast Act | 災害対策基本法 |

**都市計画法33条1項8号は特に当たり所です。** 開発許可の基準として、災害危険区域・地すべり防止区域・土砂災害特別警戒区域を並べて引用しています。

### 文脈検索は JSONP を直接叩けます

法令検索が法令名で引くのに対し、文脈検索（KWIC）は**訳文の中の語**で引けます。翻訳済み法令を網羅するので、手元にダウンロードしていない法令にも届きます。浸水・高潮・最大規模・急傾斜地はこれで見つかりました。

```
https://www.japaneselawtranslation.go.jp/webkoyori/koyori-json.cgi?q=<語>&callback=cb&title_lang_code=ja&maxshow=30
```

JSONP なので `cb( ... )` を剥がします。`ret` が `[原文側の行, 訳文側の行]` の2本で、同じ添字が対応します。

**`kwd_lang` は付けないでください。** 付けると 0 件になります。日本語でも英語でも `q` に直接入れれば引けます。

### 施設系は法令典拠が不要です

XKT004〜018 の施設系（小学校区、学校、保育園・幼稚園等、医療機関、福祉施設、図書館、市区町村役場及び集会施設等）は一般語です。国土数値情報は英語のデータセット名を公開していないため、当たる先もありません。

## 優先順位のどこにも訳語がないとき

根拠法が法令訳DBに未収録で、所管省庁の英語資料も旧称のまま揺れている語があります。**どの段階でも訳語を発明しないでください。** 次の順に試します。

1. **その語を名前にしない設計を選ぶ。** コード表なら `str` のままにできます（[enum にするか `str` にするか](CONTRIBUTING.md#enum-にするか-str-にするか)）。メソッド名は避けようがないので、この手は使えません
2. **典拠のある部品から合成する。** 根拠法自身の造語パターンに従ってください。部品のどちらかに典拠がなければ使えません。[都市計画道路](#都市計画道路は合成した訳語です)と[浸水想定区域](#浸水想定区域そのものの公定訳はありません)がこれです
3. **二次資料で定着している訳語を採る。** 政府資料が原典として挙げられていて、かつ競合候補がない場合に限ります。[立地適正化計画](#立地適正化計画は二次資料で決めています)だけがこれです
4. **実装を保留する。** 上のどれも使えないとき

**どの段階で決めたか、そして空振りした当たり先を書いてください。** 原典が後から出てきたときに見直せます。当たり先を書き残さないと、次の人が同じ検索を繰り返します。

**合成（手順2）の前に手順3の当たり先を尽くしてください。** 部品が正しくても構造を間違えられます。大規模盛土造成地 は `造成 = development` を正しく取った上で「地」を主要語と解釈しかけましたが、公定訳は 盛土 を主要語にした `large-scale developed embankment` でした。

## 不動産情報ライブラリの地図の英語ラベル

[地図](https://www.reinfolib.mlit.go.jp/map/)の英語版に、レイヤーごとの日英対が**73組**入っています。APIを公開しているのと同じシステムなので、データセット名の典拠としては直接的です。

`/map/` の JS チャンクの中にあります。`Liquefaction` などの英語ラベルで全チャンクを grep して、`キー:{header:"ラベル"}` の形を拾うと日本語版と英語版が別オブジェクトで取れます。キーで突き合わせます。

**優先順位は法令の公定訳とMLIT用語集の下です。** ラベルの質が場所によって落ちます。

- 津波浸水想定 → `Tsunami flooding forecast`。法定の想定であって予報ではありません
- 大規模盛土造成地マップ → `Large fill site map`。土地白書の `large-scale developed embankment` と、API自身の出力フィールド `embankment_classification` の両方に反します
- 防火・準防火地域 → `Fire prevention zone`。建築基準法の公定訳は `district` です
- 洪水浸水想定区域 → `Potential flood inundation area`、高潮浸水想定区域 → `Potential storm surge flood area`。同じ 浸水 が inundation と flood に割れています
- 地価公示 → `Land price public notices`。MLIT用語集201が「通達と紛らわしい」として却下した語です

**それでも15件のメソッド名を裏付けました。** 特に根拠が弱かった3件が確認できています。立地適正化計画（二次資料のみ）、都市計画道路（合成）、地すべり防止地区（公定訳の `area` に逆らってAPI名の `地区` を採用）。3つ目は[API 名と公定訳が食い違うときは API 名に従います](CONTRIBUTING.md#api-名と公定訳が食い違うときは-api-名に従います)の裏付けです。

**相違があったときは、根拠の強い方を採ります。** こちらが法令やMLIT用語集を典拠にしているならそのまま、こちらが合成や推測で決めていたなら地図のラベルに寄せます。どちらを採ったかと理由をここに残してください。

寄せたのは2件で、どちらもこちらの名前にどの語の典拠もありませんでした。

| 日本語 | 変更前 | 変更後 |
|---|---|---|
| 市区町村役場及び集会施設等 | `..._and_public_meeting_facilities_etc` | `..._and_meeting_facilities_etc` |
| 将来推計人口250mメッシュ | `get_future_population_estimates_by_250m_mesh` | `get_population_projections_in_250m_grid_squares` |

1件目の `public` は日本語にない語をこちらが足していたもので、訳語の選択ではなく誤りでした。

2件目は調べ直したところ3語すべてに作成機関の裏付けがありました。将来推計人口 は[国立社会保障・人口問題研究所](https://www.ipss.go.jp/index-e.asp)が `Population Projections for Japan` として公表しています。`将来` が落ちるのは `projections` が将来を含意するためで、同研究所も落としています。メッシュ は[総務省統計局](https://www.stat.go.jp/english/data/mesh/index.html)が `Grid Square Statistics` を使っています。

**`250m` は `250-meter` にしませんでした。** 地図のラベルは `250-meter` ですが、API名が 250m で、名前はAPI名から導出します。`250-meter` は散文の表記慣習と判断しました。

## 確定した訳語

| 日本語 | English | 典拠 |
|---|---|---|
| 用途地域 | use district | 建築基準法48条（[laws/view/4024](https://www.japaneselawtranslation.go.jp/ja/laws/view/4024/je)）、都市計画法8条3項・9条13項 |
| 防火地域 | fire prevention district | 建築基準法53条3項 |
| 準防火地域 | quasi-fire prevention district | 建築基準法53条3項 |
| 高度利用地区 | high-level use district | 建築基準法59条 |
| 高度地区 | height control district | 建築基準法58条 |
| 都市計画区域 | city planning area | 都市計画法5条（[laws/view/3841](https://www.japaneselawtranslation.go.jp/ja/laws/view/3841/je)） |
| 区域区分 | area classification | 都市計画法7条 |
| 市街化区域 | urbanization promotion area | 都市計画法7条 |
| 市街化調整区域 | urbanization control area | 都市計画法7条 |
| 地区計画 | district plan | 都市計画法12条の4 |
| 都市計画施設 | city planning facility | 都市計画法4条6項 |
| 都市計画事業 | city planning project | 都市計画法4条15項 |
| 都市施設 | urban facility | 都市計画法4条5項 |
| 都市計画道路 | city planning road | 都市計画法に定義なし。[合成](#都市計画道路は合成した訳語です) |
| 立地適正化計画 | location normalization plan | [二次資料のみ](#立地適正化計画は二次資料で決めています) |
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
| 災害危険区域 | disaster risk area | 建築基準法39条 |
| 地すべり防止区域 | landslide prevention area | 都市計画法33条1項8号 |
| 土砂災害警戒区域 | sediment disaster alert area | 土砂災害防止法の英語題名。都市計画法33条1項8号で引用 |
| 土砂災害特別警戒区域 | sediment disaster special alert area | 都市計画法33条1項8号 |
| 急傾斜地崩壊危険区域 | steep slope failure hazard area | [公定訳が2つあります](#急傾斜地崩壊危険区域には公定訳が2つあります) |
| 浸水 | inundation | 津波対策の推進に関する法律6条・8条・10条・16条（[laws/view/4648](https://www.japaneselawtranslation.go.jp/ja/laws/view/4648/je)） |
| 浸水すると想定される範囲 | the expected ... inundation zone | 同法8条2項 |
| 想定される | expected | 同法、港湾の施設の技術上の基準を定める省令1条1項5号（[laws/view/3891](https://www.japaneselawtranslation.go.jp/ja/laws/view/3891/je)） |
| 最大規模 | the maximum scale | 港湾の施設の技術上の基準を定める省令1条1項5号 |
| 洪水 | flood | 災害対策基本法2条1号 |
| 高潮 | storm surge | [気象業務法17条・18条・24条、海洋基本法25条2項](#高潮は-storm-surge-です) |
| 津波 | tsunami | 津波対策の推進に関する法律 |
| 液状化 | liquefaction | 津波対策の推進に関する法律10条1項、住宅の品質確保の促進等に関する法律施行規則1条1項、東日本大震災復興特別区域法46条2項 |
| 盛土 | embankment | 環境影響評価法施行令 別表、航空法施行規則77条1項 |
| 大規模 | large scale | 文脈検索で複数条文 |
| 大規模盛土造成地 | large-scale developed embankment | [土地白書 平成30年度 英語版](https://www.mlit.go.jp/totikensangyo/content/001428844.pdf) p43 |
| 大規模盛土造成地マップ | map of large-scale developed embankments | 同 p43 |
| 宅地造成 | residential land development | 宅地造成等規制法の英語題名（建築基準法88条4項が引用）、土地白書英語版 p43 |
| 宅地の造成 | development of residential land | 土地収用法86条、租税特別措置法62条の3第4項 |
| 人口集中地区 | densely inhabited district | [総務省統計局 英語ページ](https://www.stat.go.jp/english/data/jyutaku/25021.html) |
| 将来推計人口 | population projections | [国立社会保障・人口問題研究所](https://www.ipss.go.jp/index-e.asp) |
| メッシュ | grid square | [総務省統計局](https://www.stat.go.jp/english/data/mesh/index.html) |
| 地形区分に基づく液状化の発生傾向図 | liquefaction tendency based on topographical classification | [地図の英語ラベル](#不動産情報ライブラリの地図の英語ラベル) |
| 災害履歴 | disaster history | 同 |
| 国土調査 | National Land Survey | 土地白書英語版 p70 |
| 砂防法 | Erosion Control Act | 自然環境保全法施行規則19条1項 |
| 河川法 | River Act | 同条 |
| 海岸保全区域 | coastal preservation zone | 同条 |

用途地域の内訳（13種）も建築基準法から取れます。第一種低層住居専用地域 = category 1 low-rise exclusive residential district、準住居地域 = quasi-residential district、田園住居地域 = countryside residential district、準工業地域 = quasi-industrial district、工業専用地域 = exclusive industrial district、ほか。

## 個別の判断の記録

### 急傾斜地崩壊危険区域には公定訳が2つあります

`steep slope failure hazard area` を採ります。絶滅のおそれのある野生動植物の種の保存に関する法律施行規則5条1項・25条1項・50条2項と鳥獣保護管理法施行規則38条1項の**4条文**で使われています。もう一方の `steep slope collapse risk area`（自然環境保全法施行規則19条1項）は1条文だけです。[国土交通省の土砂災害の技術資料](https://www.mlit.go.jp/sogoseisaku/inter/keizai/gijyutu/pdf/sediment_e_03.pdf)も `Slope Failure Hazard Areas` を使っています。

地図の英語ラベルは `Steep slope collapse risk area` で、少数派の側と一致します。優先順位1の中で条文数の多い方を採る判断を維持しています。

### 高潮は storm surge です

建築基準法39条が災害危険区域の指定理由を列挙する文で `high tide` を使っていますが、気象用語としては `storm surge` が標準で、気象業務法と海洋基本法の2法が使っています。国土技術政策総合研究所の英語資料もこのデータセットを `storm surge inundation area` と呼んでいます。

### 浸水想定区域そのものの公定訳はありません

水防法が法令訳DBに未収録で、`浸水想定区域` も `洪水浸水想定区域` も文脈検索で0件でした。部品から[手順2](#優先順位のどこにも訳語がないとき)で合成しています。並びは津波対策法8条2項の `the expected tsunami inundation zone` に従い、`expected` + 災害 + `inundation` + 区域語 の順です。

XKT026・027・028 の3本で語を揃えています。地図のラベルは `Potential` を使い、しかも 浸水 を inundation と flood に割っているため、一貫性のあるこちらを維持しています。

### 都市計画道路は合成した訳語です

都市計画法は 都市計画道路 を定義しておらず、都市計画施設として定められた道路の通称です。同法の訳が 都市計画施設 を `city planning facility`、都市計画事業 を `city planning project` としているので、`city planning` + 名詞 は同法自身の造語パターンです。道路 は11条1項1号の都市施設の一覧で `roads` です。12条の11には `roads that are city planning facilities` という言い方も出てきます。

地図のラベルも `City planning road` で一致しました。

### 立地適正化計画は二次資料で決めています

[手順3](#優先順位のどこにも訳語がないとき)に当たる唯一の語です。`適正化` 単体の訳語典拠がないため、手順2の合成も使えませんでした。

**採った根拠**

- [ジャパンシステムのコラム](https://www.japan-systems.co.jp/column/%E9%83%BD%E5%B8%82%E8%A8%88%E7%94%BB%E3%81%A8%E5%85%AC%E5%85%B1%E6%96%BD%E8%A8%AD%E3%83%9E%E3%83%8D%E3%82%B8%E3%83%A1%E3%83%B3%E3%83%88%E3%82%B3%E3%83%A9%E3%83%A0%E2%91%A1%E3%80%8C%E7%AB%8B%E5%9C%B0/)（2016年、首都大学東京の都市計画研究者）が「国交省資料によると英語では Location Normalization Plan と呼ばれる」と書き、脚注で `Major Efforts Made in the Fields of National Land and Transportation` という MLIT の英語ページを原典に挙げています
- 査読文献で定着しています。[Sustainability 2020](https://www.mdpi.com/2071-1050/12/3/989/xml)、[Sustainability 2021](https://www.mdpi.com/2071-1050/13/23/13107/xml)（`the Location Normalization Plan (LNP)` と略称まで定義）
- 競合候補がありません。政府資料にも査読文献にも別の訳は見つかりませんでした
- 後から地図のラベルも `Location normalization plan` で一致しました

**空振りした当たり先**（原典の MLIT ページには到達できていません）

MLIT 英語トップ（現行と2016年9月3日の Wayback スナップショット）、City Bureau 英語索引 `/en/toshi/index.html`、同索引がリンクする `/common/000996976.pdf`、`/en/toshi/city_plan/compactcity_network.html` と配下の `/en/` PDF（中身は日本語）、英訳パンフ `/common/001048781.pdf`（低炭素まちづくり計画の資料）、Wayback CDX の `mlit.go.jp/en/*effort*`（0件）。

なお City Bureau 英語索引は `Act on Special Measures Concerning Urban Renaissance` と `City Planning Act` を掲げていて、法令訳DBの引用から取った題名と一致します。法令名の方は二重に典拠が付いています。

### 地価公示と地価調査

**`public notice` は使いません。** MLIT 用語集 201 に「Public notice という訳もあるようだが、通達と紛らわしい」と、退けた理由が明記されています。英語ページも `Land price public notice system` を「以前の呼称」としています。地図のラベルは `Land price public notices` ですが、用語集が明示的に却下した語なので採りません。

**公示と調査は Publication と Research で区別します。** 用語集 259 の 都道府県地価調査 の訳は説明的な文章で、地価公示と同じ `publication` を使っています。そのまま識別子にすると2つのデータセットがほぼ同名になるため、組織名（地価公示室 / 地価調査課）の固有名詞形から採ります。

**括弧は外します。** MLIT 用語集は `Land （Market） Value` と括弧付きで記載していますが、識別子に括弧は使えず、[MLIT の英語ページ](https://www.mlit.go.jp/en/totikensangyo/totikensangyo_fr4_000001.html)が括弧なしで運用しています。

### 用途地域と用途区分は別の語彙です

鑑定評価書API（XCT001）の `division`（`UseDivision`）は**地価公示の用途区分**で、都市計画法の**用途地域**ではありません。

- 準工業**地**（`QUASI_INDUSTRIAL_LAND`）≠ 準工業**地域**（quasi-industrial district）
- 現況林地、宅地見込地 も用途地域には存在しません

用語集を機械的に当てて `UseDivision` を district に「直す」のは誤りです。

## 未確定

**現在ありません。** 公開API35本すべての訳語が確定しています。新しいエンドポイントやコード表が増えて、典拠を当たっても決まらない語が出たらここに書いてください。
