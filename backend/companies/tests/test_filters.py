from rest_framework import serializers

from buho_backend.tests.base_test_case import BaseApiTestCase
from companies.filters import FilteredCompanySerializer
from companies.models import Company
from companies.tests.factory import CompanyFactory
from portfolios.tests.factory import PortfolioFactory


class MockChildSerializer(serializers.Serializer):
    """Mock serializer for testing FilteredCompanySerializer."""

    id = serializers.IntegerField()
    name = serializers.CharField()
    is_closed = serializers.BooleanField()


class FilteredCompanySerializerTestCase(BaseApiTestCase):
    """Tests for FilteredCompanySerializer class."""

    def setUp(self):
        super().setUp()
        self.portfolio = PortfolioFactory.create(base_currency="EUR")

    def test_filters_out_closed_companies(self):
        """Should filter out companies where is_closed=True."""
        CompanyFactory.create(
            portfolio=self.portfolio,
            base_currency="EUR",
            dividends_currency="EUR",
            is_closed=False,
            name="Open Company",
        )
        CompanyFactory.create(
            portfolio=self.portfolio,
            base_currency="EUR",
            dividends_currency="EUR",
            is_closed=True,
            name="Closed Company",
        )

        queryset = Company.objects.filter(portfolio=self.portfolio)

        # Create a serializer using FilteredCompanySerializer as list_serializer_class
        class TestSerializer(serializers.Serializer):
            id = serializers.IntegerField()
            name = serializers.CharField()
            is_closed = serializers.BooleanField()

            class Meta:
                list_serializer_class = FilteredCompanySerializer

        serializer = FilteredCompanySerializer(
            child=TestSerializer(), instance=queryset
        )
        data = serializer.data

        # Should only contain the open company
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["name"], "Open Company")
        self.assertFalse(data[0]["is_closed"])

    def test_returns_all_open_companies(self):
        """Should return all non-closed companies."""
        CompanyFactory.create(
            portfolio=self.portfolio,
            base_currency="EUR",
            dividends_currency="EUR",
            is_closed=False,
            name="Company A",
        )
        CompanyFactory.create(
            portfolio=self.portfolio,
            base_currency="EUR",
            dividends_currency="EUR",
            is_closed=False,
            name="Company B",
        )

        queryset = Company.objects.filter(portfolio=self.portfolio)

        class TestSerializer(serializers.Serializer):
            id = serializers.IntegerField()
            name = serializers.CharField()
            is_closed = serializers.BooleanField()

            class Meta:
                list_serializer_class = FilteredCompanySerializer

        serializer = FilteredCompanySerializer(
            child=TestSerializer(), instance=queryset
        )
        data = serializer.data

        self.assertEqual(len(data), 2)

    def test_returns_empty_list_when_all_closed(self):
        """Should return empty list when all companies are closed."""
        CompanyFactory.create(
            portfolio=self.portfolio,
            base_currency="EUR",
            dividends_currency="EUR",
            is_closed=True,
            name="Closed A",
        )
        CompanyFactory.create(
            portfolio=self.portfolio,
            base_currency="EUR",
            dividends_currency="EUR",
            is_closed=True,
            name="Closed B",
        )

        queryset = Company.objects.filter(portfolio=self.portfolio)

        class TestSerializer(serializers.Serializer):
            id = serializers.IntegerField()
            name = serializers.CharField()
            is_closed = serializers.BooleanField()

            class Meta:
                list_serializer_class = FilteredCompanySerializer

        serializer = FilteredCompanySerializer(
            child=TestSerializer(), instance=queryset
        )
        data = serializer.data

        self.assertEqual(len(data), 0)

    def test_returns_empty_list_when_no_companies(self):
        """Should return empty list when no companies exist."""
        queryset = Company.objects.none()

        class TestSerializer(serializers.Serializer):
            id = serializers.IntegerField()
            name = serializers.CharField()
            is_closed = serializers.BooleanField()

            class Meta:
                list_serializer_class = FilteredCompanySerializer

        serializer = FilteredCompanySerializer(
            child=TestSerializer(), instance=queryset
        )
        data = serializer.data

        self.assertEqual(len(data), 0)
