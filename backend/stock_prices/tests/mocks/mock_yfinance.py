from unittest import mock

import pandas as pd


class MockTicker(object):
    fast_info = {"currency": "USD"}
    sort_values = mock.Mock(spec=pd.DataFrame)


def create_ticker_mock() -> MockTicker:
    return MockTicker()


def create_download_mock_df(ticker: str = "AAPL") -> pd.DataFrame:
    """Create a mock dataframe with multi-index columns like real yfinance data

    Args:
        ticker: The ticker symbol to use in the multi-index columns

    Returns:
        DataFrame: A dataframe with multi-index columns matching yfinance structure
    """
    dates = pd.to_datetime(["2022-08-02", "2022-08-03", "2022-08-04"])
    columns = pd.MultiIndex.from_tuples(
        [
            ("Close", ticker),
            ("High", ticker),
            ("Low", ticker),
            ("Open", ticker),
            ("Volume", ticker),
        ]
    )
    data = [
        [100.0, 105.0, 95.0, 100.0, 1000000],
        [110.0, 115.0, 105.0, 110.0, 1100000],
        [120.0, 125.0, 115.0, 120.0, 1200000],
    ]
    mock_df = pd.DataFrame(data, index=dates, columns=columns)
    mock_df.index.name = "Date"
    return mock_df


def create_empty_download_mock_df() -> pd.DataFrame:
    """Create an empty mock dataframe with multi-index columns

    Returns:
        DataFrame: An empty dataframe with multi-index columns
    """
    columns = pd.MultiIndex.from_tuples(
        [
            ("Close", "EMPTY"),
            ("High", "EMPTY"),
            ("Low", "EMPTY"),
            ("Open", "EMPTY"),
            ("Volume", "EMPTY"),
        ]
    )
    mock_df = pd.DataFrame(columns=columns)
    mock_df.index.name = "Date"
    return mock_df


def create_download_mock():
    return create_download_mock_df()
