from django.core.cache import cache
from django.conf import settings
from decimal import Decimal
import requests

# Define a timeout value (1 month)
ONE_MONTH_TIMEOUT = 30 * 24 * 60 * 60  # 1 month
BASE_CURRENCY = 'USD'


class ExchangeRates:
    def get_exchange_rate(self, to_currency: str = 'USD') -> Decimal:
        """Retrieve exchange rate for the specified currency."""
        if to_currency.upper() == BASE_CURRENCY:
            return Decimal(1)

        # Generate a unique cache key for this currency
        cache_key = f'exchange_rate_{to_currency.upper()}'
        exchange_rate = cache.get(cache_key)

        if exchange_rate is None:
            # Fetch rates and store them in the cache
            self.store_exchange_rates_to_cache()
            exchange_rate = cache.get(cache_key)

        return Decimal(exchange_rate or 0)

    def _fetch_exchange_rates(self) -> dict:
        """Fetch exchange rates from the external API."""
        api_key = settings.EXCHANGE_RATE_API
        url = f"https://v6.exchangerate-api.com/v6/{api_key}/latest/{BASE_CURRENCY}"
        print(f"Fetching exchange rates from: {url}")

        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            return data.get('conversion_rates', {})
        except requests.RequestException as e:
            print(f"Error fetching exchange rates: {e}")
            return {}

    def store_exchange_rates_to_cache(self):
        """Store exchange rates in the cache."""
        rates = self._fetch_exchange_rates()

        for currency, rate in rates.items():
            # Create a unique cache key for each currency
            cache_key = f'exchange_rate_{currency.upper()}'
            cache.set(cache_key, Decimal(rate), timeout=ONE_MONTH_TIMEOUT)
