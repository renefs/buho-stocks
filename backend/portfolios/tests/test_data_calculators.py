import datetime
from decimal import Decimal

from buho_backend.tests.base_test_case import BaseApiTestCase
from buho_backend.transaction_types import TransactionType
from companies.tests.factory import CompanyFactory
from dividends_transactions.tests.factory import DividendsTransactionFactory
from portfolios.data_calculators import PortfolioDataCalculator
from portfolios.tests.factory import PortfolioFactory
from shares_transactions.tests.factory import SharesTransactionFactory


class PortfolioDataCalculatorTestCase(BaseApiTestCase):
    """Tests for PortfolioDataCalculator class."""

    def setUp(self):
        super().setUp()
        self.portfolio = PortfolioFactory.create(base_currency="EUR")

    def _create_company(self, is_closed=False):
        """Helper to create a company in the portfolio."""
        return CompanyFactory.create(
            portfolio=self.portfolio,
            base_currency="EUR",
            dividends_currency="EUR",
            is_closed=is_closed,
        )

    def _create_shares_transaction(
        self,
        company,
        count=10,
        gross_price_per_share=10,
        total_amount=None,
        total_commission=5,
        transaction_date=None,
        transaction_type=TransactionType.BUY,
    ):
        """Helper to create a shares transaction."""
        if transaction_date is None:
            transaction_date = datetime.date(2023, 1, 15)

        if total_amount is None:
            total_amount = count * gross_price_per_share

        return SharesTransactionFactory.create(
            company=company,
            gross_price_per_share_currency=company.base_currency,
            total_commission_currency=company.base_currency,
            count=count,
            gross_price_per_share=gross_price_per_share,
            total_amount=total_amount,
            total_commission=total_commission,
            exchange_rate=1,
            type=transaction_type,
            transaction_date=transaction_date,
        )

    def _create_dividend_transaction(
        self,
        company,
        total_amount=50,
        total_commission=2,
        transaction_date=None,
    ):
        """Helper to create a dividend transaction."""
        if transaction_date is None:
            transaction_date = datetime.date(2023, 6, 15)

        return DividendsTransactionFactory.create(
            company=company,
            total_amount_currency=company.dividends_currency,
            total_commission_currency=company.dividends_currency,
            total_amount=total_amount,
            total_commission=total_commission,
            exchange_rate=1,
            transaction_date=transaction_date,
        )


class GetPortfolioFirstYearTestCase(PortfolioDataCalculatorTestCase):
    """Tests for get_portfolio_first_year method."""

    def test_returns_none_when_no_transactions(self):
        """Should return None when portfolio has no transactions."""
        calculator = PortfolioDataCalculator(self.portfolio.id)
        result = calculator.get_portfolio_first_year()
        self.assertIsNone(result)

    def test_returns_first_year_with_single_transaction(self):
        """Should return the year of the first transaction."""
        company = self._create_company()
        self._create_shares_transaction(
            company, transaction_date=datetime.date(2020, 3, 15)
        )

        calculator = PortfolioDataCalculator(self.portfolio.id)
        result = calculator.get_portfolio_first_year()
        self.assertEqual(result, 2020)

    def test_returns_earliest_year_with_multiple_transactions(self):
        """Should return the earliest year when there are multiple transactions."""
        company = self._create_company()
        self._create_shares_transaction(
            company, transaction_date=datetime.date(2022, 1, 1)
        )
        self._create_shares_transaction(
            company, transaction_date=datetime.date(2020, 6, 1)
        )
        self._create_shares_transaction(
            company, transaction_date=datetime.date(2021, 3, 1)
        )

        calculator = PortfolioDataCalculator(self.portfolio.id)
        result = calculator.get_portfolio_first_year()
        self.assertEqual(result, 2020)


class CalculateTotalInvestedOnYearTestCase(PortfolioDataCalculatorTestCase):
    """Tests for calculate_total_invested_on_year method."""

    def test_returns_zero_when_no_transactions(self):
        """Should return 0 when there are no transactions."""
        calculator = PortfolioDataCalculator(self.portfolio.id)
        result = calculator.calculate_total_invested_on_year(2023)
        self.assertEqual(result, Decimal(0))

    def test_calculates_invested_for_single_company(self):
        """Should calculate total invested for single company in a year."""
        company = self._create_company()
        # 10 shares * 10 price = 100 invested
        self._create_shares_transaction(
            company,
            count=10,
            gross_price_per_share=10,
            total_commission=5,
            transaction_date=datetime.date(2023, 1, 15),
        )

        calculator = PortfolioDataCalculator(self.portfolio.id)
        result = calculator.calculate_total_invested_on_year(2023)
        # Invested = count * price - commission = 100 - 5 = 95
        self.assertEqual(result, Decimal(95))

    def test_calculates_invested_for_multiple_companies(self):
        """Should calculate total invested across multiple companies."""
        company1 = self._create_company()
        company2 = self._create_company()

        self._create_shares_transaction(
            company1,
            count=10,
            gross_price_per_share=10,
            total_commission=5,
            transaction_date=datetime.date(2023, 1, 15),
        )
        self._create_shares_transaction(
            company2,
            count=20,
            gross_price_per_share=5,
            total_commission=10,
            transaction_date=datetime.date(2023, 2, 20),
        )

        calculator = PortfolioDataCalculator(self.portfolio.id)
        result = calculator.calculate_total_invested_on_year(2023)
        # Company1: 100 - 5 = 95, Company2: 100 - 10 = 90, Total = 185
        self.assertEqual(result, Decimal(185))

    def test_excludes_transactions_from_other_years(self):
        """Should only include transactions from the specified year."""
        company = self._create_company()
        self._create_shares_transaction(
            company,
            count=10,
            gross_price_per_share=10,
            total_commission=5,
            transaction_date=datetime.date(2022, 1, 15),
        )
        self._create_shares_transaction(
            company,
            count=20,
            gross_price_per_share=10,
            total_commission=10,
            transaction_date=datetime.date(2023, 1, 15),
        )

        calculator = PortfolioDataCalculator(self.portfolio.id)
        result = calculator.calculate_total_invested_on_year(2023)
        # Only 2023 transaction: 200 - 10 = 190
        self.assertEqual(result, Decimal(190))

    def test_includes_closed_companies(self):
        """Should include closed companies in calculations."""
        open_company = self._create_company(is_closed=False)
        closed_company = self._create_company(is_closed=True)

        self._create_shares_transaction(
            open_company,
            count=10,
            gross_price_per_share=10,
            total_commission=5,
            transaction_date=datetime.date(2023, 1, 15),
        )
        self._create_shares_transaction(
            closed_company,
            count=10,
            gross_price_per_share=10,
            total_commission=5,
            transaction_date=datetime.date(2023, 2, 15),
        )

        calculator = PortfolioDataCalculator(self.portfolio.id)
        result = calculator.calculate_total_invested_on_year(2023)
        # Both companies contribute: 95 + 95 = 190
        self.assertEqual(result, Decimal(190))


class CalculateAccumulatedInvestmentUntilYearTestCase(PortfolioDataCalculatorTestCase):
    """Tests for calculate_accumulated_investment_until_year method."""

    def test_returns_zero_when_no_transactions(self):
        """Should return 0 when there are no transactions."""
        calculator = PortfolioDataCalculator(self.portfolio.id)
        result = calculator.calculate_accumulated_investment_until_year(2023)
        self.assertEqual(result, Decimal(0))

    def test_accumulates_investments_across_years(self):
        """Should accumulate investments from all years up to specified year."""
        company = self._create_company()

        self._create_shares_transaction(
            company,
            count=10,
            gross_price_per_share=10,
            total_commission=5,
            transaction_date=datetime.date(2021, 1, 15),
        )
        self._create_shares_transaction(
            company,
            count=10,
            gross_price_per_share=10,
            total_commission=5,
            transaction_date=datetime.date(2022, 1, 15),
        )
        self._create_shares_transaction(
            company,
            count=10,
            gross_price_per_share=10,
            total_commission=5,
            transaction_date=datetime.date(2023, 1, 15),
        )

        calculator = PortfolioDataCalculator(self.portfolio.id)
        result = calculator.calculate_accumulated_investment_until_year(2023)
        # Each year: 100 - 5 = 95, Total: 95 * 3 = 285
        self.assertEqual(result, Decimal(285))

    def test_excludes_future_transactions(self):
        """Should exclude transactions after the specified year."""
        company = self._create_company()

        self._create_shares_transaction(
            company,
            count=10,
            gross_price_per_share=10,
            total_commission=5,
            transaction_date=datetime.date(2022, 1, 15),
        )
        self._create_shares_transaction(
            company,
            count=10,
            gross_price_per_share=10,
            total_commission=5,
            transaction_date=datetime.date(2024, 1, 15),
        )

        calculator = PortfolioDataCalculator(self.portfolio.id)
        result = calculator.calculate_accumulated_investment_until_year(2023)
        # Only 2022 transaction: 95
        self.assertEqual(result, Decimal(95))


class CalculateTotalDividendsOfYearTestCase(PortfolioDataCalculatorTestCase):
    """Tests for calculate_total_dividends_of_year method."""

    def test_returns_zero_when_no_dividends(self):
        """Should return 0 when there are no dividend transactions."""
        calculator = PortfolioDataCalculator(self.portfolio.id)
        result = calculator.calculate_total_dividends_of_year(2023)
        self.assertEqual(result, Decimal(0))

    def test_calculates_dividends_for_year(self):
        """Should calculate total dividends for the specified year."""
        company = self._create_company()
        self._create_dividend_transaction(
            company,
            total_amount=50,
            total_commission=2,
            transaction_date=datetime.date(2023, 3, 15),
        )
        self._create_dividend_transaction(
            company,
            total_amount=60,
            total_commission=3,
            transaction_date=datetime.date(2023, 6, 15),
        )

        calculator = PortfolioDataCalculator(self.portfolio.id)
        result = calculator.calculate_total_dividends_of_year(2023)
        # Dividends = (50 - 2) + (60 - 3) = 48 + 57 = 105
        self.assertEqual(result, Decimal(105))

    def test_excludes_dividends_from_other_years(self):
        """Should only include dividends from the specified year."""
        company = self._create_company()
        self._create_dividend_transaction(
            company,
            total_amount=50,
            total_commission=2,
            transaction_date=datetime.date(2022, 6, 15),
        )
        self._create_dividend_transaction(
            company,
            total_amount=75,
            total_commission=5,
            transaction_date=datetime.date(2023, 6, 15),
        )

        calculator = PortfolioDataCalculator(self.portfolio.id)
        result = calculator.calculate_total_dividends_of_year(2023)
        # Only 2023: 75 - 5 = 70
        self.assertEqual(result, Decimal(70))


class CalculateAccumulatedDividendsUntilYearTestCase(PortfolioDataCalculatorTestCase):
    """Tests for calculate_accumulated_dividends_until_year method."""

    def test_returns_zero_when_no_dividends(self):
        """Should return 0 when there are no dividend transactions."""
        calculator = PortfolioDataCalculator(self.portfolio.id)
        result = calculator.calculate_accumulated_dividends_until_year(2023)
        self.assertEqual(result, Decimal(0))

    def test_accumulates_dividends_across_years(self):
        """Should accumulate dividends from all years up to specified year."""
        company = self._create_company()
        self._create_dividend_transaction(
            company,
            total_amount=50,
            total_commission=2,
            transaction_date=datetime.date(2021, 6, 15),
        )
        self._create_dividend_transaction(
            company,
            total_amount=60,
            total_commission=3,
            transaction_date=datetime.date(2022, 6, 15),
        )
        self._create_dividend_transaction(
            company,
            total_amount=70,
            total_commission=4,
            transaction_date=datetime.date(2023, 6, 15),
        )

        calculator = PortfolioDataCalculator(self.portfolio.id)
        result = calculator.calculate_accumulated_dividends_until_year(2023)
        # (50-2) + (60-3) + (70-4) = 48 + 57 + 66 = 171
        self.assertEqual(result, Decimal(171))


class CalculateReturnYieldOnYearTestCase(PortfolioDataCalculatorTestCase):
    """Tests for calculate_return_yield_on_year method."""

    def test_returns_zero_when_no_investment(self):
        """Should return 0 when there is no accumulated investment."""
        calculator = PortfolioDataCalculator(self.portfolio.id)
        result = calculator.calculate_return_yield_on_year(2023)
        self.assertEqual(result, Decimal(0))


class CalculateReturnWithDividendsYieldOnYearTestCase(PortfolioDataCalculatorTestCase):
    """Tests for calculate_return_with_dividends_yield_on_year method."""

    def test_returns_zero_when_no_investment(self):
        """Should return 0 when there is no accumulated investment."""
        calculator = PortfolioDataCalculator(self.portfolio.id)
        result = calculator.calculate_return_with_dividends_yield_on_year(2023)
        self.assertEqual(result, Decimal(0))


class CalculateAccumulatedDividendsYieldTestCase(PortfolioDataCalculatorTestCase):
    """Tests for calculate_accummulated_dividends_yield method."""

    def test_returns_zero_when_no_portfolio_value(self):
        """Should return 0 when portfolio value is 0."""
        calculator = PortfolioDataCalculator(self.portfolio.id)
        result = calculator.calculate_accummulated_dividends_yield(2023)
        self.assertEqual(result, Decimal(0))


class CalculateDividendsYieldOnYearTestCase(PortfolioDataCalculatorTestCase):
    """Tests for calculate_dividends_yield_on_year method."""

    def test_returns_zero_when_no_portfolio_value(self):
        """Should return 0 when portfolio value is 0."""
        calculator = PortfolioDataCalculator(self.portfolio.id)
        result = calculator.calculate_dividends_yield_on_year(2023)
        self.assertEqual(result, Decimal(0))
