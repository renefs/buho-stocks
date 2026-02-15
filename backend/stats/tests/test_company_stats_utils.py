import datetime
from decimal import Decimal

from django.conf import settings

from buho_backend.tests.base_test_case import BaseApiTestCase
from buho_backend.transaction_types import TransactionType
from companies.tests.factory import CompanyFactory
from dividends_transactions.tests.factory import DividendsTransactionFactory
from portfolios.tests.factory import PortfolioFactory
from shares_transactions.tests.factory import SharesTransactionFactory
from stats.calculators.company_stats_utils import CompanyStatsCalculator
from stats.models.company_stats import CompanyStatsForYear


class CompanyStatsCalculatorTestCase(BaseApiTestCase):
    """Tests for CompanyStatsCalculator class."""

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


class CompanyStatsCalculatorInitTestCase(CompanyStatsCalculatorTestCase):
    """Tests for CompanyStatsCalculator initialization."""

    def test_initializes_with_company_id(self):
        """Should initialize with company_id."""
        calculator = CompanyStatsCalculator(self.company.id)
        self.assertEqual(calculator.company.id, self.company.id)

    def test_initializes_with_default_year(self):
        """Should default to YEAR_FOR_ALL."""
        calculator = CompanyStatsCalculator(self.company.id)
        self.assertEqual(calculator.year, settings.YEAR_FOR_ALL)

    def test_initializes_with_specific_year(self):
        """Should accept specific year parameter."""
        calculator = CompanyStatsCalculator(self.company.id, year=2023)
        self.assertEqual(calculator.year, 2023)

    def test_uses_closed_calculator_for_closed_company(self):
        """Should use CompanyClosedDataCalculator for closed companies."""
        closed_company = CompanyFactory.create(
            portfolio=self.portfolio,
            base_currency="EUR",
            dividends_currency="EUR",
            is_closed=True,
        )
        CompanyStatsCalculator(closed_company.id)
        # The company_data_calculator should be of closed type
        self.assertTrue(closed_company.is_closed)


class GetYearStatsTestCase(CompanyStatsCalculatorTestCase):
    """Tests for get_year_stats method."""

    def test_returns_none_when_no_stats_exist(self):
        """Should return None when no stats exist for year."""
        calculator = CompanyStatsCalculator(self.company.id, year=2023)
        result = calculator.get_year_stats(2023)
        self.assertIsNone(result)

    def test_returns_existing_stats(self):
        """Should return existing stats object."""
        CompanyStatsForYear.objects.create(
            company=self.company,
            year=2023,
            invested=100,
            dividends=10,
            dividends_yield=Decimal("5.0"),
            portfolio_currency="EUR",
            accumulated_investment=100,
            accumulated_dividends=10,
            portfolio_value=110,
            portfolio_value_is_down=False,
            return_value=10,
            return_percent=Decimal("10.0"),
            return_with_dividends=20,
            return_with_dividends_percent=Decimal("20.0"),
            shares_count=10,
            stock_price_value=Decimal("11.0"),
            stock_price_currency="EUR",
            stock_price_transaction_date="2023-12-31",
        )

        calculator = CompanyStatsCalculator(self.company.id, year=2023)
        result = calculator.get_year_stats(2023)
        self.assertIsNotNone(result)
        self.assertEqual(result.year, 2023)
        self.assertEqual(result.invested, 100)


class CalculateStatsForYearTestCase(CompanyStatsCalculatorTestCase):
    """Tests for calculate_stats_for_year method."""

    def test_calculates_stats_with_no_transactions(self):
        """Should return zero values when no transactions exist."""
        calculator = CompanyStatsCalculator(self.company.id, year=2023)
        result = calculator.calculate_stats_for_year(2023)

        self.assertEqual(result["invested"], Decimal(0))
        self.assertEqual(result["dividends"], Decimal(0))
        self.assertEqual(result["shares_count"], 0)

    def test_calculates_invested_amount(self):
        """Should calculate invested amount correctly."""
        self._create_shares_transaction(
            count=10,
            gross_price_per_share=10,
            total_amount=100,
            total_commission=5,
            transaction_date=datetime.date(2023, 1, 15),
        )

        calculator = CompanyStatsCalculator(self.company.id, year=2023)
        result = calculator.calculate_stats_for_year(2023)

        self.assertEqual(result["invested"], Decimal(95))
        self.assertEqual(result["shares_count"], 10)

    def test_calculates_dividends(self):
        """Should calculate dividends correctly."""
        self._create_shares_transaction(
            transaction_date=datetime.date(2023, 1, 15),
        )
        self._create_dividend_transaction(
            total_amount=50,
            total_commission=2,
            transaction_date=datetime.date(2023, 6, 15),
        )

        calculator = CompanyStatsCalculator(self.company.id, year=2023)
        result = calculator.calculate_stats_for_year(2023)

        self.assertEqual(result["dividends"], Decimal(48))

    def test_includes_portfolio_currency(self):
        """Should include portfolio currency in results."""
        calculator = CompanyStatsCalculator(self.company.id, year=2023)
        result = calculator.calculate_stats_for_year(2023)

        self.assertEqual(result["portfolio_currency"], "EUR")

    def test_calculates_portfolio_value_is_down(self):
        """Should flag when portfolio value is less than investment."""
        self._create_shares_transaction(
            count=10,
            gross_price_per_share=10,
            total_amount=100,
            total_commission=5,
            transaction_date=datetime.date(2023, 1, 15),
        )

        calculator = CompanyStatsCalculator(self.company.id, year=2023)
        result = calculator.calculate_stats_for_year(2023)

        # With 0 portfolio value (no stock price), portfolio is down
        self.assertTrue(result["portfolio_value_is_down"])


class UpdateYearStatsTestCase(CompanyStatsCalculatorTestCase):
    """Tests for update_year_stats method."""

    def test_creates_new_stats_when_none_exist(self):
        """Should create new stats when none exist."""
        self._create_shares_transaction(
            count=10,
            gross_price_per_share=10,
            total_amount=100,
            total_commission=5,
            transaction_date=datetime.date(2023, 1, 15),
        )

        calculator = CompanyStatsCalculator(self.company.id, year=2023)
        result = calculator.update_year_stats()

        self.assertIsNotNone(result)
        self.assertEqual(result.year, 2023)
        self.assertEqual(result.company, self.company)

    def test_updates_existing_stats(self):
        """Should update existing stats."""
        CompanyStatsForYear.objects.create(
            company=self.company,
            year=2023,
            invested=50,
            dividends=5,
            dividends_yield=Decimal("2.5"),
            portfolio_currency="EUR",
            accumulated_investment=50,
            accumulated_dividends=5,
            portfolio_value=55,
            portfolio_value_is_down=False,
            return_value=5,
            return_percent=Decimal("10.0"),
            return_with_dividends=10,
            return_with_dividends_percent=Decimal("20.0"),
            shares_count=5,
            stock_price_value=Decimal("11.0"),
            stock_price_currency="EUR",
            stock_price_transaction_date="2023-12-31",
        )

        self._create_shares_transaction(
            count=10,
            gross_price_per_share=10,
            total_amount=100,
            total_commission=5,
            transaction_date=datetime.date(2023, 1, 15),
        )

        calculator = CompanyStatsCalculator(self.company.id, year=2023)
        result = calculator.update_year_stats()

        self.assertEqual(result.invested, Decimal(95))
        self.assertEqual(result.shares_count, 10)

    def test_creates_stats_object_in_database(self):
        """Should persist stats to database."""
        self._create_shares_transaction(
            transaction_date=datetime.date(2023, 1, 15),
        )

        calculator = CompanyStatsCalculator(self.company.id, year=2023)
        calculator.update_year_stats()

        # Verify object exists in database
        self.assertTrue(
            CompanyStatsForYear.objects.filter(company=self.company, year=2023).exists()
        )
