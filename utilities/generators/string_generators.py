import random, secrets, base64,time, hashlib

from utilities.cryptography.algorithms import AlphanumericCipher


class QueryID:
    def __init__(self, data: list = [], length: int = 80):
        self.data = data
        self.length = length
    
    def to_database(self) -> bytes:
        """
        Most database table's column's unique identifies are mostly integers incrementally starting from zero(0).
        It will be more secure to generate an identifier that is
        1) Deficult to memorise since knowing table's column's unique identifier permits you to access all other information in that row
        2) One can be able to extract important information from the unique identifier if gotten (reasons why the encoding needs to be secured).
                    Reasons being that, if the client is unable to access the database, the client with authorization to the encoding algorithm will be
                able to extract these important information without needing to access the database. So, some clients will be given authority to the decryption key
        """

        data = "-".join(self.data)

        cipher = AlphanumericCipher()

        query_id = cipher.encrypt(data)

        # convert to base64 encoded format
        return base64.b64encode(query_id.encode("utf-8"))
    
    def to_response(self, from_database: bytes) -> str:
        # Converts the bytes data from the Binary Field
        # to a string suitable to be use as a JSON data
        return from_database.decode("utf-8")
    
    def query_id(self, query_id: str) -> bytes:
        # Converts the string query id data to its corresponding byte data
        # suitable for comparison with the data in the database
        return bytes(query_id, "utf-8")
    
    def decode(self, query_id: bytes) -> str:
        # Decodes the corresponding query_id byte data
        cipher = AlphanumericCipher()

        # Will get to this later
        return
    
    def get_query_id(self, query_id: bytes) -> str:
        # Assuming that `query_id` contains the binary data
        binary_data = query_id
        if binary_data:
            # Encode the binary data to Base64
            return base64.b64encode(binary_data).decode('utf-8')
        return None


def generate_username():

    # Generate a random username by combining a random adjective and noun, with a random number at the end
    while True:
        noun = 'lalouge-user'
        number = random.randint(100000, 999999)
        username = f'{noun}{number}'
        
        if len(username) <= 18:
            break

    return username



class Keys:
    def __init__(self, user_data: list = [], _type: str = "public"):
        self.user_data = user_data
        self._type = _type

    def generate(self):
        # Combined user-specific information with a random component and timestamp
        user_specific_info = str(self.user_data)
        random_component = secrets.token_hex(16)  # 32 Characters
        timestamp = str(int(time.time()))  # Convert Current Time To String
        combined_string = user_specific_info + random_component + timestamp

        # Using A Cryptographic Hash Function To Create A Secure Hash Of The Combined String
        hashed_string = hashlib.sha256(combined_string.encode('utf-8')).digest()

        if self._type.lower() == "secret":
            return hashed_string[:32]
        
        return hashed_string[:32]

    def to_base64_string(self, value: bytes) -> str:
        return base64.b64encode(value).decode("utf-8")

    def from_base64_string(self, value: str) -> bytes:
        return base64.b64decode(value.encode("utf-8"))