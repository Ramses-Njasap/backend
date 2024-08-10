from django.apps import apps
from django.db import models

class ModelRelationshipChecker:
    @staticmethod
    def get_relationship_info(model, target_model, relationship_type=None) -> tuple:

        for field in model._meta.get_fields():
            if not relationship_type or isinstance(field, relationship_type):
                if field.remote_field.model == target_model:
                    return True, field.name, type(field).__name__
                
        return False, None, None

    @classmethod
    def check_relationship(cls, target_model_name, potential_relationship_model_name, app_label, relationship_type=None) -> tuple:

        # Get the model classes from the app
        target_model = apps.get_model(app_label=app_label, model_name=target_model_name)
        potential_relationship_model = apps.get_model(app_label=app_label, model_name=potential_relationship_model_name)

        # Check if the potential_relationship_model has a relationship with target_model
        has_relationship, field_name, actual_relationship_type = cls.get_relationship_info(
            potential_relationship_model, target_model, relationship_type
        )

        return has_relationship, field_name, actual_relationship_type

# # Example usage:
# app_label = 'your_app_label'
# target_model_name = 'PhoneNumberVerificationOTP'
# potential_relationship_model_name = 'UsedOTP'

# # Check if the potential_relationship_model has a relationship with target_model (any type)
# checker = ModelRelationshipChecker()
# has_relationship, field_name, relationship_type = checker.check_relationship(
#     target_model_name, potential_relationship_model_name, app_label
# )

# if has_relationship:
#     print(f"{potential_relationship_model_name} has a {relationship_type} relationship with {target_model_name} (Field Name: {field_name})")
# else:
#     print(f"{potential_relationship_model_name} does not have a relationship with {target_model_name}")
