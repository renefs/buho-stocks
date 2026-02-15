import datetime
from decimal import Decimal

from django.conf import settings

from buho_backend.tests.base_test_case import BaseApiTestCase
from buho_backend.transaction_types import TransactionType
from companies.tests.factory import CompanyFactory
from dividends_transactions.tests.factory import DividendsTransactionFactory
from portfolios.tests.factory import PortfolioFactory
from shares_transactions.tests.factory import SharesTransactionFactory
from stats.calculators.portfolio_stats_utils import PortfolioStatsUtils
from stats.models.portfolio_stats import PortfolioStatsForYear


class PortfolioStatsUtilsTestCase(BaseApiTestCase):
    """Tests for PortfolioStatsUtils class."""

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
        company=None,
    ):
        """Helper to create a shares transaction."""
        if transaction_date is None:
            transaction_date = datetime.date(2023, 1, 15)

        if total_amount is None:
            total_amount = count * gross_price_per_share

        if company is None:
            company = self.company

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
        total_amount=50,
        total_commission=2,
        transaction_date=None,
        company=None,
    ):
        """Helper to create a dividend transaction."""
        if transaction_date is None:
            transaction_date = datetime.date(2023, 6, 15)

        if company is None:
            company = self.company

        return DividendsTransactionFactory.create(
            company=company,
            total_amount_currency=company.dividends_currency,
            total_commission_currency=company.dividends_currency,
            total_amount=total_amount,
            total_commission=total_commission,
            exchange_rate=1,
            transaction_date=transaction_date,
        )


class PortfolioStatsUtilsInitTestCase(PortfolioStatsUtilsTestCase):
    """Tests for PortfolioStatsUtils initialization."""

    def test_initializes_with_portfolio_id(self):
        """Should initialize with portfolio_id."""
        stats_utils = PortfolioStatsUtils(self.portfolio.id)
        self.assertEqual(stats_utils.portfolio.id, self.portfolio.id)

    def test_initializes_with_default_year(self):
        """Should default to YEAR_FOR_ALL."""
        stats_utils = PortfolioStatsUtils(self.portfolio.id)
        self.assertEqual(stats_utils.year, settings.YEAR_FOR_ALL)

    def test_initializes_with_specific_year(self):
        """Should accept specific year parameter."""
        stats_utils = PortfolioStatsUtils(self.portfolio.id, year=2023)
        self.assertEqual(stats_utils.year, 2023)

    def test_initializes_with_use_portfolio_currency(self):
        """Should accept use_portfolio_currency parameter."""
        stats_utils = PortfolioStatsUtils(
            self.portfolio.id, use_portfolio_currency=False
        )
        self.assertFalse(stats_utils.use_portfolio_currency)


class GetYearStatsTestCase(PortfolioStatsUtilsTestCase):
    """Tests for get_year_stats method."""

    def test_returns_none_when_no_stats_exist(self):
        """Should return None when no stats exist for year."""
        stats_utils = PortfolioStatsUtils(self.portfolio.id, year=2023)
        result = stats_utils.get_year_stats()
        self.assertIsNone(result)

    def test_returns_existing_stats(self):
        """Should return existing stats object."""
        PortfolioStatsForYear.objects.create(
            portfolio=self.portfolio,
            year=2023,
            invested=100,
            dividends=10,
            dividends_yield=Decimal("5.0"),
            portfolio_currency="EUR",
            accumulated_investment=100,
            accumulated_dividends=10,
            portfolio_value=110,
            return_value=10,
            return_percent=Decimal("10.0"),
            return_with_dividends=20,
            return_with_dividends_percent=Decimal("20.0"),
        )

        stats_utils = PortfolioStatsUtils(self.portfolio.id, year=2023)
        result = stats_utils.get_year_stats()
        self.assertIsNotNone(result)
        self.assertEqual(result.year, 2023)
        self.assertEqual(result.invested, 100)


class UpdateYearStatsTestCase(PortfolioStatsUtilsTestCase):
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

        stats_utils = PortfolioStatsUtils(self.portfolio.id, year=2023)
        result = stats_utils.update_year_stats()

        self.assertIsNotNone(result)
        self.assertEqual(result.year, 2023)
        self.assertEqual(result.portfolio, self.portfolio)

    def test_updates_existing_stats(self):
        """Should update existing stats."""
        PortfolioStatsForYear.objects.create(
            portfolio=self.portfolio,
            year=2023,
            invested=50,
            dividends=5,
            dividends_yield=Decimal("2.5"),
            portfolio_currency="EUR",
            accumulated_investment=50,
            accumulated_dividends=5,
            portfolio_value=55,
            return_value=5,
            return_percent=Decimal("10.0"),
            return_with_dividends=10,
            return_with_dividends_percent=Decimal("20.0"),
        )

        self._create_shares_transaction(
            count=10,
            gross_price_per_share=10,
            total_amount=100,
            total_commission=5,
            transaction_date=datetime.date(2023, 1, 15),
        )

        stats_utils = PortfolioStatsUtils(self.portfolio.id, year=2023)
        result = stats_utils.update_year_stats()

        self.assertEqual(result.invested, Decimal(95))


class GetYearStatsByCompanyTestCase(PortfolioStatsUtilsTestCase):
    """Tests for get_year_stats_by_company method."""

    def test_returns_empty_list_when_no_companies(self):
        """Should return empty list when portfolio has no companies."""
        empty_portfolio = PortfolioFactory.create(base_currency="EUR")
        stats_utils = PortfolioStatsUtils(empty_portfolio.id, year=2023)
        result = stats_utils.get_year_stats_by_company()
        self.assertEqual(result, [])

    def test_returns_stats_for_each_company(self):
        """Should return stats for each company in portfolio."""
        CompanyFactory.create(
            portfolio=self.portfolio,
            base_currency="EUR",
            dividends_currency="EUR",
        )

        stats_utils = PortfolioStatsUtils(self.portfolio.id, year=2023)
        result = stats_utils.get_year_stats_by_company()

        self.assertEqual(len(result), 2)


class GetAllYearsStatsTestCase(PortfolioStatsUtilsTestCase):
    """Tests for get_all_years_stats method."""

    def test_returns_empty_list_when_no_transactions(self):
        """Should return empty list when no transactions exist."""
        stats_utils = PortfolioStatsUtils(self.portfolio.id)
        result = stats_utils.get_all_years_stats()
        self.assertEqual(result, [])

    def test_returns_stats_for_all_years(self):
        """Should return stats for all years with data."""
        # Create transactions in multiple years
        self._create_shares_transaction(
            transaction_date=datetime.date(2021, 1, 15),
        )
        self._create_shares_transaction(
            transaction_date=datetime.date(2022, 1, 15),
        )

        # Create stats for those years
        PortfolioStatsForYear.objects.create(
            portfolio=self.portfolio,
            year=2021,
            invested=100,
            dividends=0,
            dividends_yield=Decimal("0"),
            portfolio_currency="EUR",
            accumulated_investment=100,
            accumulated_dividends=0,
            portfolio_value=100,
            return_value=0,
            return_percent=Decimal("0"),
            return_with_dividends=0,
            return_with_dividends_percent=Decimal("0"),
        )
        PortfolioStatsForYear.objects.create(
            portfolio=self.portfolio,
            year=2022,
            invested=100,
            dividends=0,
            dividends_yield=Decimal("0"),
            portfolio_currency="EUR",
            accumulated_investment=200,
            accumulated_dividends=0,
            portfolio_value=200,
            return_value=0,
            return_percent=Decimal("0"),
            return_with_dividends=0,
            return_with_dividends_percent=Decimal("0"),
        )

        stats_utils = PortfolioStatsUtils(self.portfolio.id)
        result = stats_utils.get_all_years_stats()

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["year"], 2021)
        self.assertEqual(result[1]["year"], 2022)


class GetDividendsForYearMonthlyTestCase(PortfolioStatsUtilsTestCase):
    """Tests for get_dividends_for_year_monthly method."""

    def test_returns_empty_dict_when_no_dividends(self):
        """Should return empty dict when no dividends exist."""
        stats_utils = PortfolioStatsUtils(self.portfolio.id, year=2023)
        result = stats_utils.get_dividends_for_year_monthly()
        self.assertEqual(result, {})

    def test_groups_dividends_by_month(self):
        """Should group dividends by month name."""
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

        stats_utils = PortfolioStatsUtils(self.portfolio.id, year=2023)
        result = stats_utils.get_dividends_for_year_monthly(2023)

        self.assertIn("March", result)
        self.assertIn("June", result)
        self.assertEqual(result["March"], Decimal(48))  # 50 - 2
        self.assertEqual(result["June"], Decimal(57))  # 60 - 3

    def test_aggregates_multiple_dividends_in_same_month(self):
        """Should sum dividends in the same month."""
        self._create_dividend_transaction(
            total_amount=50,
            total_commission=2,
            transaction_date=datetime.date(2023, 3, 10),
        )
        self._create_dividend_transaction(
            total_amount=40,
            total_commission=2,
            transaction_date=datetime.date(2023, 3, 20),
        )

        stats_utils = PortfolioStatsUtils(self.portfolio.id, year=2023)
        result = stats_utils.get_dividends_for_year_monthly(2023)

        self.assertIn("March", result)
        # (50 - 2) + (40 - 2) = 48 + 38 = 86
        self.assertEqual(result["March"], Decimal(86))


class GetDividendsForAllYearsMonthlyTestCase(PortfolioStatsUtilsTestCase):
    """Tests for get_dividends_for_all_years_monthly method."""

    def test_returns_empty_dict_when_no_transactions(self):
        """Should return empty dict when no transactions exist."""
        stats_utils = PortfolioStatsUtils(self.portfolio.id)
        result = stats_utils.get_dividends_for_all_years_monthly()
        self.assertEqual(result, {})

    def test_returns_dividends_grouped_by_year_and_month(self):
        """Should return dividends grouped by year and month."""
        self._create_shares_transaction(
            transaction_date=datetime.date(2022, 1, 15),
        )
        self._create_dividend_transaction(
            total_amount=50,
            total_commission=2,
            transaction_date=datetime.date(2022, 6, 15),
        )
        self._create_dividend_transaction(
            total_amount=60,
            total_commission=3,
            transaction_date=datetime.date(2023, 3, 15),
        )

        stats_utils = PortfolioStatsUtils(self.portfolio.id)
        result = stats_utils.get_dividends_for_all_years_monthly()

        self.assertIn(2022, result)
        self.assertIn(2023, result)
        self.assertIn("June", result[2022])
        self.assertIn("March", result[2023])
