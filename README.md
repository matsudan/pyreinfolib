# pyreinfolib

国土交通省[不動産情報ライブラリ](https://www.reinfolib.mlit.go.jp/)APIサービスのPythonクライアントです。API仕様についての詳細は[API操作説明ページ](https://www.reinfolib.mlit.go.jp/help/apiManual/)をご参照ください。

## Installation

```shell
pip install pyreinfolib
```

### Supported Python Versions

Python >= 3.11

## Usage

```python
import os

from pyreinfolib import Client

client = Client(api_key=os.environ["REINFOLIB_API_KEY"])
```


## Example

### 不動産価格（取引価格・成約価格）情報

```python
client.get_real_estate_prices(year=2024, quarter=1, price_classification="01", city="13109")
```

### 鑑定評価書情報

```python
from pyreinfolib.enums import UseDivision

client.get_appraisal_reports(year=2024, area="13", division=UseDivision.INDUSTRIAL_LAND)
```

## Typing

型情報を同梱しています（[PEP 561](https://peps.python.org/pep-0561/)）。

`division`、`land_type_code`、`use_category_code` には `pyreinfolib.enums` の enum メンバーを渡してください。`StrEnum` なので実行時は文字列でも動きますが、型チェックでは拒否されます。単一のコードはリストに包む必要はありません。

## Author

@matsudan (daaamatsun@gmail.com)
