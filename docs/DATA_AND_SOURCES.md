# Data and third-party provenance

## Included inputs

The v2 cache contains exactly the six already-used tasks, 128 configurations/task, three recorded seeds and five nodes.
Fields are validation accuracy/loss, recorded elapsed time, configuration metadata and fixed selection metadata; no test metrics.
Both the invalid-unit v1 cache and corrected v2 cache are included so correction history can be inspected without reopening the archive.
No new extraction or sampling was performed for publication.

Official metadata saved in [figshare_12408707.json](../sources/figshare_12408707.json) identifies the dataset as Apache 2.0.
The copied [Apache license](../licenses/LCBench-Apache-2.0.txt) came from the already-acquired official LCBench repository snapshot.
This subset is modified by selection/field restriction and unit conversion, not an unmodified full archive.
Attribution: Zimmer, Lucas (2020). data_2k_3seed. figshare. https://doi.org/10.6084/m9.figshare.12408707.v1 .
No dataset NOTICE was present in the acquired reduced repository snapshot; the large archive was not opened during publication.

## Official full input, not uploaded

- DOI: https://doi.org/10.6084/m9.figshare.12408707.v1
- URL: https://ndownloader.figshare.com/files/22859435
- Official name: bench_full.zip; version1; bytes: 1813896086.
- SHA256: e490969c4f068fc7d96c880f9d3051bc2ae285feae995f6610d6a92092bc1198
- Put at data/bench_full.zip (ignored by Git), or provide its path to the raw preparation wrapper.
- ZIP member: bench_full.json. Do not manually concatenate planned horizons or use test metrics.
- Existing download evidence: [full_archive_download.json](../sources/full_archive_download.json).
- Generators: [download_full.py](../download_full.py), [extract_selected.py](../extract_selected.py), [json_adapter.py](../json_adapter.py).
- The original download/metadata pass succeeded historically. Corrected extractor source exists, but a complete corrected raw-to-results rebuild was not rerun; publication does not claim otherwise.

## SureStop runtime snapshot

Only core.py and its existing LICENSE/README/tree metadata are bundled, not the full repository.
Copyright (c) 2026 Adam Noonan; MIT license. core.py is unmodified:
SHA256 6b3628e2dbf728daf3fb96b18c66d798f047e1dae779707a9bc6cc80dda7cf9a.
Saved Git blob: 9dc0449d8d274ce89d318820850185a7a4b66569.
Saved Git tree: cd05b98240449dbdf39c07b6176460d6dfebf0a2 (a tree, not a commit).
Original URL: https://github.com/ACNoonan/surestop .
The runtime imports this local snapshot explicitly, so it does not depend on mutable HEAD.

## Other neighbors

[read_scope.json](../sources/read_scope.json) and [source_snapshots.json](../sources/source_snapshots.json) retain the historical reading depth, public URLs and byte hashes.
Most paths in the historical snapshot manifest refer to deliberately omitted external sources. The manifest records history; it is not an assertion that all those files are bundled.
[Snapshot inclusion map](../publication/THIRD_PARTY_SNAPSHOT_MAP.csv) states the status of each entry.
Papers, complete downloaded repositories, ifBO weights and unrelated local caches are not included.
No new paper, repository or model weight was downloaded for publication.
