from django.contrib.gis.db import models
from django.utils.translation import gettext_lazy as _

from properties.models.profiles import Profile
from properties.models.boundaries import Boundary
from properties.models.amenities import Amenity

from configurations.models.currencies import Currencies
from configurations.utilities.currencies import ExchangeRates

from utilities import response
from utilities.generators.string_generators import QueryID

from datetime import date

import uuid


class Partition(models.Model):
    class PartitionName(models.TextChoices):
        ROOM = 'room', 'Room'
        KITCHEN = 'kitchen', 'Kitchen'
        TOILET = 'toilet', 'Toilet'
        PARLOUR = 'parlour', 'Parlour'
        SINGLE_SPACE = 'single_space', 'Single Space'

    name = models.CharField(
        _("Partition Name"), max_length=14,
        choices=PartitionName.choices, default=PartitionName.SINGLE_SPACE,
        unique=True, null=False, blank=False
    )

    query_id = models.BinaryField(
        null=False, blank=False, max_length=10000, db_index=True
    )

    def __str__(self) -> str:
        return str(self.name)

    class Meta:
        verbose_name = 'Partition'
        verbose_name_plural = 'Partitions'

    def save(self, *args, **kwargs) -> None:

        # Building user_id_generator parameters

        data = [self.name, str(uuid.uuid5)]
        data_length = sum(len(item) for item in data)

        # Stopped building user_id_generator parameters

        query_id_instance = QueryID(data=data, length=data_length)

        # Generating query_id and saving it to database
        self.query_id = query_id_instance.to_database()

        return super().save(*args, **kwargs)


class RoomPartition(models.Model):
    partition = models.ForeignKey(
        Partition, null=False, blank=False, on_delete=models.CASCADE,
        help_text='Room Partition'
    )
    number = models.SmallIntegerField(default=1)
    query_id = models.BinaryField(
        null=False, blank=False, max_length=10000, db_index=True
    )

    def __str__(self) -> str:
        if self.number > 1:
            return f"{self.number} {self.partition.name}"
        else:
            return f"{self.number} {self.partition.name}s"

    class Meta:
        verbose_name = 'Room Partition'
        verbose_name_plural = 'Room Partitions'

    def save(self, *args, **kwargs) -> None:

        # Building user_id_generator parameters

        data = [self.name, str(uuid.uuid5)]
        data_length = sum(len(item) for item in data)

        # Stopped building user_id_generator parameters

        query_id_instance = QueryID(data=data, length=data_length)

        # Generating query_id and saving it to database
        self.query_id = query_id_instance.to_database()

        return super().save(*args, **kwargs)


class Room(models.Model):
    class HomeType(models.TextChoices):
        APARTMENT = 'apartment', 'Apartment'
        # SELF_CONTAINED = 'self_contained', 'Self Contained'
        BUNGALOW = 'bongalow', 'Bongalow'
        SINGLE_ROOM = 'single_room', 'Single Room'

    home_type = models.CharField(
        max_length=100, choices=HomeType.choices,
        default=HomeType.SINGLE_ROOM
    )
    number_of_rooms = models.SmallIntegerField(default=1)
    rooms_taken = models.SmallIntegerField(
        default=0, null=True, blank=True
    )

    spaces = models.ManyToManyField(RoomPartition)

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

        data = [self.name, str(uuid.uuid5)]
        data_length = sum(len(item) for item in data)

        # Stopped building user_id_generator parameters

        query_id_instance = QueryID(data=data, length=data_length)

        # Generating query_id and saving it to database
        self.query_id = query_id_instance.to_database()

        super().save(*args, **kwargs)


class Home(models.Model):

    class AvailabilityStatus(models.TextChoices):
        # Indicates that the property is available for rental
        FOR_RENT = 'for_rent', 'For Rent'

        # Indicates that the property is available for purchase
        FOR_SALE = 'for_sale', 'For Sale'

        # Indicates that the property has been sold.
        SOLD = 'sold', 'Sold'

        # Indicates that the property has been rented out.
        RENTED = 'rented', 'Rented'

        # Indicates that the property has an offer but is not yet sold.
        UNDER_OFFER = 'under_offer', 'Under Offer'

        # Indicates that the sale process is pending but not finalized.
        PENDING_SALE = 'pending_sale', 'Pending Sale'

        # Indicates that the property is available for lease,
        # which may differ slightly from rental
        # (often longer-term or commercial).
        FOR_LEASE = 'for_lease', 'For Lease'

        # General term indicating the property
        # is available without specifying the type of transaction.
        AVAILABLE = 'available', 'Available'

        # Indicates that the property has been reserved
        # but is not yet sold or rented. When reserved,
        # notification is sent to the person the property
        # is reserved for.
        RESERVED = 'reserved', 'Reserved'

        # Indicates that the property is not currently available
        # for sale or rent, possibly due to being taken off
        # the market temporarily.
        OFF_MARKET = 'off_market', 'Off Market'

        # Indicates that the property will be available
        # for sale or rent soon but is not currently listed.
        # (This is the default).
        COMING_SOON = 'coming_soon', 'Coming Soon'

        # Indicates that the property is available for
        # purchase via auction.
        AUCTION = 'auction', 'Auction'

        # Indicates that the property is not currently
        # available for any type of transaction.
        NOT_AVAILABLE = 'not_available', 'Not Available'

        # Indicates that the property was sold before it
        # officially became available on the market.
        PRE_SOLD = 'pre_sold', 'Pre-Sold'

        # Indicates that the property is available for
        # trade or exchange rather than a traditional
        # sale or rental.
        FOR_TRADE = 'for_trade', 'For Trade'

        UNDER_RENOVATION = 'under_renovation', 'Under Renovation'

        # Indicates that the property is expected to be
        # available for rent soon but is not yet listed.
        PRE_RENTAL = 'pre_rental', 'Pre-Rental'

        # Indicates that the property is available for subletting,
        # where an existing leaseholder subleases the property.
        # (Not to be included for now - Coming Soon).
        FOR_SUBLET = 'for_sublet', 'For Sublet'

    uploader = models.ForeignKey(
        Profile, null=False, blank=False, on_delete=models.CASCADE
    )
    name = models.CharField(max_length=50, null=False, blank=False)

    description = models.TextField(null=False, blank=False)
    availability = models.CharField(
        max_length=50, choices=AvailabilityStatus.choices,
        default=AvailabilityStatus.NOT_AVAILABLE
    )

    number_of_shares = models.IntegerField(default=0)
    number_of_views = models.IntegerField(default=0)
    built_on = models.DateField()
    uploaded_on = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    geom = models.PointField(
        # WGS84 link to
        # read: https://en.wikipedia.org/wiki/World_Geodetic_System
        srid=4326, geography=True, dim=3,
        spatial_index=True, null=True, blank=True
    )

    multi_rooms = models.BooleanField(default=False)

    rooms = models.ManyToManyField(Room)

    # Calculated from `geom` (coordinate) values to nearest main road .
    distance_from_road = models.FloatField(
        db_index=True, null=True, blank=True
    )

    boundary = models.PolygonField(srid=4326)

    land_boundary = models.OneToOneField(
        Boundary, null=True, blank=True, on_delete=models.CASCADE
    )
    general_amenities = models.ManyToManyField(Amenity)

    partial_upload = models.BooleanField(default=False)

    query_id = models.BinaryField(
        null=False, blank=False, max_length=10000, db_index=True
    )

    class Meta:
        verbose_name = 'Property'
        verbose_name_plural = 'Properties'

    def __str__(self) -> str:
        return f'{self.title} [{self.cost} {self.currency}]'

    def age(self) -> str:
        age: int = date.today().year - self.built_on.year
        return f"{age} years" if age > 1 else f"{age} year"

    def number_of_rooms(self) -> int:
        rooms_count: int = 0

        for room in self.rooms:
            rooms_count += room.number_of_rooms

        return int(rooms_count)

    def rooms_remaining(self) -> int:
        rooms_remaining: int = 0

        for room in self.rooms:
            rooms_remaining += room.rooms_remaining

        return int(self.number_of_rooms - rooms_remaining)

    def save(self, *args, **kwargs):

        if not self.multi_rooms and (self.rooms.count() is not None):
            response.websocket_errors(
                g_name='',
                info=(
                    "Activate The Option To Save"
                    " Multiple Rooms On This Property."
                ),
                for_developer=(
                    "Multiple Rooms Cannot Be Saved On This Property."
                    " Activate The Option To Save Multiple Rooms On This Property."
                ),
                code='METHOD_NOT_ALLOWED',
                status_code=405
            )

        # Building user_id_generator parameters

        data = [self.name, str(uuid.uuid5)]
        data_length = sum(len(item) for item in data)

        # Stopped building user_id_generator parameters

        query_id_instance = QueryID(data=data, length=data_length)

        # Generating query_id and saving it to database
        self.query_id = query_id_instance.to_database()

        super().save(*args, **kwargs)
