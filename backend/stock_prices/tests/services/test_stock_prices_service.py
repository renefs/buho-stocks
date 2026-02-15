import datetime
from decimal import Decimal
from unittest.mock import patch

from buho_backend.tests.base_test_case import BaseApiTestCase
from stock_prices.models import StockPrice
from stock_prices.services.stock_prices_service import StockPricesService


class StockPricesServiceTestCase(BaseApiTestCase):
    """Tests for StockPricesService class."""

    def setUp(self):
        super().setUp()
        self.service = StockPricesService()

    def _create_stock_price(
        self,
        ticker="AAPL",
        price=150.00,
        transaction_date=None,
    ):
        """Helper to create a stock price in the database."""
        if transaction_date is None:
            transaction_date = datetime.date(2023, 6, 15)

        return StockPrice.objects.create(
            ticker=ticker,
            price=price,
            price_currency="USD",
            transaction_date=transaction_date,
        )


class GetLastDataFromYearTestCase(StockPricesServiceTestCase):
    """Tests for get_last_data_from_year method."""

    def test_returns_last_price_from_db(self):
        """Should return the last stock price from the database when available."""
        self._create_stock_price(
            ticker="AAPL",
            price=150.00,
            transaction_date=datetime.date(2023, 6, 10),
        )
        self._create_stock_price(
            ticker="AAPL",
            price=155.00,
            transaction_date=datetime.date(2023, 6, 15),
        )
        self._create_stock_price(
            ticker="AAPL",
            price=152.00,
            transaction_date=datetime.date(2023, 6, 12),
        )

        from_date = datetime.datetime(2023, 6, 1)
        to_date = datetime.datetime(2023, 6, 30)

        result = self.service.get_last_data_from_year("AAPL", from_date, to_date)

        self.assertIsNotNone(result)
        # Should return the last one by date (June 15th)
        self.assertEqual(result.price.amount, Decimal("155.00"))

    def test_returns_none_when_no_prices(self):
        """Should return None when no stock prices exist."""
        from_date = datetime.datetime(2023, 6, 1)
        to_date = datetime.datetime(2023, 6, 30)

        with patch.object(
            self.service.api_client, "get_stock_prices_list", return_value=[]
        ):
            result = self.service.get_last_data_from_year("AAPL", from_date, to_date)

        self.assertIsNone(result)

    def test_fetches_from_api_when_update_api_price_true(self):
        """Should fetch from API when update_api_price is True."""
        # Create existing price
        self._create_stock_price(
            ticker="AAPL",
            price=150.00,
            transaction_date=datetime.date(2023, 6, 15),
        )

        from_date = datetime.datetime(2023, 6, 1)
        to_date = datetime.datetime(2023, 6, 30)

        mock_api_response = [
            {
                "ticker": "AAPL",
                "price": 160.00,
                "price_currency": "USD",
                "transaction_date": "2023-06-20",
            }
        ]

        with patch.object(
            self.service.api_client,
            "get_stock_prices_list",
            return_value=mock_api_response,
        ):
            result = self.service.get_last_data_from_year(
                "AAPL", from_date, to_date, update_api_price=True
            )

        # Should have fetched from API
        self.assertIsNotNone(result)
        self.assertEqual(result.price.amount, Decimal("160.00"))


class GetLastDataFromLastMonthTestCase(StockPricesServiceTestCase):
    """Tests for get_last_data_from_last_month method."""

    def test_returns_price_from_last_month(self):
        """Should return stock price from the last month."""
        # Create price from recent days
        recent_date = datetime.date.today() - datetime.timedelta(days=5)
        self._create_stock_price(
            ticker="MSFT",
            price=350.00,
            transaction_date=recent_date,
        )
        older_date = datetime.date.today() - datetime.timedelta(days=10)
        self._create_stock_price(
            ticker="MSFT",
            price=345.00,
            transaction_date=older_date,
        )

        result = self.service.get_last_data_from_last_month("MSFT")

        self.assertIsNotNone(result)

    def test_returns_none_when_no_recent_prices(self):
        """Should return None when no prices in the last month."""
        with patch.object(
            self.service.api_client, "get_stock_prices_list", return_value=[]
        ):
            result = self.service.get_last_data_from_last_month("UNKNOWN")

        self.assertIsNone(result)


class GetHistoricalDataTestCase(StockPricesServiceTestCase):
    """Tests for _get_historical_data method."""

    def test_returns_prices_from_db_when_available(self):
        """Should return prices from database when they exist."""
        self._create_stock_price(
            ticker="GOOG",
            price=140.00,
            transaction_date=datetime.date(2023, 5, 10),
        )
        self._create_stock_price(
            ticker="GOOG",
            price=142.00,
            transaction_date=datetime.date(2023, 5, 15),
        )

        result = self.service._get_historical_data("GOOG", "2023-05-01", "2023-05-31")

        self.assertEqual(len(result), 2)

    def test_fetches_from_api_when_no_local_prices(self):
        """Should fetch from API when no local prices exist."""
        mock_api_response = [
            {
                "ticker": "AMZN",
                "price": 130.00,
                "price_currency": "USD",
                "transaction_date": "2023-05-10",
            },
            {
                "ticker": "AMZN",
                "price": 132.00,
                "price_currency": "USD",
                "transaction_date": "2023-05-15",
            },
        ]

        with patch.object(
            self.service.api_client,
            "get_stock_prices_list",
            return_value=mock_api_response,
        ):
            result = self.service._get_historical_data(
                "AMZN", "2023-05-01", "2023-05-31"
            )

        self.assertEqual(len(result), 2)
        # Verify prices were saved to DB
        db_prices = StockPrice.objects.filter(ticker="AMZN").count()
        self.assertEqual(db_prices, 2)

    def test_dry_run_does_not_save_to_db(self):
        """Should not save to database when dry_run is True."""
        mock_api_response = [
            {
                "ticker": "META",
                "price": 300.00,
                "price_currency": "USD",
                "transaction_date": "2023-05-10",
            }
        ]

        with patch.object(
            self.service.api_client,
            "get_stock_prices_list",
            return_value=mock_api_response,
        ):
            result = self.service._get_historical_data(
                "META", "2023-05-01", "2023-05-31", dry_run=True
            )

        # Should return empty list in dry run mode
        self.assertEqual(len(result), 0)
        # Should NOT have saved to DB
        db_prices = StockPrice.objects.filter(ticker="META").count()
        self.assertEqual(db_prices, 0)

    def test_updates_existing_price_from_api(self):
        """Should update existing price when fetching from API."""
        # Create existing price
        existing_price = self._create_stock_price(
            ticker="NVDA",
            price=400.00,
            transaction_date=datetime.date(2023, 5, 10),
        )
        original_id = existing_price.id

        mock_api_response = [
            {
                "ticker": "NVDA",
                "price": 420.00,
                "price_currency": "USD",
                "transaction_date": "2023-05-10",
            }
        ]

        with patch.object(
            self.service.api_client,
            "get_stock_prices_list",
            return_value=mock_api_response,
        ):
            result = self.service._get_historical_data(
                "NVDA", "2023-05-01", "2023-05-31", update_api_price=True
            )

        # Should have updated the existing price
        self.assertEqual(len(result), 1)
        updated_price = StockPrice.objects.get(id=original_id)
        self.assertEqual(updated_price.price.amount, Decimal("420.00"))

    def test_handles_api_returning_empty_list(self):
        """Should handle API returning empty list gracefully."""
        with patch.object(
            self.service.api_client, "get_stock_prices_list", return_value=[]
        ):
            result = self.service._get_historical_data(
                "EMPTY", "2023-05-01", "2023-05-31"
            )

        self.assertEqual(len(result), 0)

    def test_returns_all_prices_in_date_range(self):
        """Should return only prices within the specified date range."""
        # Create prices inside range
        self._create_stock_price(
            ticker="TSLA",
            price=250.00,
            transaction_date=datetime.date(2023, 5, 10),
        )
        self._create_stock_price(
            ticker="TSLA",
            price=255.00,
            transaction_date=datetime.date(2023, 5, 20),
        )
        # Create price outside range
        self._create_stock_price(
            ticker="TSLA",
            price=260.00,
            transaction_date=datetime.date(2023, 6, 5),
        )

        result = self.service._get_historical_data("TSLA", "2023-05-01", "2023-05-31")

        self.assertEqual(len(result), 2)
