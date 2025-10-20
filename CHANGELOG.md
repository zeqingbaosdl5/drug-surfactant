# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive batch conditioning documentation in `BATCH_CONDITIONING_GUIDE.md`
- Working example script `batch_conditioning_example.py` demonstrating proper use of `get_next_trials`
- Issue resolution document `ISSUE_RESOLUTION.md` analyzing the `update_results.ipynb` workflow
- Updated README.md with quick reference to batch conditioning resources
- Hardware constraints documentation for batch sizing (4 slots, 2 tip sizes, up to 2 x 96-wellplates)
- Trial-level early stopping section with periodic measurement considerations
- Documentation of trade-offs between batch size and manual intervention frequency

### Changed
- Documented recommended approach for batch conditioning using Ax v1's built-in mechanisms
- Clarified when to use `update_trial_data()` vs `get_next_trials()` for different use cases
- Added guidance on balancing batch sizes with periodic stability measurements
- Converted example from Jupyter notebook to Python script for easier integration

### Deprecated
- Manual fantasy point updates using `update_trial_data()` for batch conditioning (use `get_next_trials()` instead)

