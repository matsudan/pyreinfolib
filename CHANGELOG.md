# Changelog

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
