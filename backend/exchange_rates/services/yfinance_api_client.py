import logging
from datetime import datetime, timedelta
from typing import Union

from stock_prices.services.yfinance_api_client import YFinanceApiClient

logger = logging.getLogger("buho_backend")


class YFinanceExchangeClient:
    def get_exchange_rate_for_date(
        self, from_currency: str, to_currency: str, exchange_date: datetime
    ) -> Union[dict, None]:
        logger.debug(
            f"Call the Yfinance exchange lib. From: {from_currency} To: {to_currency} "
            f"Date: {exchange_date}."
        )

        ticker = f"{from_currency}{to_currency}=X"
        api_client = YFinanceApiClient()
        # exchange_date - 1 day
        previous_day = (exchange_date - timedelta(days=1)).strftime("%Y-%m-%d")
        # exchange_date + 1 day
        next_day = (exchange_date + timedelta(days=1)).strftime("%Y-%m-%d")
        exchange_rate_dict = api_client.get_company_data_between_dates(
            ticker, previous_day, next_day
        )

        # Get the close value for the first key of the dict
        logger.debug((exchange_rate_dict[0]))
        if exchange_rate_dict and exchange_rate_dict[0]:
            first_date = list(exchange_rate_dict[0].keys())[
                0
            ]  # Get the first column name
            logger.debug(first_date)
            value = exchange_rate_dict[0][first_date][("Close", ticker)]

            # Return as formatted dict
            parsed_dict = self.exchange_rate_as_dict(
                from_currency, to_currency, exchange_date.strftime("%Y-%m-%d"), value
            )

            return parsed_dict
        return None

    def exchange_rate_as_dict(
        self,
        from_currency: str,
        to_currency: str,
        exchange_date: str,
        exchange_rate_value: float,
    ) -> dict:
        data = {
            "exchange_from": from_currency,
            "exchange_to": to_currency,
            "exchange_date": exchange_date,
            "exchange_rate": exchange_rate_value,
        }
        return data
