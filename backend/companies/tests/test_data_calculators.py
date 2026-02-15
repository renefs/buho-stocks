import datetime
from decimal import Decimal

from buho_backend.tests.base_test_case import BaseApiTestCase
from buho_backend.transaction_types import TransactionType
from companies.data_calculators import CompanyDataCalculator
from companies.tests.factory import CompanyFactory
from dividends_transactions.tests.factory import DividendsTransactionFactory
from portfolios.tests.factory import PortfolioFactory
from shares_transactions.tests.factory import SharesTransactionFactory


class CompanyDataCalculatorTestCase(BaseApiTestCase):
    """Tests for CompanyDataCalculator class."""

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

    def _create_dividend_transaction(
        self,
        total_amount=50,
        total_commission=2,
        transaction_date=None,
    ):
        """Helper to create a dividend transaction."""
        if transaction_date is None:
            transaction_date = datetime.date(2023, 6, 15)

        return DividendsTransactionFactory.create(
            company=self.company,
            total_amount_currency=self.company.dividends_currency,
            total_commission_currency=self.company.dividends_currency,
            total_amount=total_amount,
            total_commission=total_commission,
            exchange_rate=1,
            transaction_date=transaction_date,
        )


class CalculateTotalInvestedOnYearTestCase(CompanyDataCalculatorTestCase):
    """Tests for calculate_total_invested_on_year method."""

    def test_returns_zero_when_no_transactions(self):
        """Should return 0 when there are no transactions."""
        calculator = CompanyDataCalculator(self.company.id)
        result = calculator.calculate_total_invested_on_year(2023)
        self.assertEqual(result, Decimal(0))

    def test_calculates_invested_for_single_transaction(self):
        """Should calculate total invested for a single transaction."""
        self._create_shares_transaction(
            count=10,
            gross_price_per_share=10,
            total_amount=100,
            total_commission=5,
            transaction_date=datetime.date(2023, 1, 15),
        )

        calculator = CompanyDataCalculator(self.company.id)
        result = calculator.calculate_total_invested_on_year(2023)
        # Invested = total_amount - commission = 100 - 5 = 95
        self.assertEqual(result, Decimal(95))

    def test_calculates_invested_for_multiple_transactions(self):
        """Should sum investments from multiple transactions in same year."""
        self._create_shares_transaction(
            count=10,
            gross_price_per_share=10,
            total_amount=100,
            total_commission=5,
            transaction_date=datetime.date(2023, 1, 15),
        )
        self._create_shares_transaction(
            count=20,
            gross_price_per_share=5,
            total_amount=100,
            total_commission=10,
            transaction_date=datetime.date(2023, 6, 15),
        )

        calculator = CompanyDataCalculator(self.company.id)
        result = calculator.calculate_total_invested_on_year(2023)
        # (100 - 5) + (100 - 10) = 95 + 90 = 185
        self.assertEqual(result, Decimal(185))

    def test_excludes_transactions_from_other_years(self):
        """Should only include transactions from the specified year."""
        self._create_shares_transaction(
            count=10,
            gross_price_per_share=10,
            total_amount=100,
            total_commission=5,
            transaction_date=datetime.date(2022, 1, 15),
        )
        self._create_shares_transaction(
            count=10,
            gross_price_per_share=10,
            total_amount=100,
            total_commission=5,
            transaction_date=datetime.date(2023, 1, 15),
        )

        calculator = CompanyDataCalculator(self.company.id)
        result = calculator.calculate_total_invested_on_year(2023)
        self.assertEqual(result, Decimal(95))


class CalculateAccumulatedInvestmentUntilYearTestCase(CompanyDataCalculatorTestCase):
    """Tests for calculate_accumulated_investment_until_year method."""

    def test_returns_zero_when_no_transactions(self):
        """Should return 0 when there are no transactions."""
        calculator = CompanyDataCalculator(self.company.id)
        result = calculator.calculate_accumulated_investment_until_year(2023)
        self.assertEqual(result, Decimal(0))

    def test_accumulates_investments_across_years(self):
        """Should accumulate investments from all years up to specified."""
        self._create_shares_transaction(
            count=10,
            gross_price_per_share=10,
            total_amount=100,
            total_commission=5,
            transaction_date=datetime.date(2021, 1, 15),
        )
        self._create_shares_transaction(
            count=10,
            gross_price_per_share=10,
            total_amount=100,
            total_commission=5,
            transaction_date=datetime.date(2022, 1, 15),
        )
        self._create_shares_transaction(
            count=10,
            gross_price_per_share=10,
            total_amount=100,
            total_commission=5,
            transaction_date=datetime.date(2023, 1, 15),
        )

        calculator = CompanyDataCalculator(self.company.id)
        result = calculator.calculate_accumulated_investment_until_year(2023)
        # 95 * 3 = 285
        self.assertEqual(result, Decimal(285))


class CalculateAccumulatedSharesCountUntilYearTestCase(CompanyDataCalculatorTestCase):
    """Tests for calculate_accumulated_shares_count_until_year method."""

    def test_returns_zero_when_no_transactions(self):
        """Should return 0 when there are no transactions."""
        calculator = CompanyDataCalculator(self.company.id)
        result = calculator.calculate_accumulated_shares_count_until_year(2023)
        self.assertEqual(result, 0)

    def test_counts_shares_from_buy_transactions(self):
        """Should count shares from buy transactions."""
        self._create_shares_transaction(
            count=10,
            transaction_date=datetime.date(2021, 1, 15),
            transaction_type=TransactionType.BUY,
        )
        self._create_shares_transaction(
            count=20,
            transaction_date=datetime.date(2022, 1, 15),
            transaction_type=TransactionType.BUY,
        )

        calculator = CompanyDataCalculator(self.company.id)
        result = calculator.calculate_accumulated_shares_count_until_year(2023)
        self.assertEqual(result, 30)

    def test_subtracts_shares_from_sell_transactions(self):
        """Should subtract shares from sell transactions."""
        self._create_shares_transaction(
            count=20,
            transaction_date=datetime.date(2021, 1, 15),
            transaction_type=TransactionType.BUY,
        )
        self._create_shares_transaction(
            count=10,
            transaction_date=datetime.date(2022, 1, 15),
            transaction_type=TransactionType.SELL,
        )

        calculator = CompanyDataCalculator(self.company.id)
        result = calculator.calculate_accumulated_shares_count_until_year(2023)
        self.assertEqual(result, 10)


class CalculateDividendsOfYearTestCase(CompanyDataCalculatorTestCase):
    """Tests for calculate_dividends_of_year method."""

    def test_returns_zero_when_no_dividends(self):
        """Should return 0 when there are no dividend transactions."""
        calculator = CompanyDataCalculator(self.company.id)
        result = calculator.calculate_dividends_of_year(2023)
        self.assertEqual(result, Decimal(0))

    def test_calculates_dividends_for_year(self):
        """Should calculate dividends for the specified year."""
        self._create_dividend_transaction(
            total_amount=50,
            total_commission=2,
            transaction_date=datetime.date(2023, 3, 15),
        )
        self._create_dividend_transaction(
            total_amount=60,
            total_commission=3,
            transaction_date=datetime.date(2023, 6, 15),
        )

        calculator = CompanyDataCalculator(self.company.id)
        result = calculator.calculate_dividends_of_year(2023)
        # (50 - 2) + (60 - 3) = 48 + 57 = 105
        self.assertEqual(result, Decimal(105))

    def test_excludes_dividends_from_other_years(self):
        """Should only include dividends from the specified year."""
        self._create_dividend_transaction(
            total_amount=50,
            total_commission=2,
            transaction_date=datetime.date(2022, 6, 15),
        )
        self._create_dividend_transaction(
            total_amount=60,
            total_commission=3,
            transaction_date=datetime.date(2023, 6, 15),
        )

        calculator = CompanyDataCalculator(self.company.id)
        result = calculator.calculate_dividends_of_year(2023)
        self.assertEqual(result, Decimal(57))


class CalculateAccumulatedDividendsUntilYearTestCase(CompanyDataCalculatorTestCase):
    """Tests for calculate_accumulated_dividends_until_year method."""

    def test_returns_zero_when_no_dividends(self):
        """Should return 0 when there are no dividends."""
        calculator = CompanyDataCalculator(self.company.id)
        result = calculator.calculate_accumulated_dividends_until_year(2023)
        self.assertEqual(result, Decimal(0))

    def test_accumulates_dividends_across_years(self):
        """Should accumulate dividends from all years up to specified."""
        self._create_dividend_transaction(
            total_amount=50,
            total_commission=2,
            transaction_date=datetime.date(2021, 6, 15),
        )
        self._create_dividend_transaction(
            total_amount=60,
            total_commission=3,
            transaction_date=datetime.date(2022, 6, 15),
        )
        self._create_dividend_transaction(
            total_amount=70,
            total_commission=4,
            transaction_date=datetime.date(2023, 6, 15),
        )

        calculator = CompanyDataCalculator(self.company.id)
        result = calculator.calculate_accumulated_dividends_until_year(2023)
        # (50-2) + (60-3) + (70-4) = 48 + 57 + 66 = 171
        self.assertEqual(result, Decimal(171))


class CalculateReturnYieldOnYearTestCase(CompanyDataCalculatorTestCase):
    """Tests for calculate_return_yield_on_year method."""

    def test_returns_zero_when_no_investment(self):
        """Should return 0 when there is no investment."""
        calculator = CompanyDataCalculator(self.company.id)
        result = calculator.calculate_return_yield_on_year(2023)
        self.assertEqual(result, Decimal(0))


class CalculateReturnYieldWithDividendsOnYearTestCase(CompanyDataCalculatorTestCase):
    """Tests for calculate_return_yield_with_dividends_on_year method."""

    def test_returns_zero_when_no_investment(self):
        """Should return 0 when there is no investment."""
        calculator = CompanyDataCalculator(self.company.id)
        result = calculator.calculate_return_yield_with_dividends_on_year(2023)
        self.assertEqual(result, Decimal(0))


class CalculateDividendsYieldOnYearTestCase(CompanyDataCalculatorTestCase):
    """Tests for calculate_dividends_yield_on_year method."""

    def test_returns_zero_when_no_company_value(self):
        """Should return 0 when company value is 0."""
        calculator = CompanyDataCalculator(self.company.id)
        result = calculator.calculate_dividends_yield_on_year(2023)
        self.assertEqual(result, Decimal(0))


class CalculateAccumulatedDividendsYieldTestCase(CompanyDataCalculatorTestCase):
    """Tests for calculate_accummulated_dividends_yield method."""

    def test_returns_zero_when_no_company_value(self):
        """Should return 0 when company value is 0."""
        calculator = CompanyDataCalculator(self.company.id)
        result = calculator.calculate_accummulated_dividends_yield(2023)
        self.assertEqual(result, Decimal(0))


class CalculateReturnOnYearTestCase(CompanyDataCalculatorTestCase):
    """Tests for calculate_return_on_year method."""

    def test_returns_negative_investment_when_no_value(self):
        """Should return negative of investment when no company value."""
        self._create_shares_transaction(
            count=10,
            gross_price_per_share=10,
            total_amount=100,
            total_commission=5,
            transaction_date=datetime.date(2023, 1, 15),
        )

        calculator = CompanyDataCalculator(self.company.id)
        result = calculator.calculate_return_on_year(2023)
        # Company value = 0, investment = 95
        # Return = 0 - 95 = -95
        self.assertEqual(result, Decimal(-95))


class CalculateReturnWithDividendsOnYearTestCase(CompanyDataCalculatorTestCase):
    """Tests for calculate_return_with_dividends_on_year method."""

    def test_includes_dividends_in_return(self):
        """Should add dividends to the return calculation."""
        self._create_shares_transaction(
            count=10,
            gross_price_per_share=10,
            total_amount=100,
            total_commission=5,
            transaction_date=datetime.date(2023, 1, 15),
        )
        self._create_dividend_transaction(
            total_amount=30,
            total_commission=2,
            transaction_date=datetime.date(2023, 6, 15),
        )

        calculator = CompanyDataCalculator(self.company.id)
        result = calculator.calculate_return_with_dividends_on_year(2023)
        # Company value = 0, investment = 95, dividends = 28
        # Return = 0 - 95 + 28 = -67
        self.assertEqual(result, Decimal(-67))
