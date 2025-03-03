from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.apps import apps
from django.conf import settings

from decimal import Decimal

from accounts.models.users import User
from accounts.models.settings import UserSettings
from accounts.managers.plans import SubscriptionPlanManager

from configurations.utilities.currencies import ExchangeRates


application_setting: dict = settings.APPLICATION_SETTINGS
default_currency: dict = application_setting["DEFAULT_CURRENCY"]
subscription_defaults: dict = (
    application_setting["SUBSCRIPTION_DEFAULTS"]
)


class DefaultFeature(models.Model):

    class FeatureBelongsTo(models.TextChoices):
        INTERNAL = "INTERNAL", "internal"
        EXTERNAL = "EXTERNAL", "external"

    UNIT_PRICE = {
        "per_invite": Decimal("1.00"),
        "per_invite_commission": Decimal("2.50"),
    }

    _type = models.CharField(
        max_length=10,
        choices=FeatureBelongsTo.choices,
        default=FeatureBelongsTo.INTERNAL,
        db_index=True,
        verbose_name="Feature Type",
        help_text=(
            "Indicates whether the feature is"
            " for internal or external users ."
        )
    )

    is_custom = models.BooleanField(
        default=False,
        verbose_name="Custom Checker",
        help_text=(
            "Indicates if this is a custom feature ."
        )
    )

    name = models.CharField(
        max_length=50,
        null=False,
        blank=False,
        unique=True,
        db_index=True,
        verbose_name="Feature Name",
        help_text=(
            "The name of the feature"
        ),
    )

    buyer = models.BooleanField(
        default=True,
        verbose_name="Buyer",
        help_text=(
            "By default buyer is set to True . We need to ensure "
            "that it is always True ."
        )
    )

    max_invite = models.SmallIntegerField(
        default=subscription_defaults.get(
            "MAXIMUM_INVITE", 2
        ),
        verbose_name="Maximum Invite",
        validators=[
            MinValueValidator(2)
        ],
        help_text=(
            "Maximum number of invites allowed (non-negative)"
        ),
    )

    invite_commission = models.DecimalField(
        default=Decimal(
            subscription_defaults.get(
                "INVITE_COMMISSION", 10
            )
        ),
        max_digits=4,
        decimal_places=2,
        verbose_name="Invite Commission",
        validators=[
            MinValueValidator(
                Decimal("10.00")
            ),
            MaxValueValidator(
                Decimal("30.00")
            )
        ],
        help_text=(
            "Commission upon invite"
            " (in percentage and non-negative value)"
        ),
    )

    class Meta:
        verbose_name = "Default Feature"
        verbose_name_plural = "Default Features"
        constraints = [
            models.UniqueConstraint(
                fields=["name", "_type"],
                name=(
                    "default_feature__"
                    "unique_name_per_type"
                ),
            )
        ]
        db_table = f"{apps.get_app_config('accounts').label}__default_subscription"
        db_table_comment = (
            "This table stores default features related to subscriptions, "
            "including invite limits, commissions, and user types."
        )

    def __str__(self) -> str:
        return f"Default Feature | {self._type}"

    @property
    def get_invite_commission(self) -> Decimal:
        return f"{round(self.invite_commission, 2)} %"

    @property
    def get_max_invite(self) -> str:
        return (
            f"{self.max_invite} Person"
            if self.max_invite <= 1
            else f"{self.max_invite} People"
        )

    # Calculated for those who want an invite commission
    # greater than the default percentage (%)
    def invite_commission_price(self, user: User) -> str:
        invite_commission_price = (
            (
                (
                    self.invite_commission
                    - subscription_defaults.get(
                        "INVITE_COMMISSION", 10
                    )
                ) / 100
            )
            * self.UNIT_PRICE.get(
                "per_invite_commission", Decimal("2.50")
            ) if (
                Decimal(
                    self.invite_commission
                ) > Decimal(
                    subscription_defaults.get(
                        "INVITE_COMMISSION", 10
                    )
                )
            ) else Decimal("0.00")
        )

        price = invite_commission_price

        preferred_currency = default_currency.get(
            "code", "USD"
        )

        if user:
            user_settings = UserSettings.objects.get(
                user=user
            )
            preferred_currency = user_settings.preferred_currency.code
            exchange_rates = ExchangeRates()
            currency_eqv = exchange_rates.get_exchange_rate(
                to_currency=preferred_currency
            )

            price = price * currency_eqv
        return f"{round(price, 2)} {preferred_currency}"

    def invite_price(self, user: User = None) -> str:

        invite_price = (
            Decimal(
                self.max_invite
                * self.UNIT_PRICE.get(
                    "per_invite", Decimal("1.00")
                ) if (
                    int(
                        self.max_invite
                    ) > int(
                        subscription_defaults.get(
                            "MAXIMUM_INVITE", 2
                        )
                    )
                ) else Decimal("0.00")
            )
        )

        price = invite_price

        preferred_currency = default_currency.get(
            "code", "USD"
        )

        if user:
            user_settings = UserSettings.objects.get(
                user=user
            )
            preferred_currency = user_settings.preferred_currency.code
            exchange_rates = ExchangeRates()
            currency_eqv = exchange_rates.get_exchange_rate(
                to_currency=preferred_currency
            )

            price = price * currency_eqv
        return f"{round(price, 2)} {preferred_currency}"

    def price(self, user: User = None) -> str:
        """
        Calculates the total price for the feature by summing:
        - Price based on `max_invite` and `price_per_invite`.
        - Price based on `invite_commission` and `price_per_invite_commission`.
        """
        price = (
            # Conver to decimal after ...
            Decimal(
                # Getting the price in the format
                # `string(`decimal` `string`)`
                # that is to say the returned value
                # is of the form: 123 USD
                self.invite_price(
                    user=None
                ).split(" ")[0]  # then split it to get the decimal string
            )
            + Decimal(
                self.invite_commission_price(
                    user=None
                ).split(" ")[0]
            )
        )

        preferred_currency = default_currency.get(
            "code", "USD"
        )

        if user:
            user_settings = UserSettings.objects.get(
                user=user
            )
            preferred_currency = user_settings.preferred_currency.code
            exchange_rates = ExchangeRates()
            currency_eqv = exchange_rates.get_exchange_rate(
                to_currency=preferred_currency
            )
            price = currency_eqv * price

        return (
            f"{round(price, 2)} {preferred_currency}"
        )


class AIConflictResolutionAssistantFeature(models.Model):

    class FeatureBelongsTo(models.TextChoices):
        INTERNAL = "INTERNAL", "internal"
        EXTERNAL = "EXTERNAL", "external"

    UNIT_PRICE = {
        "per_conflict": Decimal("1.00"),
    }

    _type = models.CharField(
        max_length=10,
        choices=FeatureBelongsTo.choices,
        default=FeatureBelongsTo.INTERNAL,
        db_index=True,
        verbose_name="Feature Type",
        help_text=(
            "Indicates whether the feature is"
            " for internal or external users ."
        )
    )

    is_custom = models.BooleanField(
        default=False,
        verbose_name="Custom Checker",
        help_text=(
            "Indicates if this is a custom feature ."
        )
    )

    name = models.CharField(
        max_length=50,
        null=False,
        blank=False,
        unique=True,
        db_index=True,
        verbose_name="Feature Name",
        help_text=(
            "The name of the feature"
        ),
    )

    max_conflict = models.SmallIntegerField(
        default=(
            subscription_defaults.get(
                "MAXIMUM_CONFLICT", 1
            )
        ),
        validators=[
            MinValueValidator(1),
        ],
        verbose_name="Maximum Conflict",
        help_text=(
            "Maximum number of conflict required to solve ."
        ),
    )

    class Meta:
        verbose_name = "AI Conflict Resolution Assistant Feature"
        verbose_name_plural = "AI Conflict Resolution Assistant Feature"
        constraints = [
            models.UniqueConstraint(
                fields=["name", "_type"],
                name=(
                    "ai_conflict_resolution_assistant_feature__"
                    "unique_name_per_type"
                ),
            )
        ]
        db_table = (
            f"{apps.get_app_config('accounts').label}"
            "__ai_conflict_resolution_assistant"
        )
        db_table_comment = (
            "This table stores features related to conflict resolution, including "
            "the maximum number of conflicts that can be addressed."
        )

    @property
    def get_max_conflict(self) -> str:
        return (
            f"{self.max_conflict} Conflict"
            if self.max_conflict <= 1
            else f"{self.max_conflict} Conflicts"
        )

    def max_conflict_price(self, user):

        max_conflict_price = Decimal(
            self.max_conflict
            * self.UNIT_PRICE.get(
                "per_conflict", Decimal("1.00")
            )
        )

        price = max_conflict_price

        preferred_currency = default_currency.get(
            "code", "USD"
        )

        if user:
            user_settings = UserSettings.objects.get(
                user=user
            )
            preferred_currency = user_settings.preferred_currency.code
            exchange_rates = ExchangeRates()
            currency_eqv = exchange_rates.get_exchange_rate(
                to_currency=preferred_currency
            )

            price = price * currency_eqv
        return f"{round(price, 2)} {preferred_currency}"

    def price(self, user: User):
        """
        Calculates the total price for the feature by summing:
        - Price based on `max_invite` and `price_per_invite`.
        - Price based on `invite_commission` and `price_per_invite_commission`.
        """
        max_conflict_price = Decimal(
            # Conver to decimal after ...
            Decimal(
                # Getting the price in the format
                # `string(`decimal` `string`)`
                # that is to say the returned value
                # is of the form: 123 USD
                self.max_conflict_price(
                    user=None
                ).split(" ")[0]  # then split it to get the decimal string
            )
        )

        price = max_conflict_price

        preferred_currency = default_currency.get(
            "code", "USD"
        )

        if user:
            user_settings = UserSettings.objects.get(
                user=user
            )
            preferred_currency = user_settings.preferred_currency.code
            exchange_rates = ExchangeRates()
            currency_eqv = exchange_rates.get_exchange_rate(
                to_currency=preferred_currency
            )
            price = currency_eqv * price

        return (
            f"{round(price, 2)} {preferred_currency}"
        )


class TeamGoalFeature(models.Model):

    class FeatureBelongsTo(models.TextChoices):
        INTERNAL = "INTERNAL", "internal"
        EXTERNAL = "EXTERNAL", "external"

    UNIT_PRICE = {
        "per_team": Decimal("0.5"),
    }

    _type = models.CharField(
        max_length=10,
        choices=FeatureBelongsTo.choices,
        default=FeatureBelongsTo.INTERNAL,
        db_index=True,
        verbose_name="Feature Type",
        help_text=(
            "Indicates whether the feature is"
            " for internal or external users ."
        )
    )

    is_custom = models.BooleanField(
        default=False,
        verbose_name="Custom Checker",
        help_text=(
            "Indicates if this is a custom feature ."
        )
    )

    name = models.CharField(
        max_length=50,
        null=False,
        blank=False,
        unique=True,
        db_index=True,
        verbose_name="Feature Name",
        help_text=(
            "The name of the feature"
        ),
    )

    max_team = models.SmallIntegerField(
        default=(
            subscription_defaults.get(
                "MAXIMUM_TEAM", 1
            )
        ),
        validators=[
            MinValueValidator(1),
        ],
        verbose_name="Maximum Team",
        help_text=(
            "Grouping users into small groups for joint vacation or trip ."
        ),
    )

    conflict_resolver = models.OneToOneField(
        AIConflictResolutionAssistantFeature,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Conflict Resolver",
        help_text=(
            "For resolving conflict amongst teams ."
            " Probably teams who want to have a trip "
            "might have varying ideas and finds it difficult "
            "to come up with travel decisions ."
        ),
    )

    class Meta:
        verbose_name = "Team Goal Feature"
        verbose_name_plural = "Team Goal Features"
        constraints = [
            models.UniqueConstraint(
                fields=["name", "_type"],
                name=(
                    "team_goal_feature__"
                    "unique_name_per_type"
                ),
            )
        ]
        db_table = f"{apps.get_app_config('accounts').label}__team_goal"
        db_table_comment = (
            "This table stores features related to team goals, including "
            "maximum team size and conflict resolution settings."
        )

    def __str__(self):
        return f"{self.max_team} | Team Goal Feature"

    @property
    def get_max_team(self) -> str:
        return (
            f"{self.max_team} Person"
            if self.max_team <= 1
            else f"{self.max_team} People"
        )

    def max_team_price(self, user: User) -> str:
        """
        Calculate cummulative team package price
        """
        price = (
            self.max_team
            * self.UNIT_PRICE.get(
                "per_team", Decimal("0.5")
            )
        )

        preferred_currency = default_currency.get(
            "code", "USD"
        )

        if user:
            user_settings = UserSettings.objects.get(
                user=user
            )
            preferred_currency = user_settings.preferred_currency.code
            exchange_rates = ExchangeRates()
            currency_eqv = exchange_rates.get_exchange_rate(
                to_currency=preferred_currency
            )
            price = currency_eqv * price

        return (
            f"{round(price, 2)} {preferred_currency}"
        )

    def price(self, user: User) -> str:
        """
        Calculates the total price for the feature by summing:
        - Price based on `max_invite` and `price_per_invite`.
        - Price based on `invite_commission` and `price_per_invite_commission`.
        """

        conflict_resolver_price = Decimal(
            self.conflict_resolver.price(
                user=None
            ).split(" ")[0]
        ) if self.conflict_resolver else Decimal("0.00")

        max_team_price = Decimal(
            self.max_team_price(
                user=None
            ).split(" ")[0]
        )

        price = (
            conflict_resolver_price
            + max_team_price
        )

        preferred_currency = default_currency.get(
            "code", "USD"
        )

        if user:
            user_settings = UserSettings.objects.get(
                user=user
            )
            preferred_currency = user_settings.preferred_currency.code
            exchange_rates = ExchangeRates()
            currency_eqv = exchange_rates.get_exchange_rate(
                to_currency=preferred_currency
            )
            price = currency_eqv * price

        return (
            f"{round(price, 2)} {preferred_currency}"
        )


class AIMarketingAssistantFeature(models.Model):

    class FeatureBelongsTo(models.TextChoices):
        INTERNAL = "INTERNAL", "internal"
        EXTERNAL = "EXTERNAL", "external"

    UNIT_PRICE = {
        "per_round": Decimal("0.1"),
    }

    _type = models.CharField(
        max_length=10,
        choices=FeatureBelongsTo.choices,
        default=FeatureBelongsTo.INTERNAL,
        db_index=True,
        verbose_name="Feature Type",
        help_text=(
            "Indicates whether the feature is"
            " for internal or external users ."
        )
    )

    is_custom = models.BooleanField(
        default=False,
        verbose_name="Custom Checker",
        help_text=(
            "Indicates if this is a custom feature ."
        )
    )

    name = models.CharField(
        max_length=50,
        null=False,
        blank=False,
        unique=True,
        db_index=True,
        verbose_name="Feature Name",
        help_text=(
            "The name of the feature"
        ),
    )

    max_rounds = models.SmallIntegerField(
        default=(
            subscription_defaults.get(
                "AI_MARKETING_MAXIMUM_ROUNDS", 2
            )
        ),
        validators=[
            MinValueValidator(2),
        ],
        verbose_name="Maximum Rounds",
        help_text=(
            "Maximum time usage for AI marketing assistant "
            "feature per subscription ."
        ),
    )

    class Meta:
        verbose_name = "AI Marketing Assistant Feature"
        verbose_name_plural = "AI Marketing Assistant Features"
        constraints = [
            models.UniqueConstraint(
                fields=["name", "_type"],
                name=(
                    "ai_marketing_assistant_feature__"
                    "unique_name_per_type"
                ),
            )
        ]
        db_table = f"{apps.get_app_config('accounts').label}__ai_marketing_assistant"
        db_table_comment = (
            "The AIMarketingAssistantFeature table defines features "
            "related to an AI-powered marketing assistant. "
            "This assistant provides users with data-driven insights and "
            "recommendations to optimize property marketing strategies, "
            "including pricing and advertising. "
            "The '_type' field specifies whether the feature is for internal or "
            "external users, while 'is_custom' indicates if the feature "
            "has been customized. 'max_rounds' limits the number of times the "
            "AI assistant can be used per subscription. "
            "Each feature is uniquely identified by its name and type."
        )

    def __str__(self):
        return f"{self.max_rounds} | AI Marketing Assistant"

    @property
    def get_max_rounds(self) -> str:
        return (
            f"{self.max_rounds} Round"
            if self.max_rounds <= 1
            else f"{self.max_rounds} Rounds"
        )

    def max_rounds_price(self, user: User) -> str:
        price = (
            self.max_rounds
            * self.UNIT_PRICE.get(
                "per_round", Decimal("0.1")
            )
        )

        preferred_currency = default_currency.get(
            "code", "USD"
        )

        if user:
            user_settings = UserSettings.objects.get(
                user=user
            )
            preferred_currency = user_settings.preferred_currency.code
            exchange_rates = ExchangeRates()
            currency_eqv = exchange_rates.get_exchange_rate(
                to_currency=preferred_currency
            )
            price = currency_eqv * price

        return (
            f"{round(price, 2)} {preferred_currency}"
        )

    def price(self, user: User):
        max_rounds_price = Decimal(
            self.max_rounds_price(
                user=None
            ).split(" ")[0]
        )

        price = max_rounds_price

        preferred_currency = default_currency.get(
            "code", "USD"
        )

        if user:
            user_settings = UserSettings.objects.get(
                user=user
            )
            preferred_currency = user_settings.preferred_currency.code
            exchange_rates = ExchangeRates()
            currency_eqv = exchange_rates.get_exchange_rate(
                to_currency=preferred_currency
            )
            price = currency_eqv * price

        return (
            f"{round(price, 2)} {preferred_currency}"
        )


class MultiLevelMarketingFeature(models.Model):

    class FeatureBelongsTo(models.TextChoices):
        INTERNAL = "INTERNAL", "internal"
        EXTERNAL = "EXTERNAL", "external"

    UNIT_PRICE = {
        "per_sale_commission": Decimal("0.85"),
        "per_rental_commission": Decimal("0.55"),
    }

    _type = models.CharField(
        max_length=10,
        choices=FeatureBelongsTo.choices,
        default=FeatureBelongsTo.INTERNAL,
        db_index=True,
        verbose_name="Feature Type",
        help_text=(
            "Indicates whether the feature is"
            " for internal or external users ."
        )
    )

    is_custom = models.BooleanField(
        default=False,
        verbose_name="Custom Checker",
        help_text=(
            "Indicates if this is a custom feature ."
        )
    )

    name = models.CharField(
        max_length=50,
        null=False,
        blank=False,
        unique=True,
        db_index=True,
        verbose_name="Feature Name",
        help_text=(
            "The name of the feature"
        ),
    )

    # Commission given to User from LaLouge Remaining Commission
    sale_commission = models.DecimalField(
        default=(
            subscription_defaults.get(
                "SALE_COMMISSION", Decimal("1.00")
            )
        ),
        validators=[
            MinValueValidator(Decimal("1.00")),
            MaxValueValidator(Decimal("30.00")),
        ],
        max_digits=4,
        decimal_places=2,
        verbose_name="Sales Commission",
        help_text=(
            "Commission a user in this plan receives upon the sale of any property. "
            "The commission follows a multi-level marketing model, where a percentage "
            "is earned directly by the seller and additional portions are distributed "
            "to users in higher levels of the hierarchy."
        ),
    )

    rental_commission = models.DecimalField(
        default=(
            subscription_defaults.get(
                "RENTAL_COMMISSION", Decimal("5.00")
            )
        ),
        validators=[
            MinValueValidator(Decimal("5.00")),
            MaxValueValidator(Decimal("30.00")),
        ],
        max_digits=4,
        decimal_places=2,
        verbose_name="Rental Commission",
        help_text=(
            "Commission a user in this plan receives upon the rentage of any property. "
            "The commission follows a multi-level marketing model, where a percentage "
            "is earned directly by the renter and additional portions are distributed "
            "to users in higher levels of the hierarchy."
        ),
    )

    class Meta:
        verbose_name = "Multi-Level Marketing Feature"
        verbose_name_plural = "Multi-Level Marketing Features"
        constraints = [
            models.UniqueConstraint(
                fields=["name", "_type"],
                name=(
                    "multilevel_marketing_feature__"
                    "unique_name_per_type"
                ),
            )
        ]
        db_table = f"{apps.get_app_config('accounts').label}__multilevel_marketing"
        db_table_comment = (
            "The MultiLevelMarketingFeature table defines features that "
            "support a multi-level marketing model within the platform. "
            "Each feature specifies commissions earned by users based on "
            "property sales and rentals, with additional hierarchical payouts "
            "to higher-level users. The '_type' field distinguishes whether "
            "the feature is internal or external, and 'is_custom' indicates "
            "whether the feature is customized. Each feature is uniquely "
            "identified by its name and type, ensuring no duplicates."
        )

    def __str__(self):
        return f"Multi-level Marketing Feature | {self._type}"

    @property
    def get_sale_commission(self) -> Decimal:
        return f"{round(self.sale_commission, 2)} %"

    @property
    def get_rental_commission(self) -> Decimal:
        return f"{round(self.rental_commission, 2)} %"

    def sale_commission_price(self, user: User):
        sale_commission_price = Decimal(
            (
                (
                    self.sale_commission
                    - Decimal(
                        subscription_defaults.get(
                            "SALE_COMMISSION", "0.01"
                        )
                    )
                ) / 100
            )
            * Decimal(
                self.UNIT_PRICE.get(
                    "per_sale_commission", "0.85"
                )
            )
        ) if (
            self.sale_commission
            > Decimal(
                subscription_defaults.get(
                    "SALE_COMMISSION", "0.01"
                )
            )
        ) else Decimal("0.00")

        price = sale_commission_price

        preferred_currency = default_currency.get(
            "code", "USD"
        )

        if user:
            user_settings = UserSettings.objects.get(
                user=user
            )
            preferred_currency = user_settings.preferred_currency.code
            exchange_rates = ExchangeRates()
            currency_eqv = exchange_rates.get_exchange_rate(
                to_currency=preferred_currency
            )
            price = currency_eqv * price

        return (
            f"{round(price, 2)} {preferred_currency}"
        )

    def rental_commission_price(self, user: User):
        rental_commission_price = Decimal(
            (
                (
                    self.rental_commission
                    - Decimal(
                        subscription_defaults.get(
                            "RENTAL_COMMISSION", "0.05"
                        )
                    )
                ) / 100
            )
            * self.UNIT_PRICE.get(
                "per_rental_commission", Decimal("0.85")
            )
        ) if (
            self.rental_commission
            > Decimal(
                subscription_defaults.get(
                    "RENTAL_COMMISSION", "0.05"
                )
            )
        ) else Decimal("0.00")

        price = rental_commission_price

        preferred_currency = default_currency.get(
            "code", "USD"
        )

        if user:
            user_settings = UserSettings.objects.get(
                user=user
            )
            preferred_currency = user_settings.preferred_currency.code
            exchange_rates = ExchangeRates()
            currency_eqv = exchange_rates.get_exchange_rate(
                to_currency=preferred_currency
            )
            price = currency_eqv * price

        return (
            f"{round(price, 2)} {preferred_currency}"
        )

    def price(self, user: User):
        price = (
            Decimal(
                self.sale_commission_price(
                    user=None
                ).split(" ")[0]
            )
            + Decimal(
                self.rental_commission_price(
                    user=None
                ).split(" ")[0]
            )
        )

        preferred_currency = default_currency.get(
            "code", "USD"
        )

        if user:
            user_settings = UserSettings.objects.get(
                user=user
            )
            preferred_currency = user_settings.preferred_currency.code
            exchange_rates = ExchangeRates()
            currency_eqv = exchange_rates.get_exchange_rate(
                to_currency=preferred_currency
            )
            price = currency_eqv * price

        return (
            f"{round(price, 2)} {preferred_currency}"
        )


class BusinessFeature(models.Model):

    class FeatureBelongsTo(models.TextChoices):
        INTERNAL = "INTERNAL", "internal"
        EXTERNAL = "EXTERNAL", "external"

    UNIT_PRICE = {
        "per_sale_deduction": Decimal("1.00"),
        "per_rental_deduction": Decimal("1.00"),
        "per_storage_space": Decimal("1.00"),
        "per_consultation_hour": Decimal("1.00"),
    }

    _type = models.CharField(
        max_length=10,
        choices=FeatureBelongsTo.choices,
        default=FeatureBelongsTo.INTERNAL,
        db_index=True
    )

    is_custom = models.BooleanField(
        default=False,
        verbose_name="Custom Checker",
        help_text=(
            "Indicates if this is a custom feature ."
        )
    )

    name = models.CharField(
        max_length=50,
        null=False,
        blank=False,
        db_index=True
    )

    seller = models.BooleanField(
        default=True
    )

    # Commission given to LaLouge from the sale of user's property
    sale_deduction = models.DecimalField(
        null=True,
        blank=True,
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("2.00")),
        ],
        verbose_name="Sale Deduction",
        help_text=(
            "Commission on sale the system receives ."
            "For non-standard feature it should default to 10.00%"
        )
    )

    # Commission given to LaLouge from the rentage of user's property
    rental_deduction = models.DecimalField(
        null=True,
        blank=True,
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("2.00")),
        ],
        verbose_name="Rental Deduction",
        help_text=(
            "Commission on rent the system receives ."
            "For non-standard feature it should default to 10.00%"
        )
    )

    # storage space is in Mb
    storage_space = models.DecimalField(
        null=True,
        blank=True,
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("1024.00")),
        ],
        verbose_name="Storage Space",
        help_text=(
            "Space allocated for the storage of property media contents ."
            "For non-standard feature it should default to 1024.00 MB ."
        )
    )

    # consultation hours in minutes default = 120 minutes = 2 hours
    consultation_hours = models.DecimalField(
        null=True,
        blank=True,
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("120.00")),
        ],
        verbose_name="Consultation Hour",
        help_text=(
            "Allocated consultation hours with the real estate experts ."
            "For non-standard feature it should default to 120.00 minutes"
        )
    )

    marketing_assistant = models.OneToOneField(
        AIMarketingAssistantFeature,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Marketing Assistant",
        help_text=(
            "Assists in proposing marketing decisions "
            "in terms of pricing, advertisement etc "
            "to realtors on the platform"
        ),
    )

    mlm_feature = models.OneToOneField(
        MultiLevelMarketingFeature,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Multi-Level Marketing Feature"
    )

    class Meta:
        verbose_name = "Business Feature"
        verbose_name_plural = "Business Features"
        constraints = [
            models.UniqueConstraint(
                fields=["name", "_type"],
                name=(
                    "business_feature__"
                    "unique_name_per_type"
                ),
            )
        ]
        db_table = f"{apps.get_app_config('accounts').label}__business"
        db_table_comment = (
            "The BusinessFeature table defines specific features "
            "and settings tailored for business purposes within the platform. "
            "Each feature is classified as either internal or external, "
            "with optional customization indicated by the 'is_custom' field. "
            "Features include details like commissions on sales and "
            "rentals, storage space allocation, and consultation hours. "
            "Additional features such as a marketing assistant or "
            "multi-level marketing support can be associated. "
            "Unique constraints ensure that each combination of 'name' "
            "and '_type' is distinct, allowing clear categorization and "
            "management of features."
        )

    def __str__(self):
        return f"Business Feature | {self._type}"

    @property
    def get_sale_deduction(self) -> Decimal:
        return f"{round(self.sale_deduction, 2)} %"

    @property
    def get_rental_deduction(self) -> Decimal:
        return f"{round(self.rental_deduction, 2)} %"

    @property
    def get_storage_space(self) -> Decimal:
        return f"{round(self.storage_space/1024, 2)} GB"

    @property
    def get_consultation_hours(self) -> Decimal:
        return f"{round(self.consultation_hours/60, 2)} Hours"

    def sale_deduction_price(self, user: User):
        price = (
            (self.sale_deduction / 100)
            * self.UNIT_PRICE["per_sale_deduction"]
        )

        preferred_currency = (
            default_currency["code"]
            if default_currency["code"]
            else "USD"
        )

        if user:
            user_settings = UserSettings.objects.get(
                user=user
            )
            preferred_currency = user_settings.preferred_currency.code
            exchange_rates = ExchangeRates()
            currency_eqv = exchange_rates.get_exchange_rate(
                to_currency=preferred_currency
            )
            price = currency_eqv * price

        return (
            f"{round(price, 2)} {preferred_currency}"
        )

    def rental_deduction_price(self, user: User):
        price = (
            (self.rental_deduction / 100)
            * self.UNIT_PRICE["per_rental_deduction"]
        )

        preferred_currency = (
            default_currency["code"]
            if default_currency["code"]
            else "USD"
        )

        if user:
            user_settings = UserSettings.objects.get(
                user=user
            )
            preferred_currency = user_settings.preferred_currency.code
            exchange_rates = ExchangeRates()
            currency_eqv = exchange_rates.get_exchange_rate(
                to_currency=preferred_currency
            )
            price = currency_eqv * price

        return (
            f"{round(price, 2)} {preferred_currency}"
        )

    def storage_space_price(self, user: User):
        price = (
            (self.storage_space / 100)
            * self.UNIT_PRICE["per_storage_space"]
        )

        preferred_currency = (
            default_currency["code"]
            if default_currency["code"]
            else "USD"
        )

        if user:
            user_settings = UserSettings.objects.get(
                user=user
            )
            preferred_currency = user_settings.preferred_currency.code
            exchange_rates = ExchangeRates()
            currency_eqv = exchange_rates.get_exchange_rate(
                to_currency=preferred_currency
            )
            price = currency_eqv * price

        return (
            f"{round(price, 2)} {preferred_currency}"
        )

    def consultation_hours_price(self, user: User):

        consultation_hours = Decimal(
            self.consultation_hours / 60
        )

        price = (
            consultation_hours
            * self.UNIT_PRICE["per_consultation_hour"]
        )

        preferred_currency = (
            default_currency["code"]
            if default_currency["code"]
            else "USD"
        )

        if user:
            user_settings = UserSettings.objects.get(
                user=user
            )
            preferred_currency = user_settings.preferred_currency.code
            exchange_rates = ExchangeRates()
            currency_eqv = exchange_rates.get_exchange_rate(
                to_currency=preferred_currency
            )
            price = currency_eqv * price

        return (
            f"{round(price, 2)} {preferred_currency}"
        )

    def price(self, user: User):

        sale_deduction_price = Decimal(
            self.sale_deduction_price(
                user=None
            ).split(" ")[0]
        )

        rental_deduction_price = Decimal(
            self.rental_deduction_price(
                user=None
            ).split(" ")[0]
        )

        storage_space_price = Decimal(
            self.storage_space_price(
                user=None
            ).split(" ")[0]
        )

        consultation_hours_price = Decimal(
            self.consultation_hours_price(
                user=None
            ).split(" ")[0]
        )

        mlm_feature_price = Decimal(
            self.mlm_feature.price(
                user=None
            ).split(" ")[0]
        ) if self.mlm_feature else 0

        marketing_assistant_price = Decimal(
            self.marketing_assistant.price(
                user=None
            ).split(" ")[0]
        ) if self.marketing_assistant else 0

        price = (
            sale_deduction_price
            + rental_deduction_price
            + storage_space_price
            + consultation_hours_price
            + mlm_feature_price
            + marketing_assistant_price
        )

        preferred_currency = (
            default_currency["code"]
            if default_currency["code"]
            else "USD"
        )

        if user:
            user_settings = UserSettings.objects.get(
                user=user
            )
            preferred_currency = user_settings.preferred_currency.code
            exchange_rates = ExchangeRates()
            currency_eqv = exchange_rates.get_exchange_rate(
                to_currency=preferred_currency
            )
            price = currency_eqv * price

        return (
            f"{round(price, 2)} {preferred_currency}"
        )


class SubscriptionPlan(models.Model):

    class FeatureBelongsTo(models.TextChoices):
        INTERNAL = "INTERNAL", "internal"
        EXTERNAL = "EXTERNAL", "external"

    _type = models.CharField(
        max_length=10, choices=FeatureBelongsTo.choices,
        default=FeatureBelongsTo.INTERNAL,
        db_index=True
    )

    is_custom = models.BooleanField(default=False)

    name = models.CharField(max_length=25)

    description = models.TextField()

    is_active = models.BooleanField(default=False)

    # features

    default_feature = models.OneToOneField(
        DefaultFeature,
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        verbose_name="Default Feature",
        help_text=(
            "Everything suppose to have a default feature ."
            " If no default feature then subscription is nullified ."
        ),
    )

    team_feature = models.OneToOneField(
        TeamGoalFeature,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Team",
    )

    business_feature = models.OneToOneField(
        BusinessFeature,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    objects = SubscriptionPlanManager()

    class Meta:
        verbose_name = "Subscription Plan"
        verbose_name_plural = "Subscription Plans"
        constraints = [
            models.UniqueConstraint(
                fields=["name", "_type"],
                name=(
                    "subscription_plan__"
                    "unique_name_per_type"
                ),
            )
        ]
        db_table = f"{apps.get_app_config('accounts').label}__subscription"
        db_table_comment = (
            "The SubscriptionPlan table defines the various subscription plans "
            "available in the system. Each plan can either be internal or external "
            "as specified by the '_type' field. Plans include a name, description, "
            "and activation status. They also specify associated features such as a "
            "mandatory default feature and an optional business-specific feature. "
            "A unique constraint ensures that each combination of 'name' and '_type' "
            "is distinct, preventing duplication."
        )

    def __str__(self) -> str:
        return f"{self.name} | {self._type}"

    def price(self, user: User) -> Decimal:
        default_feature_price = Decimal(
            self.default_feature.price(
                user=None
            ).split(" ")[0]
        ) if self.default_feature else Decimal("0.00")

        team_feature_price = Decimal(
            self.team_feature.price(
                user=None
            ).split(" ")[0]
        ) if self.team_feature else Decimal("0.00")

        business_feature_price = Decimal(
            self.business_feature.price(
                user=None
            ).split(" ")[0]
        ) if self.business_feature else Decimal("0.00")

        price = (
            default_feature_price
            + team_feature_price
            + business_feature_price
        )

        preferred_currency = (
            default_currency["code"]
            if default_currency["code"]
            else "USD"
        )

        if user:
            user_settings = UserSettings.objects.get(
                user=user
            )
            preferred_currency = user_settings.preferred_currency.code
            exchange_rates = ExchangeRates()
            currency_eqv = exchange_rates.get_exchange_rate(
                to_currency=preferred_currency
            )
            price = currency_eqv * price

        return (
            f"{round(price, 2)} {preferred_currency}"
        )

    @classmethod
    def get_active_plan(cls, auto: bool = True,
                        *args, **kwargs) -> models.Model:

        manager = cls.objects

        if not auto:
            return manager.get_active_plan(auto=False, *args, **kwargs)

        return manager.get_active_plan(*args, **kwargs)


class UserSubscriptionPlan(models.Model):
    class SubscriptionDuration(models.TextChoices):
        MONTHLY = 'MONTHLY', 'monthly'
        YEARLY = 'YEARLY', 'yearly'
        LIFETIME = "LIFE TIME", "life time"

    TIME_UNITS = {
        SubscriptionDuration.MONTHLY: 'MONTH',
        SubscriptionDuration.YEARLY: 'YEAR',
        SubscriptionDuration.LIFETIME: "LIFE TIME"
    }

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    subscription_plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.SET_NULL,
        null=True
    )

    duration = models.CharField(
        max_length=9,
        choices=SubscriptionDuration.choices,
        default=SubscriptionDuration.MONTHLY
    )

    duration_period = models.PositiveSmallIntegerField(default=1)

    price = models.DecimalField(
        null=False,
        blank=False,
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0.00")),
        ],
        verbose_name="Price",
        help_text=(
            "Price for user subscription ."
        )
    )

    is_active = models.BooleanField(
        default=False
    )

    # getting duration in terms of MONTHLY or YEARLY
    @property
    def formatted_duration(self):
        duration = self.duration_period
        time_unit = self.TIME_UNITS.get(self.duration, 'invalid duration')
        return f'{duration} {time_unit}S' if duration > 1 else f'1 {time_unit}'

    # This also needs to be worked on
    @property
    def formatted_price(self):
        plan_instance = SubscriptionPlan.objects.get(pk=self.plan.pk)

        # Access the associated SubscriptionPlan
        subscription_plan = plan_instance.price

        # Call the formatted_price property on the SubscriptionPlan
        formatted_price = subscription_plan.formatted_price(subscription_plan)
        return formatted_price
