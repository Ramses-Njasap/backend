from django.contrib.gis.db import models
from django.utils.translation import gettext_lazy as _

from utilities.generators.string_generators import QueryID

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
