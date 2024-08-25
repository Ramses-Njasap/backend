from configurations.utilities.currencies import ExchangeRates

from celery import shared_task

@shared_task
def update_exchange_rates_cache():
    # Instantiate the ExchangeRates class
    exchange_rates = ExchangeRates()
    # Call the store_exchange_rates_to_cache method to update the cache
    exchange_rates.store_exchange_rates_to_cache()
