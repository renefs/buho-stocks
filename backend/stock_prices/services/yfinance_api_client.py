import logging
import time
from typing import Any, Tuple

import requests_cache
import yfinance as yf
from django.conf import settings
from pandas import Timestamp  # type: ignore
from random_user_agent.params import OperatingSystem, SoftwareName
from random_user_agent.user_agent import UserAgent
from redis import Redis
from requests import Session
from requests_cache import CacheMixin
from requests_ratelimiter import Duration, Limiter, LimiterMixin, Rate

from stock_prices.services.types import TypedStockPrice


class CachedLimiterSession(CacheMixin, LimiterMixin, Session):
    pass


connection = Redis(host=settings.REDIS_HOSTNAME, port=settings.REDIS_PORT)
backend = requests_cache.RedisCache(connection=connection)

software_names = [SoftwareName.CHROME.value, SoftwareName.FIREFOX.value]
operating_systems = [
    OperatingSystem.WINDOWS.value,
    OperatingSystem.LINUX.value,
    OperatingSystem.MAC_OS_X.value,
]
user_agent_rotator = UserAgent(
    software_names=software_names, operating_systems=operating_systems, limit=100
)
user_agents = user_agent_rotator.get_user_agents()
user_agent = user_agent_rotator.get_random_user_agent()

session = CachedLimiterSession(
    cache_name="yfinance.cache",
    limiter=Limiter(Rate(2, Duration.SECOND * 5)),  # max 2 requests per 5 seconds
    backend=backend,
)

session.headers["User-agent"] = user_agent

logger = logging.getLogger("buho_backend")


class YFinanceApiClient:
    def __init__(self, wait_time=2):
        self.wait_time = wait_time

    def get_company_info_by_ticker(self, ticker: str) -> dict | None:
        company = yf.Ticker(ticker, session=session)
        if not company:
            logger.warning(f"{ticker}: Company not found.")
            return None
        logger.info(f"{ticker} company.")
        isin = company.isin
        info: dict = company.info
        info["isin"] = isin

        return info

    def get_stock_prices_list(
        self, ticker: str, start_date: str, end_date: str
    ) -> list[TypedStockPrice]:
        prices = []
        time.sleep(self.wait_time)

        results, currency = self.get_company_data_between_dates(
            ticker, start_date, end_date
        )

        if results is None:
            return []

        for price_date in results:
            try:
                if not currency:
                    break
                element_values = results[price_date]
                data = self.get_formatted_price_dict(
                    ticker, currency, price_date, element_values
                )
                prices.append(data)

            except (KeyError, TypeError) as error:
                logger.warning(
                    f"{ticker}: close or date fields not found: {error}. Skipping."
                )

        prices.sort(key=lambda x: x["transaction_date"], reverse=False)
        return prices

    def get_formatted_price_dict(
        self,
        ticker: str,
        currency: str,
        price_date: Timestamp,
        element_values: dict,
    ) -> TypedStockPrice:
        price = element_values[("Close", ticker)]
        if currency == "GBP":
            price = self.convert_price_to_gbp(price)

        price = round(price, 3)
        converted_date = price_date.to_pydatetime().date()
        formatted_date = converted_date.strftime("%Y-%m-%d")
        transaction_date = formatted_date
        data: TypedStockPrice = {
            "price": price,
            "price_currency": currency,
            "ticker": ticker,
            "transaction_date": transaction_date,
        }

        return data

    def convert_price_to_gbp(self, price):
        price = price / 100
        return price

    def get_company_currency(self, ticker: str) -> str:
        company = yf.Ticker(ticker, session=session)
        if not company:
            logger.warning(f"{ticker}: Company not found.")
        try:
            currency: str = company.fast_info["currency"]
            currency = currency.upper()
            return currency
        except KeyError as error:
            logger.error(f"{ticker}: Currency not found.")
            raise error

    def convert_api_data_to_dict(self, api_data: Any) -> dict | None:
        result = api_data.sort_values("Date", ascending=False)
        dates_dict: dict = result.to_dict("index")
        if dates_dict == {}:
            return None
        return dates_dict

    def get_company_data_between_dates(
        self, ticker: str, from_date: str, to_date: str
    ) -> tuple[dict[Timestamp, dict] | None, str] | Tuple[None, None]:
        try:
            currency = self.get_company_currency(ticker)
            result = yf.download(ticker, start=from_date, end=to_date, session=session)
            result_as_dict = self.convert_api_data_to_dict(result)
            return result_as_dict, currency

        except (IndexError, TypeError, KeyError) as error:
            logger.warning(f"{ticker}: Error: {error}. Skipping.")
            return None, None
