import datetime

from buho_backend.tests.base_test_case import BaseApiTestCase
from buho_backend.transaction_types import TransactionType
from companies.tests.factory import CompanyFactory
from companies.utils import get_company_first_year
from portfolios.tests.factory import PortfolioFactory
from shares_transactions.tests.factory import SharesTransactionFactory


class GetCompanyFirstYearTestCase(BaseApiTestCase):
    """Tests for get_company_first_year function."""

    def setUp(self):
        super().setUp()
        self.portfolio = PortfolioFactory.create(base_currency="EUR")
        self.company = CompanyFactory.create(
            portfolio=self.portfolio,
            base_currency="EUR",
            dividends_currency="EUR",
            is_closed=False,
        )

    def _create_shares_transaction(
        self,
        transaction_date,
        count=10,
        gross_price_per_share=10,
        total_commission=5,
        transaction_type=TransactionType.BUY,
    ):
        """Helper to create a shares transaction."""
        return SharesTransactionFactory.create(
            company=self.company,
            gross_price_per_share_currency=self.company.base_currency,
            total_commission_currency=self.company.base_currency,
            count=count,
            gross_price_per_share=gross_price_per_share,
            total_amount=count * gross_price_per_share,
            total_commission=total_commission,
            exchange_rate=1,
            type=transaction_type,
            transaction_date=transaction_date,
        )

    def test_returns_none_when_no_transactions(self):
        """Should return None when company has no transactions."""
        result = get_company_first_year(self.company.id)
        self.assertIsNone(result)

    def test_returns_year_of_first_transaction(self):
        """Should return the year of the first transaction."""
        self._create_shares_transaction(
            transaction_date=datetime.date(2020, 6, 15),
        )
        self._create_shares_transaction(
            transaction_date=datetime.date(2021, 3, 10),
        )
        self._create_shares_transaction(
            transaction_date=datetime.date(2022, 1, 5),
        )

        result = get_company_first_year(self.company.id)
        self.assertEqual(result, 2020)

    def test_returns_earliest_year_regardless_of_insertion_order(self):
        """Should return earliest year even if added later."""
        self._create_shares_transaction(
            transaction_date=datetime.date(2022, 1, 5),
        )
        self._create_shares_transaction(
            transaction_date=datetime.date(2020, 6, 15),
        )
        self._create_shares_transaction(
            transaction_date=datetime.date(2021, 3, 10),
        )

        result = get_company_first_year(self.company.id)
        self.assertEqual(result, 2020)

    def test_returns_none_for_nonexistent_company(self):
        """Should return None for company with no transactions."""
        # Use a company ID that doesn't have any transactions
        empty_company = CompanyFactory.create(
            portfolio=self.portfolio,
            base_currency="EUR",
            dividends_currency="EUR",
        )
        result = get_company_first_year(empty_company.id)
        self.assertIsNone(result)
