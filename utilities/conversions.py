class String:
    def __init__(self, value: str):
        self.value = value
    
    @property
    def snake_case_lower_to_snake_case_upper(self):
        values = self.value.split("_")

        return "_".join(value.upper() for value in values)
    
    @property
    def snake_case_upper_to_snake_case_lower(self):
        values = self.value.split("_")

        return "_".join(value.lower() for value in values)