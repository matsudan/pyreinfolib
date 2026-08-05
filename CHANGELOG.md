# Changelog

## [0.8.0](https://github.com/matsudan/pyreinfolib/compare/v0.7.1...v0.8.0) (2026-08-05)


### ⚠ BREAKING CHANGES

* `get_real_estate_prices` now requires at least one of `area`, `city` and `station`. A call that passes only `year` raises `ValueError` instead of issuing a request. Pass a prefecture code, a municipality code or a station code to say where to look.

### Bug Fixes

* correct the response types against live responses ([#75](https://github.com/matsudan/pyreinfolib/issues/75)) ([12aeb5c](https://github.com/matsudan/pyreinfolib/commit/12aeb5cfc2d60109d96e9f893ee3260594a7dfb7))
* require a place on the real estate price query ([#79](https://github.com/matsudan/pyreinfolib/issues/79)) ([8c15fc5](https://github.com/matsudan/pyreinfolib/commit/8c15fc51b368a308fce37e547f8c896bf74a275c))
* validate a covering box at the call ([#81](https://github.com/matsudan/pyreinfolib/issues/81)) ([357cf1f](https://github.com/matsudan/pyreinfolib/commit/357cf1ff9a8f79e0d8dca2c47835ee8f01524c1f))


### Documentation

* cite the tile scheme the manual points at ([#82](https://github.com/matsudan/pyreinfolib/issues/82)) ([5b1fe71](https://github.com/matsudan/pyreinfolib/commit/5b1fe71cda8feb92714610a9467224aac3ac6b30))
* keep the checking record out of the docstrings ([#80](https://github.com/matsudan/pyreinfolib/issues/80)) ([b16b3f3](https://github.com/matsudan/pyreinfolib/commit/b16b3f3787377d7714d44cf378dcf87505a49e6b))
* record what reading every endpoint's response showed ([#77](https://github.com/matsudan/pyreinfolib/issues/77)) ([f596f00](https://github.com/matsudan/pyreinfolib/commit/f596f005190544f4c8adce204eef9e2d48b3cd4e))

## [0.7.1](https://github.com/matsudan/pyreinfolib/compare/v0.7.0...v0.7.1) (2026-08-03)


### Documentation

* organise the README around using the API, not around signatures ([#72](https://github.com/matsudan/pyreinfolib/issues/72)) ([ef33cab](https://github.com/matsudan/pyreinfolib/commit/ef33cab296d880b55b6190581f88f49c20695ea6))
* remove the endpoint count and the inline code list ([#73](https://github.com/matsudan/pyreinfolib/issues/73)) ([d68478d](https://github.com/matsudan/pyreinfolib/commit/d68478d0486c5736e36a866047d93584001c53b7))
* show the code table wording on enum members ([#74](https://github.com/matsudan/pyreinfolib/issues/74)) ([bb2be6d](https://github.com/matsudan/pyreinfolib/commit/bb2be6d9cb53fbbe45009d57a43aceea1fd8762e))
* split the glossary into its own file ([#70](https://github.com/matsudan/pyreinfolib/issues/70)) ([6e77cc7](https://github.com/matsudan/pyreinfolib/commit/6e77cc74af5bd23dd4ec8d4bf11d6dad46989f1e))

## [0.7.0](https://github.com/matsudan/pyreinfolib/compare/v0.6.0...v0.7.0) (2026-08-02)


### ⚠ BREAKING CHANGES

* `get_municipal_offices_and_public_meeting_facilities_etc` is now `get_municipal_offices_and_meeting_facilities_etc`, and `get_future_population_estimates_by_250m_mesh` is now `get_population_projections_in_250m_grid_squares`. Their response and properties types are renamed to match. No aliases are kept. ([#69](https://github.com/matsudan/pyreinfolib/issues/69))
* every `Client` method now returns a `TypedDict` from `pyreinfolib.types` rather than `dict[str, Any]`. A `TypedDict` is not assignable to `dict[str, Any]`, so a caller who annotated a return value fails type checking. Drop the annotation, or use the matching `...Response` type. Runtime behaviour is unchanged.

### Features

* add the flood, storm surge and tsunami inundation endpoints ([#64](https://github.com/matsudan/pyreinfolib/issues/64)) ([30f0976](https://github.com/matsudan/pyreinfolib/commit/30f097691797d60954c1d0c57805ff91cab28fd3))
* add the large-scale developed embankment endpoint ([#67](https://github.com/matsudan/pyreinfolib/issues/67)) ([4cffec9](https://github.com/matsudan/pyreinfolib/commit/4cffec9486a4af3f80f39b4984934c74789b1210))
* add the liquefaction tendency and disaster history endpoints ([#68](https://github.com/matsudan/pyreinfolib/issues/68)) ([c969d9c](https://github.com/matsudan/pyreinfolib/commit/c969d9c64dc6d405a629034f07a03fc883da1063))
* add the steep slope failure hazard area endpoint ([#66](https://github.com/matsudan/pyreinfolib/issues/66)) ([b0584e7](https://github.com/matsudan/pyreinfolib/commit/b0584e751007aa8c1962509b437b07d517fb46c1))
* rename the two methods whose names had no source ([#69](https://github.com/matsudan/pyreinfolib/issues/69)) ([6fc2f2d](https://github.com/matsudan/pyreinfolib/commit/6fc2f2d8bed934c2286a893d19b7551ad96d84cd))
* type the response bodies ([#63](https://github.com/matsudan/pyreinfolib/issues/63)) ([3922c42](https://github.com/matsudan/pyreinfolib/commit/3922c427ac586e0a8abaae905c51410320d1c57f))


### Documentation

* describe the data in docstrings, not how the name was derived ([#65](https://github.com/matsudan/pyreinfolib/issues/65)) ([2c5f737](https://github.com/matsudan/pyreinfolib/commit/2c5f737f44b775cf1c90093774da7c10e9e201f2))
* reword the section headings and shorten the prose ([#61](https://github.com/matsudan/pyreinfolib/issues/61)) ([55afa91](https://github.com/matsudan/pyreinfolib/commit/55afa910538ee031c83d944948c0ad9133a77ff3))

## [0.6.0](https://github.com/matsudan/pyreinfolib/compare/v0.5.0...v0.6.0) (2026-08-01)


### Features

* add the disaster risk area, city planning road and DID endpoints ([#55](https://github.com/matsudan/pyreinfolib/issues/55)) ([61a49e4](https://github.com/matsudan/pyreinfolib/commit/61a49e4ca3ce0e8f469b96e32295cb2732aeea30))
* add the landslide prevention and sediment disaster endpoints ([#58](https://github.com/matsudan/pyreinfolib/issues/58)) ([0f2ff5d](https://github.com/matsudan/pyreinfolib/commit/0f2ff5d714321e2410768cd8459c0739de8c0899))
* add the location normalization plan endpoint ([#60](https://github.com/matsudan/pyreinfolib/issues/60)) ([2e4c963](https://github.com/matsudan/pyreinfolib/commit/2e4c963d0a49cb788cddfab214b67dcf02e23f88))
* add the natural park and emergency evacuation site endpoints ([#54](https://github.com/matsudan/pyreinfolib/issues/54)) ([646686f](https://github.com/matsudan/pyreinfolib/commit/646686feee259e66b95614bfac9faab061c4a532))
* add the tile endpoints that filter by municipality code ([#53](https://github.com/matsudan/pyreinfolib/issues/53)) ([0faf56f](https://github.com/matsudan/pyreinfolib/commit/0faf56f9df8c8ae28dbcfc3c3136feb7dee13ca4))
* add the tile endpoints that take no further parameters ([#51](https://github.com/matsudan/pyreinfolib/issues/51)) ([0b625ac](https://github.com/matsudan/pyreinfolib/commit/0b625ac4f2afda6488fb4bdc7600f4b248e6beee))
* support Python 3.13 and 3.14 ([#57](https://github.com/matsudan/pyreinfolib/issues/57)) ([c0af7b7](https://github.com/matsudan/pyreinfolib/commit/c0af7b72141e4b16d8def22b8626b65b27bf3356))


### Documentation

* add status badges to the README ([#56](https://github.com/matsudan/pyreinfolib/issues/56)) ([faf9828](https://github.com/matsudan/pyreinfolib/commit/faf98281addb8498af11d88e07254bc864dd6143))

## [0.5.0](https://github.com/matsudan/pyreinfolib/compare/v0.4.0...v0.5.0) (2026-08-01)


### ⚠ BREAKING CHANGES

* `get_land_price_public_notices_and_surveys_point` is now `get_land_market_value_publication_and_research_point`, and `LandPriceClassification.LAND_PRICE_PUBLIC_NOTICE` and `PREFECTURAL_LAND_PRICE_SURVEY` are now `LAND_MARKET_VALUE_PUBLICATION` and `PREFECTURAL_LAND_MARKET_VALUE_RESEARCH`. The codes and the behaviour are unchanged; only the names move.
* a blank string argument now raises `ValueError` instead of being dropped. Pass `None`, or leave the argument out, to omit it; use `city=value or None` for a value that may be blank. An empty sequence of codes raises for the same reason.

### Features

* add tile coordinate helpers ([#43](https://github.com/matsudan/pyreinfolib/issues/43)) ([a17c887](https://github.com/matsudan/pyreinfolib/commit/a17c887e6b08bef1b3ee9c6aa39cf62ebf9044de))
* reuse HTTP connections and retry throttled requests ([#42](https://github.com/matsudan/pyreinfolib/issues/42)) ([4f901d3](https://github.com/matsudan/pyreinfolib/commit/4f901d3378a226ca1c94a0124e17f485d97d4481))
* use MLIT current terminology for the land price surveys ([#49](https://github.com/matsudan/pyreinfolib/issues/49)) ([ca260c8](https://github.com/matsudan/pyreinfolib/commit/ca260c81e4c6761d01a998a2ad6c433d5f4122eb))


### Bug Fixes

* accept a computed zoom level on the tile endpoints ([#45](https://github.com/matsudan/pyreinfolib/issues/45)) ([3af4a26](https://github.com/matsudan/pyreinfolib/commit/3af4a262c3b0be49d84462ee2c077eed9405b8ae))
* refuse a blank argument instead of treating it as omitted ([#48](https://github.com/matsudan/pyreinfolib/issues/48)) ([a5e08ac](https://github.com/matsudan/pyreinfolib/commit/a5e08ac57d5888c1fa4c1c0b30aa76998fe92cad))


### Documentation

* document the naming rule and the terminology glossary ([#40](https://github.com/matsudan/pyreinfolib/issues/40)) ([8cadbf9](https://github.com/matsudan/pyreinfolib/commit/8cadbf98768708c54cd01591f73950def5ca9e76))
* record the pull request description format ([#47](https://github.com/matsudan/pyreinfolib/issues/47)) ([183949d](https://github.com/matsudan/pyreinfolib/commit/183949dfb8bef111b64c962c15a134592a8a337d))
* say how a shared term in a coordinated name is handled ([#50](https://github.com/matsudan/pyreinfolib/issues/50)) ([1dd96c5](https://github.com/matsudan/pyreinfolib/commit/1dd96c5110fdb181907bd8c31e6e65fca3767c93))

## [0.4.0](https://github.com/matsudan/pyreinfolib/compare/v0.3.0...v0.4.0) (2026-07-31)


### ⚠ BREAKING CHANGES

* `price_classification` no longer accepts a bare code string. Pass `pyreinfolib.enums.PriceClassification` on `get_real_estate_prices` and `get_real_estate_prices_point`, and `pyreinfolib.enums.LandPriceClassification` on `get_land_price_public_notices_and_surveys_point`. A `StrEnum` member is a `str`, so existing calls keep working at runtime; it is type checking that now rejects them.
* requests exceptions no longer escape the client. Catch `pyreinfolib.ReinfolibError`, or one of its subclasses, instead of `requests.RequestException`. In particular, a query that matches no data now raises `NoResultsError` instead of `requests.HTTPError` for HTTP 404.

### Features

* accept enums for price classification codes ([#39](https://github.com/matsudan/pyreinfolib/issues/39)) ([1ea86b2](https://github.com/matsudan/pyreinfolib/commit/1ea86b22fabeb35b9763b99433ebd7595c8c7a45))
* replace requests exceptions with a pyreinfolib exception hierarchy ([#36](https://github.com/matsudan/pyreinfolib/issues/36)) ([da2f8d4](https://github.com/matsudan/pyreinfolib/commit/da2f8d48c5e389570c4d2bc74c77ec7c407e4451))


### Bug Fixes

* reject an empty api_key at construction time ([#33](https://github.com/matsudan/pyreinfolib/issues/33)) ([d413b72](https://github.com/matsudan/pyreinfolib/commit/d413b72aee3be08c7faf8e37992d1926100b56f5))

## [0.3.0](https://github.com/matsudan/pyreinfolib/compare/v0.2.1...v0.3.0) (2026-07-31)


### Features

* add request timeout and fix error handling for responseless failures ([#27](https://github.com/matsudan/pyreinfolib/issues/27)) ([b0ac782](https://github.com/matsudan/pyreinfolib/commit/b0ac782f1d621ad04f76f34a0dd35b2e6a738503))
* ship type information (PEP 561) ([#30](https://github.com/matsudan/pyreinfolib/issues/30)) ([419458a](https://github.com/matsudan/pyreinfolib/commit/419458a8ae74e4c86826d21980d9a94970c1b14f))

## [0.2.1](https://github.com/matsudan/pyreinfolib/compare/v0.2.0...v0.2.1) (2026-07-30)


### Bug Fixes

* fix release and publish and add lint  and test ci ([#17](https://github.com/matsudan/pyreinfolib/issues/17)) ([1e5acfd](https://github.com/matsudan/pyreinfolib/commit/1e5acfd07fad4876b9a33817b33423c79d23cf77))

## [0.2.0](https://github.com/matsudan/pyreinfolib/compare/v0.1.0...v0.2.0) (2024-11-28)


### Features

* add get_number_of_passengers_per_station method ([#12](https://github.com/matsudan/pyreinfolib/issues/12)) ([9eccf89](https://github.com/matsudan/pyreinfolib/commit/9eccf89e473b89cab77d7ee4ab4d2d7c439853a4))

## [0.1.0](https://github.com/matsudan/pyreinfolib/compare/v0.1.0...v0.1.0) (2024-11-23)


### Features

* add client class ([989f0cb](https://github.com/matsudan/pyreinfolib/commit/989f0cb6b440fba08169b315a6e6db5ab95611fb))
* add get_appraisal_reports method ([4a246c3](https://github.com/matsudan/pyreinfolib/commit/4a246c3235db378451deaa2e7a4f7cd7284ac912))
* add get_land_price_public_notices_and_surveys_point method ([a1cae6a](https://github.com/matsudan/pyreinfolib/commit/a1cae6af60b180309f5aa59b49cd11c0a24f5d98))
* add get_real_estate_price_point method ([6bac4fa](https://github.com/matsudan/pyreinfolib/commit/6bac4fa101bbe00bca285a22045f804fd97787ab))
* add get_real_estate_prices method ([27b7894](https://github.com/matsudan/pyreinfolib/commit/27b78947fbcb5074d3ae70f2495b50e08b7504b4))
* add landTypeCode enum ([837d031](https://github.com/matsudan/pyreinfolib/commit/837d03158ff7960f91c892ce525119105eeece93))
* add UseDivision enum ([df1f213](https://github.com/matsudan/pyreinfolib/commit/df1f213e717fc7fd57906b201050d68b7f2b9107))


### Bug Fixes

* fix area argument type of get_municipalities method to str ([2594a17](https://github.com/matsudan/pyreinfolib/commit/2594a17eb1a0ecea271d865dee981788abdc27dd))
* fix get method name in each api method ([d6031b3](https://github.com/matsudan/pyreinfolib/commit/d6031b37f4467f06ff501ebaa38cc1a7a667a542))
* fix to add trailing slash to the end of base url ([350af78](https://github.com/matsudan/pyreinfolib/commit/350af789c65399e477b0075c1d77e49e6f9d1a1a))
* fix to use urljoin for api_url ([f8842b8](https://github.com/matsudan/pyreinfolib/commit/f8842b8999993d47401582c02167b762a615446f))
