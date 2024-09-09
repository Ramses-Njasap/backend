from django.db import models

from configurations.models.currency import Currency
from configurations.utilities.currencies import ExchangeRates

from decimal import Decimal

import requests


class Properties(models.Model):

    class AvailabilityStatus(models.TextChoices):
        FOR_RENT = 'for_rent', 'For Rent' # Indicates that the property is available for rental
        FOR_SALE = 'for_sale', 'For Sale' # Indicates that the property is available for purchase
        SOLD = 'sold', 'Sold' # Indicates that the property has been sold.
        RENTED = 'rented', 'Rented' # Indicates that the property has been rented out.
        UNDER_OFFER = 'under_offer', 'Under Offer' # Indicates that the property has an offer but is not yet sold.
        PENDING_SALE = 'pending_sale', 'Pending Sale' # Indicates that the sale process is pending but not finalized.
        FOR_LEASE = 'for_lease', 'For Lease' # Indicates that the property is available for lease, which may differ slightly from rental (often longer-term or commercial).
        AVAILABLE = 'available', 'Available' # General term indicating the property is available without specifying the type of transaction.
        RESERVED = 'reserved', 'Reserved' # Indicates that the property has been reserved but is not yet sold or rented. When reserved, notification is sent to the person the property is reserved for
        OFF_MARKET = 'off_market', 'Off Market' # Indicates that the property is not currently available for sale or rent, possibly due to being taken off the market temporarily.
        COMING_SOON = 'coming_soon', 'Coming Soon' # Indicates that the property will be available for sale or rent soon but is not currently listed. (This is the default)
        AUCTION = 'auction', 'Auction' # Indicates that the property is available for purchase via auction.
        NOT_AVAILABLE = 'not_available', 'Not Available' # Indicates that the property is not currently available for any type of transaction.
        PRE_SOLD = 'pre_sold', 'Pre-Sold' # Indicates that the property was sold before it officially became available on the market.
        FOR_TRADE = 'for_trade', 'For Trade' # Indicates that the property is available for trade or exchange rather than a traditional sale or rental.
        UNDER_RENOVATION = 'under_renovation', 'Under Renovation'
        PRE_RENTAL = 'pre_rental', 'Pre-Rental' # Indicates that the property is expected to be available for rent soon but is not yet listed.
        FOR_SUBLET = 'for_sublet', 'For Sublet' # Indicates that the property is available for subletting, where an existing leaseholder subleases the property. (Not to be included for now - Coming Soon)

    title = models.CharField(max_length=50, null=False, blank=False)
    description = models.TextField(null=False, blank=False)
    age = models.DateField()
    availability = models.CharField(max_length=50, choices=AvailabilityStatus.choices, default=AvailabilityStatus.NOT_AVAILABLE)
    address = ...
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.ForeignKey(Currency, on_delete=models.DO_NOTHING)
    exchange_rate_from_usd_upon_upload = models.DecimalField(max_digits=10, decimal_places=2)
    number_of_shares = models.IntegerField(default=0)
    number_of_views = models.IntegerField(default=0)
    built_on = models.DateField()
    uploaded_on = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Property'
        verbose_name_plural = 'Properties'

    def __str__(self):
        return f'{self.title} [{self.cost} {self.currency}]'
    
    def get_price(self, to_currency: str) -> str:

        if self.currency.code.upper() == to_currency.upper():
            return f'{self.cost} {self.currency.code}'
        
        # Convert The Property's Cost Currenct To USD (Default/Base Currency)
        exchange_rate_instance = ExchangeRates()
        property_equivalent_usd_rate = exchange_rate_instance.get_exchange_rate(to_currency=self.currency.code.upper())

        property_equivalent_usd_cost = self.cost / property_equivalent_usd_rate

        if to_currency.upper() == 'USD':
            return f'{property_equivalent_usd_cost} USD'
        
        user_equivalent_usd_rate = property_equivalent_usd_rate = exchange_rate_instance.get_exchange_rate(to_currency=to_currency.upper())

        user_equivalent_usd_cost = user_equivalent_usd_rate * property_equivalent_usd_cost

        return f'{user_equivalent_usd_cost} {to_currency.upper()}'

    
    def save(self, *args, **kwargs):
        if not self.currency:
            try:
                self.currency = Currency.objects.get(code='USD'.upper())
            except Currency.DoesNotExist:
                self.currency = Currency.objects.create(
                    name='US Dollar', code='USD'.upper(), symbol='$'
                )
        
        super().save(*args, **kwargs)