# Private publication copy: changes and exclusions

Source: LCStop_20261029_v1. The research source is read-only.
No pre-existing final_delivery_v1 directory was found; none was invented.
A new Git history is initialized only in this independent publication copy.

## Exact copy and modifications

[source_manifest.csv](source_manifest.csv) lists each explicitly whitelisted source/destination, original/published hash and change.
Scientific Python scripts, caches, rules, results, fixed permutations and historical check records were copied byte-for-byte.
Only machine-local location examples in three report copies were replaced with descriptive placeholders.
README.md is new; the old README is preserved at README_research_original.md.
.gitignore was written before staging; .gitattributes disables newline conversion so pinned bytes remain stable across Git on Windows.
The new tools/reproduce.py isolates future runs. It does not refactor scientific logic.
requirements-replay.txt narrows installation to runtime packages at their recorded versions; requirements.txt remains unchanged.

## Excluded

No original .git history, .venv, paper PDFs, raw large ZIP, caches/.cache, credentials, full external repositories or old unrelated research projects.
Historical one-off sources/execution_helpers were not required by the runtime and are omitted; operational generation scripts are at the root.
Original AGENTS is not inherited by the publication copy: its historical no-upload rule was explicitly superseded for this private publication only.
No new repository-wide software license is selected. Dataset and SureStop licenses retain their own scope.
No CI, automatic training/download, Git LFS billing or collaborator invitation is configured.

The report references old boundary decisions only as LCStop history; no files from those older projects were read/copied.
The source_protection.json and publication_check.json checks cover the consulted whitelist plus source AGENTS, not the environment or large excluded raw archive.
Historical source hashes are retained, not rewritten to erase failures.

## Initial packaging findings and resolution

The initial static check found signed public download query parameters in two historical acquisition entries.
They were removed from the publication copy before staging; original logs remain unchanged.
The scanner also matched its own /home pattern as a path; its path recognition was narrowed, without disabling credential checks.
The first FAIL is retained in check_attempt01.json. Subsequent PASS covers the corrected publication copy only.
No credential value was printed or used for authentication.

## Git byte preservation

Default Git whitespace checking reported CRLF line endings in byte-preserved historical files. A CR-aware check and staged Git-blob verification are recorded in git_stage_check.json. No scientific file was reformatted to silence the warning.
