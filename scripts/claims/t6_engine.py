"""Compatibility import; research logic lives in project.random_pairs."""

from project.random_pairs import (  # noqa: F401
    CONVERGED, END, DELISTED, account, book_returns, last_valid_rows,
    monthly_returns, portfolio_months, prices_from_returns, rank_books,
    forced_closes, resolve_closes, vw_returns,
)
