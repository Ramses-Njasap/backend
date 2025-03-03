from django.contrib.gis.db import models

from configurations.models.currencies import Currencies
from configurations.utilities.currencies import ExchangeRates

from properties.models.rooms import RoomPartition
from utilities.generators.string_generators import QueryID

import uuid


class Unit(models.Model):
    class UnitType(models.TextChoices):
        APARTMENT = 'apartment', 'Apartment'
        # SELF_CONTAINED = 'self_contained', 'Self Contained'
        BUNGALOW = 'bongalow', 'Bongalow'
        SINGLE_ROOM = 'single_room', 'Single Room'

    home_type = models.CharField(
        max_length=100, choices=UnitType.choices,
        default=UnitType.SINGLE_ROOM
    )
    name = models.CharField(max_length=100)
    number_of_rooms = models.SmallIntegerField(default=1)
    rooms_taken = models.SmallIntegerField(
        default=0, null=True, blank=True
    )

    rooms = models.ManyToManyField(RoomPartition)

    cost = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.ForeignKey(
        Currencies, on_delete=models.DO_NOTHING
    )
    exchange_rate_from_usd_upon_upload = models.DecimalField(
        max_digits=10, decimal_places=2
    )

    query_id = models.BinaryField(
        null=False, blank=False, max_length=10000, db_index=True
    )

    def rooms_remaining(self) -> int:
        if self.rooms_taken > self.number_of_rooms:
            return 0
        else:
            return (self.number_of_rooms - self.rooms_taken)

    def get_price(self, to_currency: str) -> str:
        """
        Converts the cost of a property to the specified currency.
        """
        # If the currency matches, return the cost directly
        if self.currency.code.upper() == to_currency.upper():
            return f'{self.cost} {self.currency.code}'

        # Convert the property's cost currency to USD (Base Currency)
        exchange_rate_instance = ExchangeRates()
        property_equivalent_usd_rate = exchange_rate_instance.get_exchange_rate(
            to_currency=self.currency.code.upper()
        )

        property_eqv_usd_cost = self.cost / property_equivalent_usd_rate

        # If the target currency is USD, return the USD equivalent
        if to_currency.upper() == 'USD':
            return f'{property_eqv_usd_cost} USD'

        # Convert the USD cost to the target currency
        # eqv = equivalent
        user_eqv_usd_rate = exchange_rate_instance.get_exchange_rate(
            to_currency=to_currency.upper()
        )
        user_eqv_usd_cost = user_eqv_usd_rate * property_eqv_usd_cost

        return f'{user_eqv_usd_cost} {to_currency.upper()}'

    def save(self, *args, **kwargs):
        if not self.pk:
            try:
                self.currency = Currencies.objects.get(code='USD'.upper())
            except Currencies.DoesNotExist:
                self.currency = Currencies.objects.create(
                    name='US Dollar', code='USD'.upper(), symbol='$'
                )

        # Building user_id_generator parameters

        data = [self.name, str(uuid.uuid5(uuid.NAMESPACE_DNS, self.name))]

        data_length = sum(len(item) for item in data)

        # Stopped building user_id_generator parameters

        query_id_instance = QueryID(data=data, length=data_length)

        # Generating query_id and saving it to database
        self.query_id = query_id_instance.to_database()

        super().save(*args, **kwargs)
