import re


class Validate:
    def __init__(self, value: str):
        self.value = value

    @property
    def phone(self) -> bool:
        # Checking if the value matches a phone number pattern
        return bool(re.match(r'^\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}$', self.value))

    @property
    def email(self) -> bool:
        # Checking if the value matches an email pattern
        return bool(re.match(r'^[\w+\-.]+@[a-zA-Z\d\-]+(\.[a-zA-Z\d\-]+)*\.[a-zA-Z]+$', self.value))