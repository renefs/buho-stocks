import datetime
import logging
from decimal import Decimal

from faker import Faker

from buho_backend.tests.base_test_case import BaseApiTestCase
from exchange_rates.services.exchange_rate_fetcher import ExchangeRateFetcher
from exchange_rates.tests.factory import ExchangeRateFactory
from stock_prices.tests.mocks.mock_yfinance import (
    create_download_mock_df,
    create_empty_download_mock_df,
)

logger = logging.getLogger("buho_backend")


class ExchangeRateFetcherTestCase(BaseApiTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.faker_obj = Faker()
        instances = []
        self.years = [2018, 2020, 2021, 2022]
        self.exchange_dates = [
            "2018-01-01",
            "2020-01-01",
            "2021-01-01",
            "2022-01-01",
        ]
        self.not_found_date = datetime.datetime.strptime(
            f"{self.years[3]}-08-04", "%Y-%m-%d"
        )
        self.exchange_rates = [Decimal(10), Decimal(20), Decimal(30), Decimal(40)]
        self.from_currency = "USD"
        self.to_currency = "EUR"
        for index in range(0, 4):
            first_datetime = self.exchange_dates[index]
            instance = ExchangeRateFactory.create(
                exchange_from=self.from_currency,
                exchange_to=self.to_currency,
                exchange_rate=self.exchange_rates[index],
                exchange_date=first_datetime,
            )
            instances.append(instance)
        self.instances = instances

    def test_get_exchange_rate_for_date(self):
        index = 3
        service = ExchangeRateFetcher()
        rate = service.get_exchange_rate_for_date(
            self.from_currency, self.to_currency, self.exchange_dates[index]
        )
        if not rate:
            self.fail("Rate not found")
        self.assertEqual(
            rate.exchange_from,
            self.from_currency,
        )
        self.assertEqual(
            rate.exchange_to,
            self.to_currency,
        )

        # convert self.exchange_dates[index] to datetime.date
        date = datetime.datetime.strptime(self.exchange_dates[index], "%Y-%m-%d").date()
        self.assertEqual(
            rate.exchange_date,
            date,
        )
        self.assertEqual(
            rate.exchange_rate,
            self.exchange_rates[index],
        )

    def test_get_exchange_rate_for_date_same_currency(self):
        index = 3
        same_currency_exchange_rate = {
            "exchange_from": "USD",
            "exchange_to": "USD",
            "exchange_date": "2022-01-01",
            "exchange_rate": "1.000",
        }
        service = ExchangeRateFetcher()
        value = service.get_exchange_rate_for_date(
            self.from_currency, self.from_currency, self.exchange_dates[index]
        )

        if not value:
            self.fail("Rate not found")

        self.assertEqual(
            value.exchange_from,
            same_currency_exchange_rate["exchange_from"],
        )

        self.assertEqual(
            value.exchange_to,
            same_currency_exchange_rate["exchange_to"],
        )

        self.assertEqual(
            value.exchange_date,
            same_currency_exchange_rate["exchange_date"],
        )
        self.assertEqual(
            value.exchange_rate,
            same_currency_exchange_rate["exchange_rate"],
        )

    def test_get_exchange_rate_not_found_in_db(self):
        # Set up mock with correct ticker for exchange rate
        ticker = f"{self.from_currency}{self.to_currency}=X"
        self.mock_download.return_value = create_download_mock_df(ticker)

        service = ExchangeRateFetcher()
        result = service.get_exchange_rate_for_date(
            self.from_currency, self.to_currency, self.not_found_date
        )

        if not result:
            self.fail("Rate not found")

        self.assertEqual(result.exchange_from, "USD")
        self.assertEqual(result.exchange_to, "EUR")
        self.assertEqual(result.exchange_rate, 120)

    def test_get_exchange_rate_not_found_at_all(self):
        service = ExchangeRateFetcher()
        self.mock_download.return_value = create_empty_download_mock_df()
        result = service.get_exchange_rate_for_date(
            "ABCDE", self.to_currency, self.not_found_date
        )
        self.assertIsNone(result)
