from django.contrib.gis.db import models

from properties.models.profiles import Profile


class Environment(models.Model):

    class AvailabilityStatus(models.TextChoices):
        # Indicates that the property is available for rental
        FOR_RENT = 'for rent', 'FOR RENT'

        # Indicates that the property is available for purchase
        FOR_SALE = 'for sale', 'FOR SALE'

        # Indicates that the property has been sold.
        SOLD = 'sold', 'SOLD'

        # Indicates that the property has been rented out.
        RENTED = 'rented', 'RENTED'

        # Indicates that the property has an offer but is not yet sold.
        UNDER_OFFER = 'under offer', 'UNDER OFFER'

        # Indicates that the sale process is pending but not finalized.
        PENDING_SALE = 'pending sale', 'PENDING SALE'

        # Indicates that the property is available for lease,
        # which may differ slightly from rental
        # (often longer-term or commercial).
        FOR_LEASE = 'for lease', 'FOR LEASE'

        # General term indicating the property
        # is available without specifying the type of transaction.
        AVAILABLE = 'available', 'AVAILABLE'

        # Indicates that the property has been reserved
        # but is not yet sold or rented. When reserved,
        # notification is sent to the person the property
        # is reserved for.
        RESERVED = 'reserved', 'RESERVED'

        # Indicates that the property is not currently available
        # for sale or rent, possibly due to being taken off
        # the market temporarily.
        OFF_MARKET = 'off market', 'OFF MARKET'

        # Indicates that the property will be available
        # for sale or rent soon but is not currently listed.
        # (This is the default).
        COMING_SOON = 'coming soon', 'COMING SOON'

        # Indicates that the property is available for
        # purchase via auction.
        AUCTION = 'auction', 'AUCTION'

        # Indicates that the property is not currently
        # available for any type of transaction.
        NOT_AVAILABLE = 'not available', 'NOT AVAILABLE'

        # Indicates that the property was sold before it
        # officially became available on the market.
        PRE_SOLD = 'pre sold', 'PRE SOLD'

        # Indicates that the property is available for
        # trade or exchange rather than a traditional
        # sale or rental.
        FOR_TRADE = 'for trade', 'FOR TRADE'

        UNDER_RENOVATION = 'under renovation', 'UNDER RENOVATION'

        # Indicates that the property is expected to be
        # available for rent soon but is not yet listed.
        PRE_RENTAL = 'pre rental', 'PRE RENTAL'

        # Indicates that the property is available for subletting,
        # where an existing leaseholder subleases the property.
        # (Not to be included for now - Coming Soon).
        FOR_SUBLET = 'for sublet', 'FOR SUBLET'

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
    uploaded_on = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Calculated from `geom` (coordinate) values to nearest main road .
    distance_from_road = models.FloatField(
        db_index=True, null=True, blank=True
    )

    geom = models.PointField(
        # WGS84 link to
        # read: https://en.wikipedia.org/wiki/World_Geodetic_System
        srid=4326, geography=True, dim=3,
        spatial_index=True, null=True, blank=True
    )

    boundary = models.PolygonField(
        # WGS84 link to
        # read: https://en.wikipedia.org/wiki/World_Geodetic_System
        srid=4326,
    )
