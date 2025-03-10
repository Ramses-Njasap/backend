# Generated by Django 5.1.1 on 2025-02-28 18:54

import django.contrib.gis.db.models.fields
import django.db.models.deletion
import properties.models.profiles
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("accounts", "0001_initial"),
        ("configurations", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Amenity",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=150, verbose_name="Amenity Name")),
                ("description", models.CharField(verbose_name="Amenity Description")),
            ],
            options={
                "verbose_name": "Amenity",
                "verbose_name_plural": "Amenities",
            },
        ),
        migrations.CreateModel(
            name="Environment",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=50)),
                ("description", models.TextField()),
                (
                    "availability",
                    models.CharField(
                        choices=[
                            ("for rent", "FOR RENT"),
                            ("for sale", "FOR SALE"),
                            ("sold", "SOLD"),
                            ("rented", "RENTED"),
                            ("under offer", "UNDER OFFER"),
                            ("pending sale", "PENDING SALE"),
                            ("for lease", "FOR LEASE"),
                            ("available", "AVAILABLE"),
                            ("reserved", "RESERVED"),
                            ("off market", "OFF MARKET"),
                            ("coming soon", "COMING SOON"),
                            ("auction", "AUCTION"),
                            ("not available", "NOT AVAILABLE"),
                            ("pre sold", "PRE SOLD"),
                            ("for trade", "FOR TRADE"),
                            ("under renovation", "UNDER RENOVATION"),
                            ("pre rental", "PRE RENTAL"),
                            ("for sublet", "FOR SUBLET"),
                        ],
                        default="not available",
                        max_length=50,
                    ),
                ),
                ("number_of_shares", models.IntegerField(default=0)),
                ("number_of_views", models.IntegerField(default=0)),
                ("uploaded_on", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "distance_from_road",
                    models.FloatField(blank=True, db_index=True, null=True),
                ),
                (
                    "geom",
                    django.contrib.gis.db.models.fields.PointField(
                        blank=True, dim=3, geography=True, null=True, srid=4326
                    ),
                ),
                (
                    "boundary",
                    django.contrib.gis.db.models.fields.PolygonField(srid=4326),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Partition",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        choices=[
                            ("room", "Room"),
                            ("kitchen", "Kitchen"),
                            ("toilet", "Toilet"),
                            ("parlour", "Parlour"),
                            ("single_space", "Single Space"),
                        ],
                        default="single_space",
                        max_length=14,
                        unique=True,
                        verbose_name="Partition Name",
                    ),
                ),
                ("query_id", models.BinaryField(db_index=True, max_length=10000)),
            ],
            options={
                "verbose_name": "Partition",
                "verbose_name_plural": "Partitions",
            },
        ),
        migrations.CreateModel(
            name="ResidentialPropertyType",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        help_text="Property type name. e.g Guest house, villa, apartment etc.",
                        max_length=100,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="LandProperty",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "environment",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="properties.environment",
                    ),
                ),
            ],
            options={
                "verbose_name": "Land Property",
                "verbose_name_plural": "Land Properties",
            },
        ),
        migrations.CreateModel(
            name="Profile",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "statuses",
                    models.JSONField(
                        default=properties.models.profiles.Profile.default_statuses
                    ),
                ),
                (
                    "boundary",
                    django.contrib.gis.db.models.fields.PolygonField(
                        geography=True, srid=4326
                    ),
                ),
                ("central_coordinate", models.JSONField()),
                (
                    "location_name",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                (
                    "user_type",
                    models.CharField(
                        choices=[("COMPANY", "Company"), ("INDIVIDUAL", "Individual")],
                        db_index=True,
                        default="INDIVIDUAL",
                        max_length=15,
                    ),
                ),
                ("name", models.CharField(blank=True, max_length=70, null=True)),
                ("is_active", models.BooleanField(default=True)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="accounts.userprofile",
                    ),
                ),
            ],
            options={
                "verbose_name": "LaLouge Estate User Profile",
                "verbose_name_plural": "LaLouge Estate User Profiles",
            },
        ),
        migrations.AddField(
            model_name="environment",
            name="uploader",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="properties.profile"
            ),
        ),
        migrations.CreateModel(
            name="Building",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=50)),
                ("description", models.TextField()),
                (
                    "availability",
                    models.CharField(
                        choices=[
                            ("for rent", "FOR RENT"),
                            ("for sale", "FOR SALE"),
                            ("sold", "SOLD"),
                            ("rented", "RENTED"),
                            ("under offer", "UNDER OFFER"),
                            ("pending sale", "PENDING SALE"),
                            ("for lease", "FOR LEASE"),
                            ("available", "AVAILABLE"),
                            ("reserved", "RESERVED"),
                            ("off market", "OFF MARKET"),
                            ("coming soon", "COMING SOON"),
                            ("auction", "AUCTION"),
                            ("not available", "NOT AVAILABLE"),
                            ("pre sold", "PRE SOLD"),
                            ("for trade", "FOR TRADE"),
                            ("under renovation", "UNDER RENOVATION"),
                            ("pre rental", "PRE RENTAL"),
                            ("for sublet", "FOR SUBLET"),
                        ],
                        default="not available",
                        max_length=50,
                    ),
                ),
                ("number_of_shares", models.IntegerField(default=0)),
                ("number_of_views", models.IntegerField(default=0)),
                ("built_on", models.DateField()),
                ("uploaded_on", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "geom",
                    django.contrib.gis.db.models.fields.PointField(
                        blank=True, dim=3, geography=True, null=True, srid=4326
                    ),
                ),
                ("multi_units", models.BooleanField(default=False)),
                (
                    "distance_from_road",
                    models.FloatField(blank=True, db_index=True, null=True),
                ),
                (
                    "boundary",
                    django.contrib.gis.db.models.fields.PolygonField(srid=4326),
                ),
                ("partial_upload", models.BooleanField(default=False)),
                ("query_id", models.BinaryField(db_index=True, max_length=10000)),
                ("general_amenities", models.ManyToManyField(to="properties.amenity")),
                (
                    "uploader",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="properties.profile",
                    ),
                ),
            ],
            options={
                "verbose_name": "Property",
                "verbose_name_plural": "Properties",
            },
        ),
        migrations.CreateModel(
            name="ResidentialProperty",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("built_on", models.DateField()),
                ("partial_upload", models.BooleanField(default=False)),
                ("query_id", models.BinaryField(db_index=True, max_length=10000)),
                ("buildings", models.ManyToManyField(to="properties.building")),
                (
                    "environment",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="properties.environment",
                    ),
                ),
                ("general_amenities", models.ManyToManyField(to="properties.amenity")),
                (
                    "_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="properties.residentialpropertytype",
                    ),
                ),
            ],
            options={
                "verbose_name": "Residential Property",
                "verbose_name_plural": "Residential Properties",
            },
        ),
        migrations.CreateModel(
            name="ResidentialPropertyTypeInclusive",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "includes",
                    models.ManyToManyField(
                        related_name="inclusive_include",
                        to="properties.residentialpropertytype",
                    ),
                ),
                (
                    "main",
                    models.OneToOneField(
                        help_text="Main property type that includes other types. E.g: Villa can have apartments, guest houses",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="inclusive_main",
                        to="properties.residentialpropertytype",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="RoomPartition",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("number", models.SmallIntegerField(default=1)),
                ("query_id", models.BinaryField(db_index=True, max_length=10000)),
                (
                    "partition",
                    models.ForeignKey(
                        help_text="Room Partition",
                        on_delete=django.db.models.deletion.CASCADE,
                        to="properties.partition",
                    ),
                ),
            ],
            options={
                "verbose_name": "Room Partition",
                "verbose_name_plural": "Room Partitions",
            },
        ),
        migrations.CreateModel(
            name="Unit",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "home_type",
                    models.CharField(
                        choices=[
                            ("apartment", "Apartment"),
                            ("bongalow", "Bongalow"),
                            ("single_room", "Single Room"),
                        ],
                        default="single_room",
                        max_length=100,
                    ),
                ),
                ("name", models.CharField(max_length=100)),
                ("number_of_rooms", models.SmallIntegerField(default=1)),
                (
                    "rooms_taken",
                    models.SmallIntegerField(blank=True, default=0, null=True),
                ),
                ("cost", models.DecimalField(decimal_places=2, max_digits=10)),
                (
                    "exchange_rate_from_usd_upon_upload",
                    models.DecimalField(decimal_places=2, max_digits=10),
                ),
                ("query_id", models.BinaryField(db_index=True, max_length=10000)),
                (
                    "currency",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        to="configurations.currencies",
                    ),
                ),
                ("rooms", models.ManyToManyField(to="properties.roompartition")),
            ],
        ),
        migrations.AddField(
            model_name="building",
            name="units",
            field=models.ManyToManyField(to="properties.unit"),
        ),
    ]
