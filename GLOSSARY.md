# 用語集

メソッド名・引数名・enum 名に使う訳語と典拠です。命名の手順は [CONTRIBUTING.md](CONTRIBUTING.md#命名) にあります。

ここにない語は、下記の典拠を順に当たって決めてください。

## 典拠の優先順位

1. **[日本法令外国語訳データベースシステム](https://www.japaneselawtranslation.go.jp/)**（法務省）。政府公式訳が条文単位で日英対応しています
2. **[地価に関する国際的な情報発信の強化に向けた検討業務 調査報告書](https://www.mlit.go.jp/common/000214955.pdf)**（国土交通省、以下「MLIT 用語集」）。地価公示・鑑定評価の語彙は法令訳DBより詳しくなっています
3. **所管省庁の英語版資料**。法令用語でない語（統計用語、データセット名）はここです。[土地白書の英語版](https://www.mlit.go.jp/totikensangyo/content/001428844.pdf)は宅地・防災系が載っています
4. **[不動産情報ライブラリの地図の英語ラベル](https://www.reinfolib.mlit.go.jp/map/)**。質にばらつきがあるので上位3つの下に置きます。ラベルは `/map/` の JS チャンクにあります
5. **既にこのライブラリで使っている訳語**

相違があったときは根拠の強い方を採ります。こちらが合成や推測で決めた語なら地図のラベルに寄せ、法令や MLIT 用語集が典拠なら変えません。

## 典拠の調べ方

- **法令訳DB:** 法令名から翻訳IDを引き、`https://www.japaneselawtranslation.go.jp/ja/laws/view/{id}/je` を開きます。定義条（「この法律において『○○』とは」）で定義語の訳が取れます。標準対訳辞書は一般的な法令用語しかなく、施設名や区域名は引けません
- **文脈検索（KWIC）:** 訳文中の語で引けます。未ダウンロードの法令にも届きます

  ```
  https://www.japaneselawtranslation.go.jp/webkoyori/koyori-json.cgi?q=<語>&callback=cb&title_lang_code=ja&maxshow=30
  ```

  JSONP なので `cb( ... )` を剥がします。`ret` は `[原文側の行, 訳文側の行]` で、同じ添字が対応します。`kwd_lang` は付けないでください（0件になります）
- **未収録の法令の英語題名:** 収録済みの法令が引用していれば分かります。**照合には法令番号を使ってください。** 条文単位で対応させると別の法令の題名を拾います
- **施設系（XKT004〜018）:** 一般語なので法令典拠は不要です

## 典拠のどこにも訳語がないとき

次の順に試します。**どの段階で決めたか、空振りした当たり先も残してください。**

1. **その語を名前にしない。** コード表なら `str` のままにできます（[enum / `Literal` / `str`](CONTRIBUTING.md#enum)）。メソッド名では使えません
2. **典拠のある部品から合成する。** 根拠法自身の造語パターンに従い、部品のどちらかに典拠がなければ使いません。例: 都市計画道路、浸水想定区域
3. **二次資料で定着している訳語を採る。** 政府資料が原典として挙げられ、競合候補がない場合に限ります。例: 立地適正化計画
4. **実装を保留する。**

合成の前に手順3の当たり先を尽くしてください。部品が正しくても構造を間違えることがあります（大規模盛土造成地の公定訳は 盛土 が主要語）。

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
| 都市計画道路 | city planning road | 都市計画法に定義なし。[合成](#個別の判断) |
| 立地適正化計画 | location normalization plan | [二次資料のみ](#個別の判断) |
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
| 急傾斜地崩壊危険区域 | steep slope failure hazard area | [公定訳が2つあります](#個別の判断) |
| 浸水 | inundation | 津波対策の推進に関する法律6条・8条・10条・16条（[laws/view/4648](https://www.japaneselawtranslation.go.jp/ja/laws/view/4648/je)） |
| 浸水すると想定される範囲 | the expected ... inundation zone | 同法8条2項 |
| 想定される | expected | 同法、港湾の施設の技術上の基準を定める省令1条1項5号（[laws/view/3891](https://www.japaneselawtranslation.go.jp/ja/laws/view/3891/je)） |
| 最大規模 | the maximum scale | 港湾の施設の技術上の基準を定める省令1条1項5号 |
| 洪水 | flood | 災害対策基本法2条1号 |
| 高潮 | storm surge | 気象業務法17条・18条・24条、海洋基本法25条2項 |
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
| 地形区分に基づく液状化の発生傾向図 | liquefaction tendency based on topographical classification | [地図の英語ラベル](https://www.reinfolib.mlit.go.jp/map/) |
| 災害履歴 | disaster history | 同 |
| 国土調査 | National Land Survey | 土地白書英語版 p70 |
| 砂防法 | Erosion Control Act | 自然環境保全法施行規則19条1項 |
| 河川法 | River Act | 同条 |
| 海岸保全区域 | coastal preservation zone | 同条 |

用途地域の内訳も建築基準法から取れます。第一種低層住居専用地域 = category 1 low-rise exclusive residential district、準住居地域 = quasi-residential district、田園住居地域 = countryside residential district、準工業地域 = quasi-industrial district、工業専用地域 = exclusive industrial district、ほか。

## 個別の判断

**急傾斜地崩壊危険区域** は `steep slope failure hazard area` を採ります。公定訳は2つあり、こちらは4条文で使われ（絶滅のおそれのある野生動植物の種の保存に関する法律施行規則5条1項ほか、鳥獣保護管理法施行規則38条1項）、もう一方の `steep slope collapse risk area` は自然環境保全法施行規則19条1項のみです。[国土交通省の技術資料](https://www.mlit.go.jp/sogoseisaku/inter/keizai/gijyutu/pdf/sediment_e_03.pdf)も `Slope Failure Hazard Areas` です。

**高潮** は `storm surge` です。建築基準法39条は `high tide` ですが、気象業務法と海洋基本法が `storm surge` を使い、気象用語としても標準です。

**浸水想定区域**（XKT026〜028）は公定訳がありません。津波対策の推進に関する法律8条2項の `the expected tsunami inundation zone` に従い、`expected` + 災害 + `inundation` + 区域語 で合成し、3本で揃えています。地図のラベルは `Potential` を使い、浸水 を inundation と flood に割っているため採りません。

**都市計画道路** は合成です。都市計画法の `city planning facility`、`city planning project` にならって `city planning` + `road`（11条1項1号の `roads`）としています。地図のラベルも一致します。

**立地適正化計画** は二次資料のみです。`適正化` の典拠がなく、手順2の合成は使えません。[ジャパンシステムのコラム](https://www.japan-systems.co.jp/column/%E9%83%BD%E5%B8%82%E8%A8%88%E7%94%BB%E3%81%A8%E5%85%AC%E5%85%B1%E6%96%BD%E8%A8%AD%E3%83%9E%E3%83%8D%E3%82%B8%E3%83%A1%E3%83%B3%E3%83%88%E3%82%B3%E3%83%A9%E3%83%A0%E2%91%A1%E3%80%8C%E7%AB%8B%E5%9C%B0/)が MLIT 資料での呼称として `Location Normalization Plan` を挙げ、査読文献（[Sustainability 2020](https://www.mdpi.com/2071-1050/12/3/989/xml)、[2021](https://www.mdpi.com/2071-1050/13/23/13107/xml)）でも定着しています。競合候補はなく、地図のラベルとも一致します。原典の MLIT 英語ページには到達できていません。

**地価公示と地価調査**
- `public notice` は使いません。MLIT 用語集 201 が「通達と紛らわしい」として退けています。地図のラベル `Land price public notices` も採りません
- 2つは `publication` と `research` で区別します。用語集 259 の訳は説明文で同じ `publication` を使っており、そのままでは2つがほぼ同名になるため、組織名（地価公示室 / 地価調査課）から採ります
- MLIT 用語集の `Land （Market） Value` は括弧を外します。[MLIT の英語ページ](https://www.mlit.go.jp/en/totikensangyo/totikensangyo_fr4_000001.html)が括弧なしで運用しています

**将来推計人口250mメッシュ** は `get_population_projections_in_250m_grid_squares` です。`将来` は `projections` が含意します（同研究所も落としています）。`250m` は API 名に合わせ、地図のラベルの `250-meter` にはしません。

**用途地域と用途区分は別の語彙です。** XCT001 の `division`（`UseDivision`）は地価公示の用途区分で、都市計画法の用途地域ではありません。準工業**地**（`QUASI_INDUSTRIAL_LAND`）は準工業**地域**（quasi-industrial district）ではなく、現況林地・宅地見込地も用途地域にありません。用語集を当てて district に直さないでください。
