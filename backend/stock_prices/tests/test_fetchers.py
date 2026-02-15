import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

from buho_backend.tests.base_test_case import BaseApiTestCase
from buho_backend.transaction_types import TransactionType
from companies.tests.factory import CompanyFactory
from portfolios.tests.factory import PortfolioFactory
from shares_transactions.tests.factory import SharesTransactionFactory
from stock_prices.fetchers import CompanyStockPriceFetcher
from stock_prices.models import StockPrice


class CompanyStockPriceFetcherTestCase(BaseApiTestCase):
    """Tests for CompanyStockPriceFetcher class."""

    def setUp(self):
        super().setUp()
        self.portfolio = PortfolioFactory.create(base_currency="EUR")
        self.company = CompanyFactory.create(
            portfolio=self.portfolio,
            ticker="AAPL",
            base_currency="USD",
            is_closed=False,
        )

    def _create_stock_price(
        self,
        ticker="AAPL",
        price=150.00,
        transaction_date=None,
    ):
        """Helper to create a stock price in the database."""
        if transaction_date is None:
            transaction_date = datetime.date(2023, 12, 15)

        return StockPrice.objects.create(
            ticker=ticker,
            price=price,
            price_currency="USD",
            transaction_date=transaction_date,
        )

    def _create_shares_transaction(
        self,
        count=10,
        gross_price_per_share=10,
        total_amount=None,
        total_commission=5,
        transaction_date=None,
        transaction_type=TransactionType.BUY,
    ):
        """Helper to create a shares transaction."""
        if transaction_date is None:
            transaction_date = datetime.date(2021, 1, 15)

        if total_amount is None:
            total_amount = count * gross_price_per_share

        return SharesTransactionFactory.create(
            company=self.company,
            gross_price_per_share_currency=self.company.base_currency,
            total_commission_currency=self.company.base_currency,
            count=count,
            gross_price_per_share=gross_price_per_share,
            total_amount=total_amount,
            total_commission=total_commission,
            exchange_rate=1,
            type=transaction_type,
            transaction_date=transaction_date,
        )


class GetLastStockPriceFromDbOfYearTestCase(CompanyStockPriceFetcherTestCase):
    """Tests for get_last_stock_price_from_db_of_year method."""

    def test_returns_last_price_when_exists(self):
        """Should return the most recent stock price in date range."""
        self._create_stock_price(
            ticker="AAPL",
            price=150.00,
            transaction_date=datetime.date(2023, 12, 10),
        )
        self._create_stock_price(
            ticker="AAPL",
            price=155.00,
            transaction_date=datetime.date(2023, 12, 20),
        )
        self._create_stock_price(
            ticker="AAPL",
            price=152.00,
            transaction_date=datetime.date(2023, 12, 15),
        )

        fetcher = CompanyStockPriceFetcher(self.company, 2023)
        result = fetcher.get_last_stock_price_from_db_of_year(
            "AAPL", "2023-12-01", "2023-12-31"
        )

        self.assertIsNotNone(result)
        self.assertEqual(result.price.amount, Decimal("155.00"))

    def test_returns_none_when_no_prices(self):
        """Should return None when no prices exist in range."""
        fetcher = CompanyStockPriceFetcher(self.company, 2023)
        result = fetcher.get_last_stock_price_from_db_of_year(
            "AAPL", "2023-12-01", "2023-12-31"
        )

        self.assertIsNone(result)

    def test_only_returns_prices_in_range(self):
        """Should only consider prices within the specified date range."""
        # Price outside range
        self._create_stock_price(
            ticker="AAPL",
            price=145.00,
            transaction_date=datetime.date(2023, 11, 15),
        )
        # Price inside range
        self._create_stock_price(
            ticker="AAPL",
            price=150.00,
            transaction_date=datetime.date(2023, 12, 15),
        )

        fetcher = CompanyStockPriceFetcher(self.company, 2023)
        result = fetcher.get_last_stock_price_from_db_of_year(
            "AAPL", "2023-12-01", "2023-12-31"
        )

        self.assertIsNotNone(result)
        self.assertEqual(result.price.amount, Decimal("150.00"))


class GetStartEndDatesForYearTestCase(CompanyStockPriceFetcherTestCase):
    """Tests for get_start_end_dates_for_year method."""

    def test_returns_december_dates_for_past_year(self):
        """Should return December 1-31 for past years."""
        fetcher = CompanyStockPriceFetcher(self.company, 2022)
        from_date, to_date = fetcher.get_start_end_dates_for_year(2022)

        self.assertEqual(from_date, "2022-12-01")
        self.assertEqual(to_date, "2022-12-31")

    def test_returns_recent_dates_for_current_year(self):
        """Should return last 15 days to today for current year."""
        current_year = datetime.date.today().year
        fetcher = CompanyStockPriceFetcher(self.company, current_year)
        from_date, to_date = fetcher.get_start_end_dates_for_year(current_year)

        today = datetime.date.today()
        expected_from = (today - datetime.timedelta(days=15)).strftime("%Y-%m-%d")
        expected_to = today.strftime("%Y-%m-%d")

        self.assertEqual(from_date, expected_from)
        self.assertEqual(to_date, expected_to)


class GetStartEndDatesFromLastSellTestCase(CompanyStockPriceFetcherTestCase):
    """Tests for get_start_end_dates_from_last_sell method."""

    def test_returns_dates_based_on_last_sell(self):
        """Should return dates based on last sell transaction."""
        self.company.is_closed = True
        self.company.save()

        self._create_shares_transaction(
            transaction_date=datetime.date(2021, 1, 15),
            transaction_type=TransactionType.BUY,
        )
        self._create_shares_transaction(
            transaction_date=datetime.date(2023, 6, 15),
            transaction_type=TransactionType.SELL,
        )

        fetcher = CompanyStockPriceFetcher(self.company, 2023)
        from_date, to_date = fetcher.get_start_end_dates_from_last_sell(2023)

        self.assertEqual(from_date, "2023-06-15")
        self.assertEqual(to_date, "2023-06-16")

    def test_returns_none_for_year_before_last_sell(self):
        """Should return None, None for years before last sell."""
        self.company.is_closed = True
        self.company.save()

        self._create_shares_transaction(
            transaction_date=datetime.date(2021, 1, 15),
            transaction_type=TransactionType.BUY,
        )
        self._create_shares_transaction(
            transaction_date=datetime.date(2023, 6, 15),
            transaction_type=TransactionType.SELL,
        )

        fetcher = CompanyStockPriceFetcher(self.company, 2022)
        from_date, to_date = fetcher.get_start_end_dates_from_last_sell(2022)

        self.assertIsNone(from_date)
        self.assertIsNone(to_date)

    def test_raises_error_when_no_sell_transactions(self):
        """Should raise ValueError when company has no sell transactions."""
        self.company.is_closed = True
        self.company.save()

        fetcher = CompanyStockPriceFetcher(self.company, 2023)

        with self.assertRaises(ValueError) as context:
            fetcher.get_start_end_dates_from_last_sell(2023)

        self.assertIn("no sell transactions", str(context.exception))


class GetYearLastStockPriceTestCase(CompanyStockPriceFetcherTestCase):
    """Tests for get_year_last_stock_price method."""

    def test_returns_price_from_db_when_exists(self):
        """Should return stock price from DB when it exists."""
        # Create a buy transaction so company has shares
        self._create_shares_transaction(
            transaction_date=datetime.date(2022, 1, 15),
            transaction_type=TransactionType.BUY,
        )
        self._create_stock_price(
            ticker="AAPL",
            price=150.00,
            transaction_date=datetime.date(2023, 12, 15),
        )

        fetcher = CompanyStockPriceFetcher(self.company, 2023)
        result = fetcher.get_year_last_stock_price()

        self.assertIsNotNone(result)
        self.assertEqual(result.price.amount, Decimal("150.00"))

    def test_returns_none_when_year_before_first_transaction(self):
        """Should return None when year is before company's first transaction."""
        self._create_shares_transaction(
            transaction_date=datetime.date(2023, 1, 15),
            transaction_type=TransactionType.BUY,
        )

        fetcher = CompanyStockPriceFetcher(self.company, 2020)
        result = fetcher.get_year_last_stock_price()

        self.assertIsNone(result)

    def test_fetches_from_api_when_update_flag_set(self):
        """Should fetch from API when update_api_price is True."""
        self._create_shares_transaction(
            transaction_date=datetime.date(2022, 1, 15),
            transaction_type=TransactionType.BUY,
        )
        self._create_stock_price(
            ticker="AAPL",
            price=150.00,
            transaction_date=datetime.date(2023, 12, 15),
        )

        mock_price = MagicMock()
        mock_price.price.amount = Decimal("160.00")

        with patch("stock_prices.fetchers.StockPricesService") as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.get_last_data_from_year.return_value = mock_price

            fetcher = CompanyStockPriceFetcher(
                self.company, 2023, update_api_price=True
            )
            result = fetcher.get_year_last_stock_price()

        self.assertIsNotNone(result)
        mock_service.get_last_data_from_year.assert_called_once()

    def test_returns_none_when_no_prices_available(self):
        """Should return None when no prices exist and API returns nothing."""
        self._create_shares_transaction(
            transaction_date=datetime.date(2022, 1, 15),
            transaction_type=TransactionType.BUY,
        )

        with patch("stock_prices.fetchers.StockPricesService") as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.get_last_data_from_year.return_value = None

            fetcher = CompanyStockPriceFetcher(self.company, 2023)
            result = fetcher.get_year_last_stock_price()

        self.assertIsNone(result)


class ClosedCompanyFetcherTestCase(CompanyStockPriceFetcherTestCase):
    """Tests for closed company scenarios."""

    def setUp(self):
        super().setUp()
        self.company.is_closed = True
        self.company.save()

    def test_uses_last_sell_dates_for_closed_company(self):
        """Should use last sell transaction dates for closed companies."""
        self._create_shares_transaction(
            transaction_date=datetime.date(2021, 1, 15),
            transaction_type=TransactionType.BUY,
        )
        self._create_shares_transaction(
            transaction_date=datetime.date(2023, 6, 15),
            transaction_type=TransactionType.SELL,
        )

        fetcher = CompanyStockPriceFetcher(self.company, 2023)
        from_date, to_date = fetcher.get_start_end_dates_for_year(2023)

        self.assertEqual(from_date, "2023-06-15")
        self.assertEqual(to_date, "2023-06-16")
