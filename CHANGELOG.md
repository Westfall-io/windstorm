# CHANGELOG




## v0.3.1 (2024-07-10)
### Features
### Fixes

#### :bug:

* :bug: Fixed an issue where the chaining method changed when only one deep ([`5a3fb42`](https://github.com/Westfall-io/windstorm/commit/5a3fb429543f4ea958ff436890692a7488bc90e8))

* :bug: Fixing issue where newline characters would be missing from files edited on windows before a commit and all files would be changed making it harder to compare ([`381674f`](https://github.com/Westfall-io/windstorm/commit/381674fc802e42203effbfa259db220c87036f76))

### Tests and Documentation

### Others (CI/CD, Dependencies)

#### :zap:

* :zap: Stop looking for windstorm when found ([`4d6599c`](https://github.com/Westfall-io/windstorm/commit/4d6599cd240ca1d1b9aaf47d26df00d386038557))

## v0.3.0 (2024-06-28)
### Features
#### :sparkles:

* :sparkles: Added capability to parse attributes with units, it can&#39;t do anything with the units however. ([`27477cd`](https://github.com/Westfall-io/windstorm/commit/27477cddbacc17e3e94bb7044d55e129b1662a8c))

* :sparkles: Added capability to complete through template parsing errors. ([`89a634d`](https://github.com/Westfall-io/windstorm/commit/89a634deed215cfadfa98ed0dd390852598a3da5))

* :sparkles: Adding default value to windstorm render template function. ([`78ba6a6`](https://github.com/Westfall-io/windstorm/commit/78ba6a623a78b940359ac580ded0b52ce4d4e6ec))

### Fixes

#### :ambulance:

* :ambulance: Updating github action dependency ([`ae7abfe`](https://github.com/Westfall-io/windstorm/commit/ae7abfe9bd9828c53e6224c9ba0b27163defe69c))

#### :bug:

* :bug: Fixed an issue where it would fail if the value could not be parsed correctly. ([`37c10e6`](https://github.com/Westfall-io/windstorm/commit/37c10e6d7bdcc220bff761efefced750d70ba0b2))

* :bug: Fixed an issue where the key used in the template would not be output upon error. ([`1d73006`](https://github.com/Westfall-io/windstorm/commit/1d730063359d5e9ba896a562b5018ddb4cc18627))

* :bug: Fixed an issue where it failed when other elements could be found without metadata associating to a toolvariable. ([`64f48e0`](https://github.com/Westfall-io/windstorm/commit/64f48e074b7b0d78c2d7d596efa57c2c79ddc5a4))

* :bug: Handling missing project id with appropriate error notification. ([`c5ffb32`](https://github.com/Westfall-io/windstorm/commit/c5ffb32d6ae4d5d8882bf6dcc0b710f4e3d94aa9))

* :bug: Better handling for element name not found error ([`ee7aa9a`](https://github.com/Westfall-io/windstorm/commit/ee7aa9a78980cbd25af1a16ca9fec13dcef73edf))

### Tests and Documentation

### Others (CI/CD, Dependencies)

## v0.2.6 (2024-06-26)
### Features
### Fixes

#### :bug:

* :bug: Revert pyproject.toml change. ([`e14a4ae`](https://github.com/Westfall-io/windstorm/commit/e14a4aec734696ae945c200dac95192c803a8708))

### Tests and Documentation

### Others (CI/CD, Dependencies)

## v0.2.5 (2024-06-26)
### Features
### Fixes

#### :bug:

* :bug: Update to function. ([`1b39c59`](https://github.com/Westfall-io/windstorm/commit/1b39c5984faf077bf9c97a09116c7214c05bcb91))

### Tests and Documentation

### Others (CI/CD, Dependencies)

## v0.2.4 (2024-06-26)
### Features
### Fixes

#### :bug:

* :bug: Fixing script method. ([`2dc391a`](https://github.com/Westfall-io/windstorm/commit/2dc391ad6c6ed5935825f29624139e09f5b4b732))

### Tests and Documentation

### Others (CI/CD, Dependencies)

## v0.2.3 (2024-06-26)
### Features
### Fixes

#### :bug:

* :bug: Trying flask methodology. ([`c294aae`](https://github.com/Westfall-io/windstorm/commit/c294aae68136f32607e90a8b635f6d0e2ae66245))

### Tests and Documentation

### Others (CI/CD, Dependencies)

## v0.2.2 (2024-06-26)
### Features
### Fixes

#### :bug:

* :bug: Incorrect semantics. ([`d87d6c4`](https://github.com/Westfall-io/windstorm/commit/d87d6c43f89f42125c733097f08a519e7b6e8409))

* :bug: More poetry changes. ([`9eaa77c`](https://github.com/Westfall-io/windstorm/commit/9eaa77c7b1fc9dadd98781dd6768a3b7529ce5ab))

### Tests and Documentation

### Others (CI/CD, Dependencies)

## v0.2.1 (2024-06-26)
### Features
### Fixes

#### :bug:

* :bug: Command-line interface. ([`0a2a4af`](https://github.com/Westfall-io/windstorm/commit/0a2a4afb737070f95eaaf6ce59b26843e790f06d))

### Tests and Documentation

### Others (CI/CD, Dependencies)

#### Other

* :green_heart: Updates to build to give command to poetry. ([`3824c72`](https://github.com/Westfall-io/windstorm/commit/3824c72c34aa8194be29edf893c31c14a20e722d))

* :green_heart: Updates to build to give command to poetry. ([`5a2e4f7`](https://github.com/Westfall-io/windstorm/commit/5a2e4f7b88c92645a3ead072c4eacc093af2864d))

## v0.2.0 (2024-06-26)
### Features
#### :sparkles:

* :sparkles: Using API over sysml2py for now ([`2aa8be2`](https://github.com/Westfall-io/windstorm/commit/2aa8be2bb95343c5293ab48ff26f4ded3928a892))

### Fixes

#### :bug:

* :bug: Fixing removed template ([`3e8b868`](https://github.com/Westfall-io/windstorm/commit/3e8b8681b0c316a7f72521123891d037c72b55ce))

### Tests and Documentation

### Others (CI/CD, Dependencies)

#### Other

* :green_heart: Updates to release workflow. ([`11a914e`](https://github.com/Westfall-io/windstorm/commit/11a914e6a63dd8a48b7f365f50d7e2251ea6b5c4))

## v0.1.1 (2023-07-25)
### Features
### Fixes

### Tests and Documentation

#### :memo:

* :memo: Removing merge commits from CHANGELOG ([`55b9ece`](https://github.com/Westfall-io/windstorm/commit/55b9ece5ec1da4e59532b934bdbee61c68bd0f1e))

### Others (CI/CD, Dependencies)

## v0.1.0 (2023-07-25)
### Features
#### :sparkles:

* :sparkles: Updates for semantic-release v0.8 ([`3d20ea4`](https://github.com/Westfall-io/windstorm/commit/3d20ea46e6ef721cf69e68ea61c74384dc7c3ab6))

### Fixes

### Tests and Documentation

#### :memo:

* :memo: Updates to release workflow for CHANGELOG.md ([`0a4281d`](https://github.com/Westfall-io/windstorm/commit/0a4281ddccada66a7da8c309cf4d1ce88ce4cf2c))

* :memo: Adding template for CHANGELOG for semantic release ([`6685f66`](https://github.com/Westfall-io/windstorm/commit/6685f66b62162b03fdff96c597ebf3dd8d32eb23))

* :memo: Updates to documentation. ([`642e0a5`](https://github.com/Westfall-io/windstorm/commit/642e0a5001d8268eca5473060c440831e22f52e0))

#### :white_check_mark:

* :white_check_mark: Adding null test. ([`749fd48`](https://github.com/Westfall-io/windstorm/commit/749fd48a7b2d4f304bace4b7f17f1cc44d39c50f))

### Others (CI/CD, Dependencies)

#### :construction:

* :construction: Adding more structure. ([`df55699`](https://github.com/Westfall-io/windstorm/commit/df556997d5b53342bf84db850170e3649fdaa0d8))

#### :heavy_plus_sign:

* :heavy_plus_sign: Adding requirements.txt ([`3208fa0`](https://github.com/Westfall-io/windstorm/commit/3208fa059fea3440061aad8c1294964aeb924cb2))

#### Other

* :tada: Adding build support with poetry. ([`b093812`](https://github.com/Westfall-io/windstorm/commit/b093812e6fe5454868507ba23683fe25dc3deded))
