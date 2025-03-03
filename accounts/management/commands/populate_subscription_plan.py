from django.core.management.base import BaseCommand, CommandError
from accounts.models.plans import (
    DefaultFeature, AIConflictResolutionAssistantFeature,
    AIMarketingAssistantFeature, MultiLevelMarketingFeature,
    SubscriptionPlan, BusinessFeature, TeamGoalFeature
)

from tqdm import tqdm

import time


plan_description = {
    "standard": {
        "default": (
            "The base standard plan offering core "
            "features for individual users."
        ),
        "team": (
            "The standard plan designed for team "
            "collaboration and shared resources."
        ),
        "mlm": (
            "A standard plan tailored for multi-level "
            "marketing needs, such as commission tracking."
        ),
        "inclusive": (
            "A comprehensive standard plan combining "
            "all available features."
        )
    },
    "business": {
        "default": (
            "The base business plan offering essential "
            "features for professional use."
        ),
        "team": (
            "The business plan optimized for teams, "
            "enhancing productivity and collaboration."
        ),
        "mlm": (
            "A business plan focused on multi-level "
            "marketing support for enterprises."
        ),
        "inclusive": (
            "An all-inclusive business plan with the full "
            "range of features for maximum capability."
        )
    }
}


class Command(BaseCommand):
    help = "Populate SubscriptionPlan table with sample data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--type", type=str,
            help=(
                "Specifies whether the feature is: "
                "INTERNAL or EXTERNAL FEATURE"
            )
        )

        parser.add_argument(
            "--custom", type=str,
            help=(
                "Specifies whether the feature is: "
                "custom (system default features) or "
                "is not custom (user defined feature)"
            )
        )

    def process_with_progress_bar(self, items, description, callback):
        """
        Reusable function to process items with a progress bar and animation.

        Parameters:
            items: List of items to process.
            description: Description for the progress bar.
            callback: Function to execute for each item.
        """
        with tqdm(
            total=len(items),
            desc=description,
            unit="item",
            bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} items [Elapsed: {elapsed}]",
            colour="blue"
        ) as progress_bar:
            for item in items:
                callback(item)
                time.sleep(0.3)  # Simulate a delay
                progress_bar.update(1)

    def handle(self, *args, **options):
        """
        Handle the management command to process subscription plans.

        Parameters:
            *args: Positional arguments (not used).
            **options: Keyword options containing the type and plan names.

        Raises:
            CommandError: If there is an error during subscription creation.
        """
        # Retrieve the type and convert it to uppercase
        _type = str(options.get("type")).upper()

        # Define the list of plan names
        plan_names = [
            "standard", "standard__team", "standard__mlm", "standard__inclusive",
            "business", "business__team", "business__mlm", "business__inclusive"
        ]

        # Pair the type with each plan name
        plans = [(_type, plan_name) for plan_name in plan_names]

        try:
            # Process plans using the reusable progress bar function
            self.process_with_progress_bar(
                items=plans,
                description="Processing Plans",
                callback=lambda plan: self.process_plan(*plan)
            )

            # Output success message
            self.stdout.write(
                self.style.SUCCESS(
                    "Successfully processed all subscription plans."
                )
            )
        except Exception as e:
            # Handle errors
            self.stderr.write(
                self.style.ERROR(
                    f"Error occurred during subscription creation: {e}"
                )
            )
            raise CommandError(
                f"Error occurred during subscription creation: {e}"
            )

    def process_plan(self, _type: str, plan_name: str) -> None:
        """
        Process a single plan by creating features and
        subscription plans.

        Parameters:
            _type (str): The type of the plan.
            plan_name (str): The name of the plan.

        Raises:
            Exception: If there is an error during processing.
        """
        try:
            # Create the default feature for the plan
            default_feature = self.create_default_feature(
                _type=_type, plan_name=plan_name
            )

            # Create subscription plans based on the plan type
            if plan_name == "standard":
                self.create_subscription_plan(
                    default_feature=default_feature,
                    _type=_type,
                    plan_name=plan_name
                )
            else:
                self.create_non_standard_plan(
                    _type=_type, plan_name=plan_name,
                    default_feature=default_feature
                )

            # Output success message
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully created subscription plan for {plan_name}\n"
                )
            )
        except Exception as e:
            # Output error message with details and
            # re-raise the exception
            self.stderr.write(
                self.style.ERROR(
                    f"Error processing plan {plan_name}: {e}"
                )
            )

            # Re-raise the exception to allow external
            # handling if necessary
            raise

    def create_non_standard_plan(
        self, _type: str, plan_name: str, default_feature
    ):
        """
        Create subscription plans for non-standard plan names.

        Parameters:
            _type (str): The type of the plan.
            plan_name (str): The name of the plan.
            default_feature: The default feature associated with the plan.

        Returns:
            SubscriptionPlan: The created subscription plan instance.
        """

        if plan_name == "business":
            business_feature = self.create_business_feature(
                _type=_type, plan_name=plan_name
            )

            return self.create_subscription_plan(
                default_feature=default_feature,
                business_feature=business_feature,
                _type=_type,
                plan_name=plan_name
            )

        # Initialize team and business features to None
        team_feature = None
        business_feature = None

        # Split the plan name to extract prefix and suffix
        split_plan = plan_name.split("__")
        if len(split_plan) != 2:
            self.stderr.write(
                self.style.ERROR(
                    f"Plan name `{plan_name}` invalid."
                )
            )
            raise

        prefix, suffix = split_plan

        # Handle standard plan cases
        if prefix == "standard":
            if suffix == "team":
                team_feature = self.create_team_goal_feature(
                    _type=_type, plan_name=plan_name
                )
            elif suffix == "mlm":
                business_feature = self.create_business_feature(
                    _type=_type, plan_name=plan_name
                )
            elif suffix == "inclusive":
                team_feature = self.create_team_goal_feature(
                    _type=_type, plan_name=plan_name
                )
                business_feature = self.create_business_feature(
                    _type=_type, plan_name=plan_name
                )

        # Handle business plan cases
        elif prefix == "business":
            if suffix == "team":
                team_feature = self.create_team_goal_feature(
                    _type=_type, plan_name=plan_name
                )
            business_feature = self.create_business_feature(
                _type=_type, plan_name=plan_name
            )

        # Create the subscription plan with the provided features
        return self.create_subscription_plan(
            default_feature=default_feature,
            business_feature=business_feature,
            team_feature=team_feature,
            _type=_type,
            plan_name=plan_name
        )

    def create_default_feature(
        self, _type: str, plan_name: str
    ):
        """
        Create or retrieve a DefaultFeature instance based on a common prefix.

        Args:
            _type (str): The type of the feature (e.g., 'INTERNAL', 'EXTERNAL').
            plan_name (str): The plan name to associate with the feature.

        Returns:
            DefaultFeature: The retrieved or newly created DefaultFeature instance.
        """
        try:

            default_feature, created = DefaultFeature.objects.get_or_create(
                _type=_type,
                name=plan_name
            )

            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Created DefaultFeature: {default_feature.name}"
                    )
                )
            else:
                # https://docs.djangoproject.com/en/5.1/ref/django-admin/#syntax-coloring
                self.stdout.write(
                    self.style.HTTP_INFO(
                        f"DefaultFeature: `{default_feature.name}` already exists"
                    )
                )

            return default_feature

        except Exception as e:
            self.stderr.write(
                self.style.ERROR(
                    f"Error creating DefaultFeature: {e}"
                )
            )
            raise

    def ai_conflict_resolution_assistant_feature(
        self, _type: str, plan_name: str, max_conflict=None
    ):
        """
        Create and return an instance of AIConflictResolutionAssistantFeature.

        Parameters:
            _type (str): The type of the feature.
            plan_name (str): The name of the plan.
            max_conflict (int, optional): The maximum number of
            conflicts to resolve.

        Returns:
            AIConflictResolutionAssistantFeature: The created
            conflict resolution assistant feature instance.
        """

        # If max_conflict is provided and is an integer, set it on the feature
        if max_conflict and not isinstance(max_conflict, int):
            # Log a warning if the max_conflict is not a valid integer
            self.stderr.write(
                self.style.WARNING(
                    f"Invalid `max_conflict` value: {max_conflict}. "
                    "It must be an integer."
                )
            )

        # Initialize the feature with the provided type and plan name
        feature, created = (
            AIConflictResolutionAssistantFeature.objects.get_or_create(
                _type=_type,
                name=plan_name,
                defaults={'max_conflict': max_conflict} if max_conflict else {},
            )
        )

        if created:
            # Output a success message
            self.stdout.write(
                self.style.SUCCESS(
                    f"Created {AIConflictResolutionAssistantFeature.__name__}: "
                    f"{feature.name}"
                )
            )
        else:
            self.stdout.write(
                self.style.HTTP_INFO(
                    f"{AIConflictResolutionAssistantFeature.__name__}: "
                    f"`{feature.name}` already exists"
                )
            )

        # Return the created feature instance
        return feature

    def create_team_goal_feature(
        self, _type: str, plan_name: str
    ):
        """
        Create and return an instance of TeamGoalFeature
        based on the provided _type and plan_name.

        Parameters:
            _type (str): The type of the feature.
            plan_name (str): The name of the plan, influencing
            the feature's configuration.

        Returns:
            TeamGoalFeature: The created team goal feature instance.
        """

        # Initialize the TeamGoalFeature with the provided
        # type and plan name
        feature, created = (
            TeamGoalFeature.objects.get_or_create(
                _type=_type,
                name=plan_name,
                defaults={
                    'conflict_resolver': (
                        self.ai_conflict_resolution_assistant_feature(
                            _type=_type,
                            plan_name=plan_name,
                            max_conflict=3
                            if plan_name in (
                                "business__team", "business__inclusive"
                            ) else None
                        )
                    )
                }
            )
        )

        if created:
            # Output a success message
            self.stdout.write(
                self.style.SUCCESS(
                    f"Created {TeamGoalFeature.__name__}: "
                    f"{feature.name}"
                )
            )
        else:
            self.stdout.write(
                self.style.HTTP_INFO(
                    f"{TeamGoalFeature.__name__}: "
                    f"`{feature.name}` already exists"
                )
            )

        # Return the created team goal feature instance
        return feature

    def create_ai_marketing_assistant_feature(
        self, _type: str, plan_name: str
    ):
        """
        Create and return an AI Marketing Assistant Feature
        instance based on the provided _type and plan_name.

        Parameters:
            _type (str): The type of the AI marketing assistant
            feature. plan_name (str): The name of the plan, which
            influences the feature's configuration.

        Returns:
            AIMarketingAssistantFeature: The created AI marketing
            assistant feature instance.
        """

        # Initialize the AI marketing assistant feature
        # with provided type and name
        ai_marketing_assistant_feature, created = (
            AIMarketingAssistantFeature.objects.get_or_create(
                _type=_type,
                name=plan_name,
            )
        )

        if created:
            # Output a success message
            self.stdout.write(
                self.style.SUCCESS(
                    f"Created {AIMarketingAssistantFeature.__name__}: "
                    f"{ai_marketing_assistant_feature.name}"
                )
            )
        else:
            self.stdout.write(
                self.style.HTTP_INFO(
                    f"{AIMarketingAssistantFeature.__name__}: "
                    f"`{ai_marketing_assistant_feature.name}` already exists"
                )
            )

        # Return the saved AI marketing assistant feature instance
        return ai_marketing_assistant_feature

    def create_multilevel_marketing_feature(
        self, _type: str, plan_name: str
    ):
        """
        Create and return a MultiLevelMarketingFeature
        instance based on the provided _type and plan_name.

        Parameters:
            _type (str): The type of the marketing feature.
            plan_name (str): The name of the plan which
            determines the feature's properties.

        Returns:
            MultiLevelMarketingFeature: The created MLM
            feature instance.
        """

        # Initialize the MultiLevelMarketingFeature
        # with provided type and name
        mlm_feature, created = (
            MultiLevelMarketingFeature.objects.get_or_create(
                _type=_type,
                name=plan_name,
            )
        )

        if created:
            # Output a success message
            self.stdout.write(
                self.style.SUCCESS(
                    f"Created {MultiLevelMarketingFeature.__name__}: "
                    f"{mlm_feature.name}"
                )
            )
        else:
            self.stdout.write(
                self.style.HTTP_INFO(
                    f"{MultiLevelMarketingFeature.__name__}: "
                    f"`{mlm_feature.name}` already exists"
                )
            )

        # Return the saved MLM feature instance
        return mlm_feature

    def create_business_feature(
        self, _type: str, plan_name: str
    ):
        """
        Create and return a BusinessFeature instance
        based on the provided _type and plan_name.

        Parameters:
            _type (str): The type of the business feature.
            plan_name (str): The name of the plan which
            determines the feature's properties.

        Returns:
            BusinessFeature: The created business
            feature instance.
        """

        # Create a basic BusinessFeature instance
        # with type and name
        business_feature, created = (
            BusinessFeature.objects.get_or_create(
                _type=_type,
                name=plan_name,
                defaults={
                    'seller': (
                        True
                        if plan_name in (
                            "business", "business__mlm",
                            "business__inclusive"
                        )
                        else False
                    ),
                    'mlm_feature': (
                        self.create_multilevel_marketing_feature(
                            _type=_type, plan_name=plan_name
                        )
                        if plan_name in (
                            "standard__mlm", "standard__inclusive",
                            "business__mlm", "business__inclusive"
                        ) else None
                    ),
                    'marketing_assistant': (
                        self.create_ai_marketing_assistant_feature(
                            _type=_type, plan_name=plan_name
                        )
                        if plan_name in (
                            "business", "business__mlm",
                            "business__inclusive"
                        )
                        else None
                    ),
                },
            )
        )

        if created:
            # Output a success message
            self.stdout.write(
                self.style.SUCCESS(
                    f"Created {BusinessFeature.__name__}: "
                    f"{business_feature.name}"
                )
            )
        else:
            self.stdout.write(
                self.style.HTTP_INFO(
                    f"{BusinessFeature.__name__}: "
                    f"`{business_feature.name}` already exists"
                )
            )

        return business_feature

    def create_subscription_plan(
        self, default_feature, business_feature=None, team_feature=None,
        _type: str = "", plan_name: str = ""
    ):
        """
        Create and return a SubscriptionPlan instance.

        Parameters:
        - default_feature: The default feature for the plan.
        - business_feature: The business-specific feature for the plan.
        - team_feature: The team-specific feature for the plan.
        - _type: The type of subscription plan
          (e.g., 'internal', 'external').
        - plan_name: The name of the subscription plan
          (e.g., 'standard', 'business', 'custom__team').

        Returns:
        - A SubscriptionPlan instance.
        """

        if (
            business_feature
            and not isinstance(business_feature, BusinessFeature)
        ):
            error_message = (
                f"The provided `business_feature` value `{business_feature}` "
                f"is not an instance of the "
                f"`{self.style.WARNING(BusinessFeature.__name__, bold=True)}` model."
            )
            self.stderr.write(self.style.ERROR(error_message))
            raise

        if (
            team_feature
            and not isinstance(team_feature, TeamGoalFeature)
        ):
            error_message = (
                f"The provided `business_feature` value `{team_feature}` "
                f"is not an instance of the "
                f"`{self.style.WARNING(TeamGoalFeature.__name__, bold=True)}` model."
            )
            self.stderr.write(self.style.ERROR(error_message))
            raise

        # Initialize the description variable to
        # store the plan's description.
        description = ""

        # Check if the plan name matches predefined
        # plans and fetch their descriptions.
        if plan_name == "standard":
            description = plan_description["standard"]["default"]
        elif plan_name == "business":
            description = plan_description["business"]["default"]
        else:
            # Handle custom plan names by splitting
            # into prefix and suffix.
            try:
                # Split custom plan name by '__'.
                split_plan = plan_name.split("__")

                # Ensure the format is valid with exactly two parts.
                if len(split_plan) == 2:
                    prefix, suffix = split_plan

                    # Fetch description from plan_description dictionary.
                    description = (
                        plan_description.get(
                            prefix, {}
                        ).get(suffix, "Unknown plan")
                    )

                else:
                    # Handle invalid format cases.
                    description = "Invalid plan name format"
            except KeyError:
                # Handle cases where the plan prefix or suffix is not found.
                description = "Plan not recognized"

        # Create a new SubscriptionPlan instance in the database.
        subscription_plan, created = (
            SubscriptionPlan.objects.get_or_create(
                _type=_type,
                name=plan_name,
                defaults={
                    'description': description,
                    'default_feature': default_feature,
                    'business_feature': (
                        business_feature
                        if business_feature
                        else None
                    ),
                    'team_feature': (
                        team_feature
                        if team_feature
                        else None
                    ),
                }
            )
        )

        if created:
            # Output a success message
            self.stdout.write(
                self.style.SUCCESS(
                    f"Created {SubscriptionPlan.__name__}: "
                    f"{subscription_plan.name}"
                )
            )
        else:
            self.stdout.write(
                self.style.HTTP_INFO(
                    f"{SubscriptionPlan.__name__}: "
                    f"{subscription_plan.name}"
                )
            )

        return subscription_plan
