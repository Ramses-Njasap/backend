from django.core.cache import cache
from django.conf import settings

from decimal import Decimal

import requests

# Define a very large timeout value, e.g., 10 years
ONE_MONTH_TIMEOUT = 30 * 24 * 60 * 60  # 1 month
CACHE_KEY = 'exchange_rate'


class ExchangeRates:
    def get_exchange_rate(self, to_currency: str = 'USD') -> Decimal:
        if to_currency.upper() == 'USD':
            return Decimal(1)

        exchange_rate = cache.get(CACHE_KEY)

        if exchange_rate is None:
            exchange_rate = self._fetch_exchange_rate()
            cache.set(CACHE_KEY, exchange_rate, timeout=ONE_MONTH_TIMEOUT)

        return exchange_rate

    def _fetch_exchange_rate(self) -> Decimal:

        # Attempt to get the exchange rate from the cache
        cached_rate = cache.get(CACHE_KEY)
        if cached_rate is not None:
            return Decimal(cached_rate)

        return Decimal(0)

    def store_exchange_rates_to_cache(self):
        url = (f"""https://v6.exchangerate-api.com/
               v6/{settings.EXCHANGE_RATE_API}/latest/USD""")

        try:
            response = requests.get(url)
            data = response.json()
        except requests.RequestException:
            return

        if response.status_code != 200:
            return

        rates = data.get('conversion_rates', {})

        for currency, rate in rates.items():
            cache.set(CACHE_KEY, Decimal(rate), timeout=ONE_MONTH_TIMEOUT)
