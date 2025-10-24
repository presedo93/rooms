"""Type definitions for third-party libraries with incomplete type stubs.

This module provides Protocol classes for libraries like vectorbt that use
dynamic attribute generation, making LSP autocomplete and type checking work.

Example:
    from desk.typing.vectorbt import PortfolioProtocol

    def analyze(portfolio: PortfolioProtocol) -> dict:
        return {"return": portfolio.total_return()}
"""
