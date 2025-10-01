# Rooms - Trading System

Welcome to all my trading rooms! This is a modular Python trading system built with a workspace structure using `uv`.

## Overview

The project is organized into four main "rooms", each serving a specific purpose in the trading workflow:

## Architecture

### 🏢 Desk
**The integration hub** - Brings all components together into a cohesive trading platform.

- **Purpose**: Orchestrates the entire trading system
- **Status**: Initial setup

### 📊 Tape
**Data harvesting room** - Collects and processes market data.

- **Purpose**: Data acquisition and preprocessing
- **Status**: Initial setup

### 🔄 Replay
**Strategy optimization room** - Replays and optimizes trading strategies.

- **Purpose**: Backtesting and strategy refinement
- **Status**: Initial setup

### 🧪 Lab
**Innovation room** - Tests crazy ideas and experimental features.

- **Purpose**: Research and experimentation
- **Status**: Initial setup

## Project Structure

```
rooms/
├── pyproject.toml          # Workspace configuration
├── main.py                 # Root entry point
├── .python-version         # Python version (3.13)
├── .gitignore             # Python-specific ignores
├── desk/                  # Integration module
├── tape/                  # Data harvesting module
├── replay/                # Strategy replay module
└── lab/                   # Experimental module
```

Each room contains:
- `pyproject.toml` - Module configuration
- `main.py` - Module entry point
- `README.md` - Module documentation

## Technology Stack

- **Language**: Python 3.13+
- **Package Manager**: uv
- **Workspace**: Monorepo structure with uv workspaces

## Getting Started

1. **Prerequisites**:
   ```bash
   # Install uv
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Ensure Python 3.13+ is available
   python --version
   ```

2. **Setup**:
   ```bash
   # Clone and enter directory
   cd rooms

   # Install dependencies
   uv sync
   ```

3. **Run modules**:
   ```bash
   # Run entire system
   uv run python main.py

   # Run specific room
   cd desk && uv run python main.py
   ```

## Development

- All modules are currently in initial setup phase
- Each room has placeholder "Hello World" implementations
- Ready for feature development

## Contributing

This is a personal trading system project. Development follows:
- Incremental progress over big changes
- Test-driven development where applicable
- Clear documentation and commit messages

## License

Personal project - no license specified.