"""
MLM User = MultiLevel Marketing User

***MLM USER DEFINITION***
            A user who decides to become a multi level marketing user has the privilege to sell on behalf
        other users or companies thereby receiving commission from each sale they make.

            They also have the privilege to have commission from every new user in the pyramid system.

***THE PYRAMID SYSTEM***
            Multilevel marketing users can invite a maximum of two users. These new users (if they also decide
        to become multilevel marketing users) have the privilege to invite a maximum of two other users
        and so on and so forth thereby creating a Pyramid structure of users.

***THE PYRAMID STRUCTURE***
            As the Pyramid grows, the commission reduces till in reaches 0. When a user no longer gain subscription plan
        commission from his/her Pyramid system, that pyramid system ceases to grow thereby limiting the user to gain
        only from the existing pyramid system user based on sales of properties only.

        __Visit file__ `LaLouge/examples/mlm_pyramid_scheme.png`

"""


from collections.abc import Iterable
from django.db import models
from decimal import Decimal, ROUND_DOWN
from django.db.models import Sum, F

from accounts.models.users import User

from utilities.generators.string_generators import QueryID

import random, string, uuid


class MLMUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, db_index=True)

    # Referral code to use during login for potential downliners
    referral_code = models.CharField(max_length=255, unique=True, db_index=True)

    # MLM User position in the Pyramid distribution
    level = models.PositiveIntegerField(default=1)

    # Money generated as a multi level marketing user
    amount_generated = models.BinaryField()

    # ManyToMany relationship for child users
    children = models.ManyToManyField('self', through='MLMRelationship', 
                                      symmetrical=False, related_name='parents')

    def __str__(self):
        return self.user.username

    def calculate_recruiter_commission(self, amount: Decimal = Decimal('0.00'), recruiter: User = None) -> Decimal:
        # Calculate the commission for the recruiter
        commission_percentage = recruiter.subscription_plan.new_user_commission_percentage
        
        commission = Decimal((amount/100)*commission_percentage)

        return Decimal(commission)

    def recruit(self, new_user: User = None):
        # Method to add a new recruit efficiently
        new_mlm_user = MLMUser(user=new_user, level=0)  # Set the new user's level to zero
        new_mlm_user.save()

        if new_user.subscription_duration == new_user.SubscriptionDuration.MONTHLY:
            subscription_price = Decimal(new_user.subscription_plan.monthly_price)
        
        elif new_user.subscription_duration == new_user.SubscriptionDuration.YEARLY:
            subscription_price = Decimal(new_user.subscription_plan.yearly_price)

        else:
            subscription_price = Decimal('0.00')

        commission = self.calculate_recruiter_commission(subscription_price, self.user)
        self.balance += commission
        self.level += 1
        # self.balance += commission

        # Track the earnings for each user above the new user
        above_users_mlm = MLMUser.objects.filter(children=new_mlm_user).order_by('level')

        for above_user_mlm in above_users_mlm:
            commission = self.calculate_recruiter_commission(commission, above_user_mlm.user)

            above_user_mlm.balance += commission
            above_user_mlm.level += 1

            # Check if the earning is almost zero (rounded down)
            if above_user_mlm.balance.quantize(Decimal('1.00'), rounding=ROUND_DOWN) == Decimal('100.00'):
                break  # Stop increasing levels and commissions for users earning close to zero

        # Bulk update all users' balances and levels
        above_users_mlm.update(balance=F('balance'), level=F('level'))

        self.save()

    @property
    def can_invite(self):
        # Check if the user can invite more children
        return self.children.count() < 2

    @property
    def calculate_earnings(self):
        # Method to calculate earnings efficiently
        total_earnings = MLMUser.objects.filter(parents=self).aggregate(
            total_earnings=Sum(F('balance') + 10.00, output_field=models.DecimalField())
        )['total_earnings'] or 0.00
        return total_earnings
    
    def generate_unique_referral_code(self):
        characters = string.ascii_uppercase + string.digits
        while True:
            new_code = ''.join(random.choice(characters) for _ in range(8))
            if not MLMUser.objects.filter(referral_code=new_code).exists():
                return new_code

    def save(self, *args, **kwargs):
        # Generate a unique referral code
        if not self.referral_code:
            self.referral_code = self.generate_unique_referral_code()

        super().save(*args, **kwargs)


class MLMRelationship(models.Model):
    parent = models.ForeignKey(MLMUser, on_delete=models.CASCADE, related_name='parent_relationships')
    child = models.ForeignKey(MLMUser, on_delete=models.CASCADE, related_name='child_relationships')
    created_at = models.DateTimeField(auto_now_add=True)


class MLMConfig(models.Model):
    level = models.PositiveIntegerField(unique=True)
    commission_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    qualification_sales = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Level {self.level}"


class MLMUserConfig(models.Model):
    user = models.OneToOneField(MLMUser, on_delete=models.CASCADE)
    config = models.ForeignKey(MLMConfig, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user} - {self.config}"


class MLMAchievement(models.Model):
    user = models.ForeignKey(MLMUser, on_delete=models.CASCADE)
    achievement_name = models.CharField(max_length=255)
    achieved_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.achievement_name}"