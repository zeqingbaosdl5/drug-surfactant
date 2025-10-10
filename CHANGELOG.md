# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Added `obj_surf_conc` objective to minimize total surfactant concentration (2024-09-30)
  - New objective in `optimizer_init()` function to minimize the sum of all surfactant concentrations
  - Updated `virtual_exp()` function to accept `surfactant_conc` parameter and return `obj_surf_conc` value
  - `obj_surf_conc` is an **analytic deterministic objective** (not black-box) - equals `surfactant_conc` parameter directly
  - This enables optimization towards formulations that "use less surfactant and still have it be stable"
- Added `stability_threshold` parameter to `optimizer_init()` for easy adjustment (2024-10-10)
  - Default threshold is 0.06 (absorbance)
  - Can be adjusted based on module conditions as requested
  - Prepared for future stability constraint implementation

### Changed
- Updated `requirements.txt` to use `ax-platform~=0.2` for compatibility with existing codebase (2024-09-30)
- Enhanced documentation to clarify that `obj_surf_conc` is an analytic deterministic objective, not a black-box function (2024-10-10)
  - Ax will still model it, but the relationship is exact: obj_surf_conc = surfactant_conc
  - No experimental measurement needed for this objective

### Documentation
- Clarified distinction between analytic deterministic objectives and black-box deterministic objectives
- Added notes on stability as an outcome constraint (threshold-based, not "lower is better")
- Documented that stability threshold is easily adjustable
