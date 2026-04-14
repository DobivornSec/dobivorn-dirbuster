# Changelog

## [5.0.0] - 2026-04-14

### Added
- Built-in wordlist profiles: `quick` and `full` via `--profile`.
- New default profile flow optimized for faster first-pass scans.
- `wordlists/quick.txt` and `wordlists/full.txt` files.
- Runtime log that prints active wordlist path.

### Changed
- Upgraded project version to 5.0.
- `--wordlist` now explicitly overrides selected profile.
- Documentation rewritten for profile-based usage.

## [4.0.0] - 2026-04-14

### Added
- Retry support for transient network errors (`--retries`).
- Recursive depth limiter (`--max-depth`).
- Output format override (`--output-format`).
- Verbose diagnostics mode (`-v/--verbose`).

### Changed
- Upgraded core scanner architecture for better error handling and stability.
- Improved false-positive filtering with multi-sample 404 fingerprinting.
- Expanded default status filters to include 204/307/401.
- Improved report generation and output directory handling.
- Refreshed CLI help text and examples.

### Fixed
- Recursive scanning progress handling issues.
- Duplicate URL checks and path normalization edge cases.
- Better validation for invalid target URLs and empty wordlists.
