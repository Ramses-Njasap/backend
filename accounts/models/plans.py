from django.db import models
from decimal import Decimal

from accounts.models.users import User

from accounts.managers.plans import SubscriptionPlanManager


class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=25)
    description = models.TextField()
    
    is_active = models.BooleanField(default=False)

    price = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)

    # features

    # storage space is in Mb
    storage_space = models.DecimalField(default=1024.00, max_digits=10, decimal_places=2)

    # consultation hours in minutes default = 120 minutes = 2 hours
    consultation_hours = models.DecimalField(default=120.00, max_digits=10, decimal_places=2)

    # Commission given to LaLouge from the sale of user's property
    sale_deduction = models.DecimalField(default=10.00, max_digits=10, decimal_places=2)
    # Commission given to LaLouge from the rentage of user's property
    rental_deduction = models.DecimalField(default=10.00, max_digits=10, decimal_places=2)

    # Commission given to User from LaLouge Remaining Commission
    sales_commission = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)
    rental_commission = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)

    new_user_commission = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)

    objects = SubscriptionPlanManager()

    def __str__(self) -> str:
        return self.name
    
    # Duration is in months
    @property
    def get_price(self) -> Decimal:
        return f"{round(self.price, 2)} XAF"
    
    @property
    def get_storage_space(self) -> Decimal:
        return f"{round(self.storage_space/1024, 2)} GB"
    
    @property
    def get_consultation_hours(self) -> Decimal:
        return f"{round(self.consultation_hours/60, 2)} Hours"
    
    @property
    def get_sale_deduction(self) -> Decimal:
        return f"{round(self.sale_deduction, 2)} %"
    
    @property
    def get_rental_deduction(self) -> Decimal:
        return f"{round(self.rental_deduction, 2)} %"
    
    @property
    def get_sale_commission(self) -> Decimal:
        return f"{round(self.sales_commission, 2)} %"
    
    @property
    def get_rental_commission(self) -> Decimal:
        return f"{round(self.rental_commission, 2)} %"
    
    @property
    def get_new_user_commission(self) -> Decimal:
        return f"{round(self.new_user_commission, 2)} %"
    
    @classmethod
    def get_active_plan(cls, auto: bool = True, *args, **kwargs) -> models.Model:

        manager = cls.objects

        if not auto:
            return manager.get_active_plan(auto=False, *args, **kwargs)
        
        return manager.get_active_plan(*args, **kwargs)


class CustomPlan(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name
    

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
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True)
    duration = models.CharField(max_length=9, choices=SubscriptionDuration.choices,
                                             default=SubscriptionDuration.MONTHLY)
    duration_period = models.PositiveSmallIntegerField(default=1)
    custom_plans = models.ManyToManyField('CustomPlan')

    # getting duration in terms of MONTHLY or YEARLY
    @property
    def formatted_duration(self):
        duration = self.duration_period
        time_unit = self.TIME_UNITS.get(self.duration, 'invalid duration')
        return f'{duration} {time_unit}S' if duration > 1 else f'1 {time_unit}'
    
    # This needs to be work on intensively
    @property
    def total_price(self):

        # Calculate the total price based on the plan's base price and selected custom features
        if self.duration == self.SubscriptionDuration.MONTHLY:
            base_price = self.plan.price * self.duration_period
            
        elif self.duration == self.SubscriptionDuration.YEARLY:
            base_price = self.plan.price * self.duration_period

        else:
            base_price = Decimal('0.00')

        custom_plan_prices = self.custom_plans.aggregate(
            total_price=models.Sum('price')
        )['total_price'] or 0

        price = base_price + custom_plan_prices

        return price
    
    # This also needs to be worked on
    @property
    def formatted_price(self):
        plan_instance = SubscriptionPlan.objects.get(pk=self.plan.pk)

        # Access the associated SubscriptionPlan
        subscription_plan = plan_instance.price

        # Call the formatted_price property on the SubscriptionPlan
        formatted_price = subscription_plan.formatted_price(subscription_plan)
        return formatted_price