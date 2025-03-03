import secrets


class AlphanumericCipher:
    def __init__(self):
        self.characters = (
            "abcdefghijklmnopqrstuvwxyzABCDEFG"
            "HIJKLMNOPQRSTUVWXYZ0123456789"
        )
        self.key = self.generate_key()

    def generate_key(self):
        # Generating a random permutation of alphanumeric characters using secrets
        secure_random = secrets.SystemRandom()
        key = list(self.characters)
        secure_random.shuffle(key)  # Use secure shuffle
        return dict(zip(self.characters, key))

    def encrypt(self, message):
        # Encrypt the message using the substitution cipher
        encrypted_message = ''.join([self.key.get(char, char) for char in message])
        return encrypted_message

    def decrypt(self, encrypted_message):
        # Decrypt the message using the inverse of the substitution cipher
        inverted_key = {v: k for k, v in self.key.items()}
        decrypted_message = ''.join(
            [inverted_key.get(char, char) for char in encrypted_message]
        )
        return decrypted_message
