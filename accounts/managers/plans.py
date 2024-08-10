from django.db import models

from utilities import response


class SubscriptionPlanManager(models.Manager):
    def filter(self, auto: bool = True, *args, **kwargs) -> models.QuerySet:

        if not auto:
            return super().filter(*args, **kwargs)
        
        instances = super().filter(*args, **kwargs)

        if not instances.exists():
            # setting error messages for user and developer respectively
            field_message = "Not Found"
            for_developer = "Query Returned None"
            
            # Raising error responses
            response.errors(field_error=field_message, for_developer=for_developer, code="NOT_FOUND", status_code=404)
        
        return instances
    
    def filter_active_plans(self, auto: bool = True, *args, **kwargs) -> models.QuerySet:
        if not auto:
            return self.filter(auto=False, *args, **kwargs, is_active=True)
        
        return self.filter(*args, **kwargs, is_active=True)
    
    def filter_inactive_plans(self, auto: bool = True, *args, **kwargs) -> models.QuerySet:
        if not auto:
            return self.filter(auto=False, *args, **kwargs, is_active=False)
        
        return self.filter(*args, **kwargs, is_active=False)
    
    def get(self, auto: bool = True, *args, **kwargs) -> models.Model:

        if not auto:
            return super().get(*args, **kwargs)
        
        try:

            instance = super().get(*args, **kwargs)

        except self.model.DoesNotExist:
            # setting error messages for user and developer respectively
            field_message = "Not Found"
            for_developer = "Query Returned None"
            
            # Raising error responses
            response.errors(field_error=field_message, for_developer=for_developer, code="NOT_FOUND", status_code=404)

        except self.model.MultipleObjectsReturned:
            field_message = "Multiple Instances Was Returned"

            filtered_data = super().filter(*args, **kwargs)
            for_developer = f"Multiple {self.model.__name__} Instances Match The Given Query Parameters. Try Using .filter*** And You'll Get These Instances: {str(filtered_data)}"
            
            # Raising error responses
            response.errors(field_error=field_message, for_developer=for_developer, code="BAD_REQUEST", status_code=400)

        except models.FieldError as e:
            
            field_message = "Invalid Query Parameters"
            for_developer = f"Invalid Query Parameters: {str(e)}"
            
            # Raising error responses
            response.errors(field_error=field_message, for_developer=for_developer, code="BAD_REQUEST", status_code=400)

        except TypeError as e:

            field_message = "Type Error. Check Your Input Data Type"
            for_developer = f"Invalid Data Type: {str(e)}"
            
            # Raising error responses
            response.errors(field_error=field_message, for_developer=for_developer, code="BAD_REQUEST", status_code=400)

        return instance
    
    def get_active_plan(self, auto: bool = True, *args, **kwargs) -> models.Model:
        if not auto:
            return self.get(auto=False, *args, **kwargs, is_active=True)
        
        return self.get(*args, **kwargs, is_active=True)
    
    def get_inactive_plan(self, auto: bool = True, *args, **kwargs) -> models.Model:
        if not auto:
            return self.get(auto=False, *args, **kwargs, is_active=False)
        
        return self.get(*args, **kwargs, is_active=False)