# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Added `obj_surf_conc` objective to minimize total surfactant concentration (2024-09-30)
  - New objective in `optimizer_init()` function to minimize the sum of all surfactant concentrations
  - Updated `virtual_exp()` function to accept `surfactant_conc` parameter and return `obj_surf_conc` value
  - `obj_surf_conc` is a deterministic outcome calculated directly from the `surfactant_conc` parameter
  - This enables optimization towards formulations that "use less surfactant and still have it be stable"

### Changed
- Updated `requirements.txt` to use `ax-platform~=0.2` for compatibility with existing codebase (2024-09-30)
