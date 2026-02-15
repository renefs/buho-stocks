import datetime
from decimal import Decimal

from buho_backend.tests.base_test_case import BaseApiTestCase
from buho_backend.transaction_types import TransactionType
from companies.tests.factory import CompanyFactory
from portfolios.tests.factory import PortfolioFactory
from shares_transactions.calculators.transaction_calculator import TransactionCalculator
from shares_transactions.models import SharesTransaction
from shares_transactions.tests.factory import SharesTransactionFactory


class TransactionCalculatorTestCase(BaseApiTestCase):
    """Tests for TransactionCalculator class."""

    def setUp(self):
        super().setUp()
        self.portfolio = PortfolioFactory.create(base_currency="EUR")
        self.company = CompanyFactory.create(
            portfolio=self.portfolio,
            base_currency="EUR",
            dividends_currency="EUR",
            is_closed=False,
        )
        self.calculator = TransactionCalculator()

    def _create_shares_transaction(
        self,
        count=10,
        gross_price_per_share=10,
        total_amount=None,
        total_commission=5,
        transaction_date=None,
        transaction_type=TransactionType.BUY,
        exchange_rate=1,
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
            exchange_rate=exchange_rate,
            type=transaction_type,
            transaction_date=transaction_date,
        )


class CalculateTransactionsAmountTestCase(TransactionCalculatorTestCase):
    """Tests for calculate_transactions_amount method."""

    def test_returns_zero_for_empty_queryset(self):
        """Should return 0 when queryset is empty."""
        transactions = SharesTransaction.objects.none()
        result = self.calculator.calculate_transactions_amount(transactions)
        self.assertEqual(result, Decimal(0))

    def test_calculates_single_transaction_amount(self):
        """Should calculate amount for a single transaction."""
        self._create_shares_transaction(
            count=10,
            gross_price_per_share=10,
            total_amount=100,
            total_commission=5,
        )
        transactions = SharesTransaction.objects.filter(company=self.company)
        result = self.calculator.calculate_transactions_amount(transactions)
        # total_amount + commission = 100 + 5 = 105
        self.assertEqual(result, Decimal(105))

    def test_applies_exchange_rate_when_use_portfolio_currency(self):
        """Should apply exchange rate when use_portfolio_currency is True."""
        self._create_shares_transaction(
            count=10,
            gross_price_per_share=10,
            total_amount=100,
            total_commission=5,
            exchange_rate=Decimal("1.2"),
        )
        transactions = SharesTransaction.objects.filter(company=self.company)
        result = self.calculator.calculate_transactions_amount(
            transactions, use_portfolio_currency=True
        )
        # (100 * 1.2) + (5 * 1.2) = 120 + 6 = 126
        self.assertEqual(result, Decimal("126.0"))

    def test_ignores_exchange_rate_when_not_use_portfolio_currency(self):
        """Should ignore exchange rate when use_portfolio_currency is False."""
        self._create_shares_transaction(
            count=10,
            gross_price_per_share=10,
            total_amount=100,
            total_commission=5,
            exchange_rate=Decimal("1.2"),
        )
        transactions = SharesTransaction.objects.filter(company=self.company)
        result = self.calculator.calculate_transactions_amount(
            transactions, use_portfolio_currency=False
        )
        # total_amount + commission = 100 + 5 = 105 (no exchange rate)
        self.assertEqual(result, Decimal(105))


class CalculateInvestedAmountTestCase(TransactionCalculatorTestCase):
    """Tests for calculate_invested_amount method."""

    def test_returns_zero_for_empty_queryset(self):
        """Should return 0 when queryset is empty."""
        transactions = SharesTransaction.objects.none()
        result = self.calculator.calculate_invested_amount(transactions)
        self.assertEqual(result, Decimal(0))

    def test_calculates_invested_amount_subtracting_commission(self):
        """Should calculate invested amount subtracting commission."""
        self._create_shares_transaction(
            count=10,
            gross_price_per_share=10,
            total_amount=100,
            total_commission=5,
        )
        transactions = SharesTransaction.objects.filter(company=self.company)
        result = self.calculator.calculate_invested_amount(transactions)
        # total_amount - commission = 100 - 5 = 95
        self.assertEqual(result, Decimal(95))

    def test_applies_exchange_rate_when_use_portfolio_currency(self):
        """Should apply exchange rate when use_portfolio_currency is True."""
        self._create_shares_transaction(
            count=10,
            gross_price_per_share=10,
            total_amount=100,
            total_commission=5,
            exchange_rate=Decimal("1.2"),
        )
        transactions = SharesTransaction.objects.filter(company=self.company)
        result = self.calculator.calculate_invested_amount(
            transactions, use_portfolio_currency=True
        )
        # (100 * 1.2) - (5 * 1.2) = 120 - 6 = 114
        self.assertEqual(result, Decimal("114.0"))


class CalculateInvestmentsTestCase(TransactionCalculatorTestCase):
    """Tests for calculate_investments method."""

    def test_returns_zero_for_empty_queryset(self):
        """Should return 0 when queryset is empty."""
        transactions = SharesTransaction.objects.none()
        result = self.calculator.calculate_investments(transactions)
        self.assertEqual(result, Decimal(0))

    def test_calculates_investments_for_single_transaction(self):
        """Should calculate investments for a single transaction."""
        self._create_shares_transaction(
            count=10,
            gross_price_per_share=10,
            total_amount=100,
            total_commission=5,
        )
        transactions = SharesTransaction.objects.filter(company=self.company)
        result = self.calculator.calculate_investments(transactions)
        # total_amount - commission = 100 - 5 = 95
        self.assertEqual(result, Decimal(95))

    def test_calculates_investments_for_multiple_transactions(self):
        """Should sum investments for multiple transactions."""
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
            transaction_date=datetime.date(2023, 2, 15),
        )
        transactions = SharesTransaction.objects.filter(company=self.company)
        result = self.calculator.calculate_investments(transactions)
        # (100 - 5) + (100 - 10) = 95 + 90 = 185
        self.assertEqual(result, Decimal(185))

    def test_applies_exchange_rate_for_each_transaction(self):
        """Should apply exchange rate to each transaction."""
        self._create_shares_transaction(
            count=10,
            gross_price_per_share=10,
            total_amount=100,
            total_commission=5,
            exchange_rate=Decimal("1.2"),
        )
        transactions = SharesTransaction.objects.filter(company=self.company)
        result = self.calculator.calculate_investments(
            transactions, use_portfolio_currency=True
        )
        # (100 * 1.2) - (5 * 1.2) = 120 - 6 = 114
        self.assertEqual(result, Decimal("114.0"))


class CalculateCommissionsTestCase(TransactionCalculatorTestCase):
    """Tests for calculate_commissions method."""

    def test_returns_zero_for_empty_queryset(self):
        """Should return 0 when queryset is empty."""
        transactions = SharesTransaction.objects.none()
        result = self.calculator.calculate_commissions(transactions)
        self.assertEqual(result, Decimal(0))

    def test_calculates_single_transaction_commission(self):
        """Should calculate commission for a single transaction."""
        self._create_shares_transaction(
            count=10,
            gross_price_per_share=10,
            total_amount=100,
            total_commission=5,
        )
        transactions = SharesTransaction.objects.filter(company=self.company)
        result = self.calculator.calculate_commissions(transactions)
        self.assertEqual(result, Decimal(5))

    def test_sums_commissions_for_multiple_transactions(self):
        """Should sum commissions from multiple transactions."""
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
            transaction_date=datetime.date(2023, 2, 15),
        )
        transactions = SharesTransaction.objects.filter(company=self.company)
        result = self.calculator.calculate_commissions(transactions)
        # 5 + 10 = 15
        self.assertEqual(result, Decimal(15))

    def test_applies_exchange_rate_when_use_portfolio_currency(self):
        """Should apply exchange rate when use_portfolio_currency is True."""
        self._create_shares_transaction(
            count=10,
            gross_price_per_share=10,
            total_amount=100,
            total_commission=5,
            exchange_rate=Decimal("1.2"),
        )
        transactions = SharesTransaction.objects.filter(company=self.company)
        result = self.calculator.calculate_commissions(
            transactions, use_portfolio_currency=True
        )
        # 5 * 1.2 = 6
        self.assertEqual(result, Decimal("6.0"))

    def test_ignores_exchange_rate_when_not_use_portfolio_currency(self):
        """Should ignore exchange rate when use_portfolio_currency is False."""
        self._create_shares_transaction(
            count=10,
            gross_price_per_share=10,
            total_amount=100,
            total_commission=5,
            exchange_rate=Decimal("1.2"),
        )
        transactions = SharesTransaction.objects.filter(company=self.company)
        result = self.calculator.calculate_commissions(
            transactions, use_portfolio_currency=False
        )
        # 5 (no exchange rate)
        self.assertEqual(result, Decimal(5))
