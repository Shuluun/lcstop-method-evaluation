# 第三方声明 / Third-party notices

## LCBench data

Zimmer, Lucas (2020). data_2k_3seed. figshare. Version1.
DOI: https://doi.org/10.6084/m9.figshare.12408707.v1
Official repository: https://github.com/automl/LCBench
License: [Apache License 2.0](licenses/LCBench-Apache-2.0.txt).

Bundled data are modified by fixed six-task/configuration/seed/checkpoint selection, field restriction,
and the documented validation-loss unit conversion. The preserved first-attempt cache has an invalid loss unit;
the corrected v2 cache retains its explicit recovery provenance.
Attribution and versioned metadata are in [data documentation](docs/DATA_AND_SOURCES.md).
No full raw archive or unselected task curves are bundled.
The live version1 license metadata was rechecked for this release without opening curve data:
[license check](public_release_v1/data_license_check.json).

## SureStop snapshot

Copyright (c) 2026 Adam Noonan.
Original project: https://github.com/ACNoonan/surestop .
License: [MIT](sources/repos/ACNoonan/surestop/LICENSE).
The runtime imports the byte-pinned [core.py](sources/repos/ACNoonan/surestop/src/surestop/core.py), unmodified.
Its SHA256 and saved Git blob/tree identities remain in [source documentation](docs/DATA_AND_SOURCES.md).
The bundled upstream README is an archival snapshot. Claims such as “this repository contains LoRA runs”
refer to the upstream repository, not to LCStop. Those experiments and full upstream repository are not bundled.

## Other reviewed works

Historical reading scopes, original URLs and byte fingerprints are retained in
[read_scope.json](sources/read_scope.json), [source_snapshots.json](sources/source_snapshots.json)
and [the inclusion map](publication/THIRD_PARTY_SNAPSHOT_MAP.csv).
A historical path in that manifest does not assert that the corresponding third-party source is bundled.
No paper PDFs, complete external repositories, or pretrained weights are included.

## Scope / 范围

These third-party licenses apply to their respective materials, not automatically to original LCStop code and writing.
第三方代码、数据与理论不归为本人原创；本次公开不新增全仓库开源许可。
[License scope / 许可范围](LICENSE_SCOPE.md)
