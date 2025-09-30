# Changelog

All notable changes to the drug-surfactant project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-09-30

### Added
- FastAPI server (`api_server.py`) with opentrons.simulate integration
- Protocol simulation endpoint using `opentrons.simulate` for validation
- Protocol execution endpoint using `opentrons.execute` for hardware control
- API helper functions (`api_helper_functions.py`) replacing SSH/SCP workflow
- Railway deployment configuration (`railway.toml`, `Dockerfile`)
- Comprehensive test suite (`comprehensive_test.py`)
- Migration guide and documentation (`MIGRATION_GUIDE.md`)
- Demo notebook (`api_workflow_demo.ipynb`) showing new workflow

### Changed
- Migrated from Jupyter notebook SSH/SCP workflow to API-based system
- Protocol generation now uses RESTful API instead of file uploads
- Cloud deployment via Railway instead of local robot computer access

### Deprecated
- `upload_file_to_robot()` function (replaced by API-based approach)
- SSH/SCP file transfer mechanism

### Removed
- Compiled Python files (.pyc) and cache directories
- macOS .DS_Store files from repository

### Fixed
- Added proper Python .gitignore template to prevent future commits of build artifacts
- Updated Railway configuration for proper cloud deployment