import datetime
from decimal import Decimal

from buho_backend.tests.base_test_case import BaseApiTestCase
from buho_backend.transaction_types import TransactionType
from companies.data_calculators_closed import CompanyClosedDataCalculator
from companies.tests.factory import CompanyFactory
from dividends_transactions.tests.factory import DividendsTransactionFactory
from portfolios.tests.factory import PortfolioFactory
from shares_transactions.tests.factory import SharesTransactionFactory


class CompanyClosedDataCalculatorTestCase(BaseApiTestCase):
    """Tests for CompanyClosedDataCalculator class."""

    def setUp(self):
        super().setUp()
        self.portfolio = PortfolioFactory.create(base_currency="EUR")
        self.company = CompanyFactory.create(
            portfolio=self.portfolio,
            base_currency="EUR",
            dividends_currency="EUR",
            is_closed=True,
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

    def _create_dividend_transaction(
        self,
        total_amount=50,
        total_commission=2,
        transaction_date=None,
    ):
        """Helper to create a dividend transaction."""
        if transaction_date is None:
            transaction_date = datetime.date(2021, 6, 15)

        return DividendsTransactionFactory.create(
            company=self.company,
            total_amount_currency=self.company.dividends_currency,
            total_commission_currency=self.company.dividends_currency,
            total_amount=total_amount,
            total_commission=total_commission,
            exchange_rate=1,
            transaction_date=transaction_date,
        )

    def _setup_closed_company_with_transactions(self):
        """Setup a typical closed company scenario with buy and sell transactions."""
        # Buy 10 shares at $10 each in 2021
        self._create_shares_transaction(
            count=10,
            gross_price_per_share=10,
            total_amount=100,
            total_commission=5,
            transaction_date=datetime.date(2021, 1, 15),
            transaction_type=TransactionType.BUY,
        )
        # Buy 10 more shares in 2022
        self._create_shares_transaction(
            count=10,
            gross_price_per_share=12,
            total_amount=120,
            total_commission=5,
            transaction_date=datetime.date(2022, 1, 15),
            transaction_type=TransactionType.BUY,
        )
        # Sell all 20 shares in 2023 (closing the position)
        self._create_shares_transaction(
            count=20,
            gross_price_per_share=15,
            total_amount=300,
            total_commission=10,
            transaction_date=datetime.date(2023, 6, 15),
            transaction_type=TransactionType.SELL,
        )


class CalculateTotalInvestedOnYearForPortfolioTestCase(
    CompanyClosedDataCalculatorTestCase
):
    """Tests for calculate_total_invested_on_year_for_portfolio method."""

    def test_returns_invested_for_year_with_transactions(self):
        """Should return total invested for the specified year."""
        self._setup_closed_company_with_transactions()

        calculator = CompanyClosedDataCalculator(self.company.id)
        result = calculator.calculate_total_invested_on_year_for_portfolio(2021)
        # 100 - 5 commission = 95
        self.assertEqual(result, Decimal(95))

    def test_returns_zero_when_no_transactions_in_year(self):
        """Should return 0 when no transactions in the year."""
        self._setup_closed_company_with_transactions()

        calculator = CompanyClosedDataCalculator(self.company.id)
        result = calculator.calculate_total_invested_on_year_for_portfolio(2020)
        self.assertEqual(result, Decimal(0))


class CalculateTotalInvestedOnYearTestCase(CompanyClosedDataCalculatorTestCase):
    """Tests for calculate_total_invested_on_year method."""

    def test_returns_zero_after_all_shares_sold(self):
        """Should return 0 for years after all shares are sold."""
        self._setup_closed_company_with_transactions()

        calculator = CompanyClosedDataCalculator(self.company.id)
        # After 2023, shares count is 0
        result = calculator.calculate_total_invested_on_year(2024)
        self.assertEqual(result, Decimal(0))

    def test_returns_invested_when_shares_exist(self):
        """Should return invested amount when company still has shares."""
        self._setup_closed_company_with_transactions()

        calculator = CompanyClosedDataCalculator(self.company.id)
        # In 2021, company had shares
        result = calculator.calculate_total_invested_on_year(2021)
        self.assertEqual(result, Decimal(95))


class CalculateAccumulatedInvestmentUntilYearForPortfolioTestCase(
    CompanyClosedDataCalculatorTestCase
):
    """Tests for calculate_accumulated_investment_until_year_for_portfolio method."""

    def test_returns_zero_after_last_sell(self):
        """Should return 0 for years >= last sell transaction year."""
        self._setup_closed_company_with_transactions()

        calculator = CompanyClosedDataCalculator(self.company.id)
        # 2023 is the year of the last sell
        result = calculator.calculate_accumulated_investment_until_year_for_portfolio(
            2023
        )
        self.assertEqual(result, Decimal(0))

    def test_returns_accumulated_before_last_sell(self):
        """Should return accumulated investment before last sell year."""
        self._setup_closed_company_with_transactions()

        calculator = CompanyClosedDataCalculator(self.company.id)
        # Before 2023 sell
        result = calculator.calculate_accumulated_investment_until_year_for_portfolio(
            2022
        )
        # 2021: 95 + 2022: 115 = 210
        self.assertEqual(result, Decimal(210))


class CalculateAccumulatedInvestmentUntilYearTestCase(
    CompanyClosedDataCalculatorTestCase
):
    """Tests for calculate_accumulated_investment_until_year method."""

    def test_returns_zero_after_last_sell(self):
        """Should return 0 for years >= last sell transaction year."""
        self._setup_closed_company_with_transactions()

        calculator = CompanyClosedDataCalculator(self.company.id)
        result = calculator.calculate_accumulated_investment_until_year(2023)
        self.assertEqual(result, Decimal(0))

    def test_returns_accumulated_before_last_sell(self):
        """Should return accumulated investment before last sell."""
        self._setup_closed_company_with_transactions()

        calculator = CompanyClosedDataCalculator(self.company.id)
        result = calculator.calculate_accumulated_investment_until_year(2022)
        # 2021: 95 + 2022: 115 = 210
        self.assertEqual(result, Decimal(210))

    def test_returns_single_year_accumulation(self):
        """Should return only first year investment."""
        self._setup_closed_company_with_transactions()

        calculator = CompanyClosedDataCalculator(self.company.id)
        result = calculator.calculate_accumulated_investment_until_year(2021)
        self.assertEqual(result, Decimal(95))


class CalculateCompanyValueOnYearForPortfolioTestCase(
    CompanyClosedDataCalculatorTestCase
):
    """Tests for calculate_company_value_on_year_for_portfolio method."""

    def test_returns_zero_after_last_sell(self):
        """Should return 0 for years >= last sell transaction year."""
        self._setup_closed_company_with_transactions()

        calculator = CompanyClosedDataCalculator(self.company.id)
        result = calculator.calculate_company_value_on_year_for_portfolio(2023)
        self.assertEqual(result, Decimal(0))


class CalculateCompanyValueOnYearTestCase(CompanyClosedDataCalculatorTestCase):
    """Tests for calculate_company_value_on_year method."""

    def test_returns_zero_after_last_sell(self):
        """Should return 0 for years >= last sell transaction year."""
        self._setup_closed_company_with_transactions()

        calculator = CompanyClosedDataCalculator(self.company.id)
        result = calculator.calculate_company_value_on_year(2023)
        self.assertEqual(result, Decimal(0))


class CalculateReturnOnYearTestCase(CompanyClosedDataCalculatorTestCase):
    """Tests for calculate_return_on_year method."""

    def test_calculates_return_for_closed_company(self):
        """Should calculate return based on sales - investments - commissions."""
        self._setup_closed_company_with_transactions()

        calculator = CompanyClosedDataCalculator(self.company.id)
        # 2023 is last sell year
        result = calculator.calculate_return_on_year(2023)
        # Sales: 300, Investments: 220, Commissions: 20 (5+5+10)
        # Return = 300 - 220 - 20 = 60
        self.assertEqual(result, Decimal(60))


class CalculateReturnWithDividendsOnYearTestCase(CompanyClosedDataCalculatorTestCase):
    """Tests for calculate_return_with_dividends_on_year method."""

    def test_includes_dividends_in_return(self):
        """Should add accumulated dividends to the return."""
        self._setup_closed_company_with_transactions()
        # Add dividend in 2022
        self._create_dividend_transaction(
            total_amount=30,
            total_commission=2,
            transaction_date=datetime.date(2022, 6, 15),
        )

        calculator = CompanyClosedDataCalculator(self.company.id)
        result = calculator.calculate_return_with_dividends_on_year(2023)
        # Return: 60 + Dividends: (30-2) = 88
        self.assertEqual(result, Decimal(88))


class CalculateReturnYieldOnYearTestCase(CompanyClosedDataCalculatorTestCase):
    """Tests for calculate_return_yield_on_year method."""

    def test_calculates_yield_percentage(self):
        """Should calculate return as percentage of total invested."""
        self._setup_closed_company_with_transactions()

        calculator = CompanyClosedDataCalculator(self.company.id)
        result = calculator.calculate_return_yield_on_year(2023)
        # Yield should be positive (profitable closed position)
        self.assertGreater(result, Decimal(0))
        # Should be a percentage less than 100% for this scenario
        self.assertLess(result, Decimal(100))

    def test_returns_zero_when_no_investment(self):
        """Should return 0 when total invested is 0 to avoid division by zero."""
        # No transactions = no last sell transaction, this will fail
        # Instead, create minimal setup
        self._create_shares_transaction(
            count=10,
            gross_price_per_share=10,
            total_amount=100,
            total_commission=5,
            transaction_date=datetime.date(2021, 1, 15),
            transaction_type=TransactionType.SELL,  # Only sell (edge case)
        )

        calculator = CompanyClosedDataCalculator(self.company.id)
        result = calculator.calculate_return_yield_on_year(2020)
        # Before any transaction, invested is 0
        self.assertEqual(result, Decimal(0))


class CalculateReturnYieldWithDividendsOnYearTestCase(
    CompanyClosedDataCalculatorTestCase
):
    """Tests for calculate_return_yield_with_dividends_on_year method."""

    def test_calculates_yield_with_dividends(self):
        """Should calculate yield including dividends."""
        self._setup_closed_company_with_transactions()
        self._create_dividend_transaction(
            total_amount=30,
            total_commission=2,
            transaction_date=datetime.date(2022, 6, 15),
        )

        calculator = CompanyClosedDataCalculator(self.company.id)
        result = calculator.calculate_return_yield_with_dividends_on_year(2023)
        # Yield with dividends should be higher than yield without
        yield_without = calculator.calculate_return_yield_on_year(2023)
        self.assertGreater(result, yield_without)
        # Should be a positive percentage
        self.assertGreater(result, Decimal(0))

    def test_returns_zero_when_no_investment(self):
        """Should return 0 when total invested is 0."""
        self._create_shares_transaction(
            count=10,
            gross_price_per_share=10,
            total_amount=100,
            total_commission=5,
            transaction_date=datetime.date(2021, 1, 15),
            transaction_type=TransactionType.SELL,
        )

        calculator = CompanyClosedDataCalculator(self.company.id)
        result = calculator.calculate_return_yield_with_dividends_on_year(2020)
        self.assertEqual(result, Decimal(0))
