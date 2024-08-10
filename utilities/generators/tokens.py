from django.utils import timezone
from django.conf import settings

from accounts.models.users import User
from accounts.models.devices import Device, DeviceToken, DeviceTokenBlacklist

from utilities import response

from rest_framework_simplejwt.tokens import RefreshToken, TokenError

from rest_framework import status

import datetime
import jwt, hashlib


class UserAuthToken:
    def __init__(self, user: User = None) -> tuple:
        self.user = user

    def get_token_expiration_date(self, token):

        token_exp = datetime.datetime.fromtimestamp(token.payload["exp"], tz=datetime.timezone.utc)

        return token_exp

    def get_token_pair(self):
        # Generate access and refresh tokens for the user
        refresh = RefreshToken.for_user(self.user)

        tokens = [refresh.access_token, refresh]
        
        token_exp = [self.get_token_expiration_date(token) for token in tokens]

        # Return [access tokens, refresh tokens]
        return [str(tokens[0]), token_exp[0]], [str(tokens[1]), token_exp[1]]
    
    def refresh_access_token(self, refresh_token, renew: bool = False):

        try:
            refresh = RefreshToken(refresh_token)
            
            tokens = [refresh.access_token, refresh]
        
            token_exp = [self.get_token_expiration_date(token) for token in tokens]

            # Return [access tokens, refresh tokens]
            return [str(tokens[0]), token_exp[0]], [str(tokens[1]), token_exp[1]]
        
        except TokenError as e:
            if "Token is expired" in str(e):
                if renew:
                    self.get_token_pair()
            else:
                response.errors(
                    field_error="Unable To Refresh Access Token",
                    for_developer=f"{str(e)}",
                    code="BAD_REQUEST",
                    status_code=400
                )
        except Exception as e:
            response.errors(
                field_error="Unexpected Error In Refreshing Access Token",
                for_developer=f"{str(e)}",
                code="INTERNAL_SERVER_ERROR",
                status_code=500
            )
    
    def revoke_tokens(self, refresh_token):

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception as e:
            response.errors(
                field_error="Couldn't Revoke Tokens",
                for_developer=f"Couldn't Revoke Tokens: {str(e)}",
                code="NOT_IMPLEMENTED",
                status_code=501
            )

        return not None


class DeviceAuthenticator:
    def __init__(self, secret_key=settings.DEVICE_JWT["SIGNING_KEY"], 
                 access_token_lifetime=settings.DEVICE_JWT["ACCESS_TOKEN_LIFETIME"], 
                 refresh_token_lifetime=settings.DEVICE_JWT["REFRESH_TOKEN_LIFETIME"],
                 database_actions=True, user_instance: User = None, instance: Device = None):
        
        self.secret_key = secret_key
        self.access_token_lifetime = access_token_lifetime
        self.refresh_token_lifetime = refresh_token_lifetime
        self.database_actions = database_actions
        self.user = user_instance
        self.instance = instance

    def perform_database_actions(self, access_token, refresh_token, access_token_expires_at,
                                 refresh_token_expires_at, refresh_access=False):
        
        if not refresh_access:

            try:

                max_retry = 0

                while DeviceToken.objects.filter(refresh_token=refresh_token).exists():
                    self.generate_tokens()
                    max_retry += 1

                    if max_retry == settings.APPLICATION_SETTINGS["LOOP_MAX_RETRY"]:
                        response.errors(
                            field_error="Max Retries Exceeded",
                            for_developer="Failed To Create Unique Refresh Token. Max Retries Exceeded.",
                            code="LOOP_DETECTED",
                            status_code=1011,
                            main_thread=False,
                            param=self.user.pk
                        )

                device_token_instance = DeviceToken.objects.create(access_token=access_token, refresh_token=refresh_token,
                                                                access_token_expires_at=access_token_expires_at,
                                                                refresh_token_expires_at=refresh_token_expires_at)
                
                self.instance.tokens = device_token_instance

                self.instance.save()
            
            except Exception as e:

                return f"{str(e)} {type(access_token_expires_at)}"
        
        else:
            try:
                device_token_instance = DeviceToken.objects.filter(refresh_token=refresh_token).last()
                device_token_instance.access_token = access_token
                device_token_instance.access_token_expires_at = access_token_expires_at
                device_token_instance.save()
            
            except Exception as e:
                return None
        
        self.blacklist_access_token(access_token=access_token)
        
        return not None
    
    def _for_old_device(self, access_token, refresh_token, access_token_expires_at,
                        refresh_token_expires_at):
        try:
            device_instance = Device.objects.get(pk=self.instance.pk)
        except Device.DoesNotExist:

            if self.user:
                response.errors(
                    field_error="Device Not Found",
                    for_developer=f"Device With ID {self.instance.pk} Was Not Found",
                    code="NOT_FOUND",
                    status_code=1011,
                    main_thread=False,
                    param=self.user.pk
                )
            else:
                response.errors(
                    field_error="Device Not Found",
                    for_developer=f"Device With ID {self.instance.pk} Was Not Found",
                    code="NOT_FOUND",
                    status_code=400,
                    main_thread=True
                )
        
        old_device_instance = device_instance
        
        device_token_instance = old_device_instance.tokens

        expired_since = (datetime.datetime.now() - device_token_instance.refresh_token_expires_at).days

        if expired_since <= settings.APPLICATION_SETTINGS["DEVICE_REFRESH_ACCESS_TOKEN_DELAY"]:
            old_device_instance.refresh_token_renewal_count += 1
            old_device_instance._is_trusted = True
        
        else:
            old_device_instance.refresh_token_renewal_count = 0
        
        old_device_instance.save()

        _is_database_actions_successful = self.perform_database_actions(
                                                access_token=access_token,
                                                refresh_token=refresh_token,
                                                access_token_expires_at=access_token_expires_at,
                                                refresh_token_expires_at=refresh_token_expires_at
                                            )
        
        if _is_database_actions_successful is None:
            old_device_instance.refresh_token_renewal_count = device_instance.refresh_token_renewal_count
            old_device_instance._is_trusted = device_instance._is_trusted
            old_device_instance.save()

            if self.user:
                response.errors(
                    field_error="Unable To Renew Both Device Tokens (access and refresh tokens)",
                    for_developer="An Error Occurred When Trying To Perform Database Actions On The Already Generated Tokens",
                    code="INTERNAL_SERVER_ERROR",
                    status_code=1011,
                    main_thread=False,
                    param=self.user.pk
                )
            
            else:
                response.errors(
                    field_error="Unable To Renew Both Device Tokens (access and refresh tokens)",
                    for_developer="An Error Occurred When Trying To Perform Database Actions On The Already Generated Tokens",
                    code="INTERNAL_SERVER_ERROR",
                    status_code=500,
                    main_thread=True
                )
        
        return not None
            

    def generate_tokens(self, is_old_device: bool = False):

        # Combine device ID and current timestamp for added uniqueness
        unique_identifier = f"{self.instance.pk}-{datetime.datetime.utcnow().timestamp()}"

        # Hash the unique identifier to generate a token
        token = hashlib.sha256(unique_identifier.encode()).hexdigest()

        # Calculate token expiration times
        current_time = timezone.now()
        access_token_exp = current_time + self.access_token_lifetime
        refresh_token_exp = current_time + self.refresh_token_lifetime

        # Define the payload for both access and refresh tokens
        access_payload = {
            'device_id': self.instance.pk,
            'token': token,
            'exp': access_token_exp
        }

        refresh_payload = {
            'device_id': self.instance.pk,
            'token': token,
            'exp': refresh_token_exp
        }

        # Generating both access and refresh tokens
        access_token = jwt.encode(access_payload, self.secret_key, algorithm=settings.DEVICE_JWT["ALGORITHM"])

        refresh_token = jwt.encode(refresh_payload, self.secret_key, algorithm=settings.DEVICE_JWT["ALGORITHM"])

        if is_old_device:
            _is_successful = self._for_old_device(
                                access_token=access_token,
                                refresh_token=refresh_token,
                                access_token_expires_at=access_token_exp,
                                refresh_token_expires_at=refresh_token_exp
                            )
        else:
            if self.database_actions:
                _is_successful = self.perform_database_actions(
                                    access_token=access_token,
                                    refresh_token=refresh_token,
                                    access_token_expires_at=access_token_exp,
                                    refresh_token_expires_at=refresh_token_exp
                                )

        if _is_successful:
            return [access_token, access_token_exp], [refresh_token, refresh_token_exp]

    def verify_access_token(self, access_token):
        try:
            # Decode and verify the access token
            payload = jwt.decode(access_token, self.secret_key, algorithms=[settings.DEVICE_JWT["ALGORITHM"]])
            return payload
        
        except jwt.ExpiredSignatureError as e:

            self.blacklist_access_token(access_token)

            if not self.user:
                response.errors(
                    field_error = "Device Token Expired.",
                    for_developer = f"{str(e)}. Request For New Token",
                    code = "UNAUTHORIZED",
                    status_code = 401
                )

            # Raising errors
            response.errors(
                field_error="Token Has Expired. Revoking Token ...",
                for_developer=f"{str(e)}. Request For New Token",
                code="UNAUTHORIZED",
                status_code=1011,
                main_thread=False,
                param=self.user.pk
            )

        except jwt.InvalidTokenError as e:

            if not self.user:
                response.errors(
                    field_error = "Invalid Device Token",
                    for_developer = f"{str(e)}",
                    code = "UNAUTHORIZED",
                    status_code = 401
                )

            # Raising errors
            response.errors(
                field_error="Invalid Token",
                for_developer=f"{e}",
                code="UNAUTHORIZED",
                status_code=1011,
                main_thread=False,
                param=self.user.pk
            )
        
    def blacklist_access_token(self, access_token):

        try:
            DeviceTokenBlacklist.objects.create(access_token=access_token)
        except Exception as e:
            # response.errors(
            #     field_error="Failed To Blacklist Token",
            #     for_developer=f"{e}",
            #     code="INTERNAL_SERVER_ERROR",
            #     status_code=500
            # )
            # Not Seeing A Reason Why The Entire Process Should Fail Because Token Failed To
            # Be Blacklisted
            pass

        return not None

    def revoke_token(self, refresh_token):
        # In a real system, you might want to maintain a list/database of revoked tokens
        # Here, we'll just print a message indicating token revocation
        print(f"Revoking refresh token: {refresh_token}")

    def refresh_access_token(self, refresh_token):
        try:
            # Decode and verify the refresh token
            try:
                refresh_payload = jwt.decode(refresh_token, self.secret_key, algorithms=[settings.DEVICE_JWT["ALGORITHM"]])
            except Exception as e:
                response.errors(
                    field_error="Failed To Refresh Access Token",
                    for_developer=str(e),
                    code="NOT_IMPLEMENTED",
                    status_code=1011,
                    main_thread=False,
                    param=self.user.pk
                )

            # Check if the refresh token is still valid
            if datetime.datetime.utcnow() < datetime.datetime.utcfromtimestamp(refresh_payload['exp']):
                # Revoke the used refresh token
                self.revoke_refresh_token(refresh_token)
                
                # Generate a new access token
                new_access_token_payload = {
                    'device_id': refresh_payload['device_id'],
                    'exp': datetime.datetime.utcnow() + datetime.timedelta(days=self.access_token_lifetime)
                }
                new_access_token = jwt.encode(new_access_token_payload, self.secret_key, algorithm=settings.DEVICE_JWT["ALGORITHM"])
                
                # Generate a new refresh token
                new_refresh_token_payload = {
                    'device_id': refresh_payload['device_id'],
                    'exp': datetime.datetime.utcnow() + datetime.timedelta(days=self.refresh_token_lifetime)
                }
                new_refresh_token = jwt.encode(new_refresh_token_payload, self.secret_key, algorithm=settings.DEVICE_JWT["ALGORITHM"])

                if self.database_actions:
                    self.perform_database_actions(
                        access_token=new_access_token,
                        refresh_token=new_refresh_token,
                        access_token_expires_at=new_access_token_payload["exp"],
                        refresh_token_expires_at=new_refresh_token_payload["exp"],
                        refresh_access=True
                    )

                return [new_access_token, new_access_token_payload["exp"]], [new_refresh_token, new_refresh_token_payload["exp"]]
            else:
                response.errors(
                    field_error="Failed To Refresh Access Token",
                    for_developer="Failed To Refresh Access Token: The Refresh Token Used Has Expired",
                    code="FAILED_DEPENDENCY",
                    status_code=1011,
                    main_thread=False,
                    param=self.user.pk
                )

        except jwt.InvalidTokenError as e:
            response.errors(
                field_error="Failed To Refresh Access Token",
                for_developer=str(e),
                code="INTERNAL_SERVER_ERROR",
                status_code=1011,
                main_thread=False,
                param=self.user.pk
            )

    def decode_token(self, access_token: str, get_device_instance: bool = False, ignore_exp: bool = False):
        try:
            decoded_payload = jwt.decode(access_token, self.secret_key, algorithms=['HS256'], options={"verify_exp": not ignore_exp})

            if get_device_instance:
                try:
                    device_id = int(decoded_payload['device_id'])
                except KeyError:
                    print("The token payload does not contain a 'device_id' key.")
                    return None
                except ValueError:
                    print("The 'device_id' value is not an integer.")
                    return None
                except TypeError:
                    print("The 'device_id' value is of an inappropriate type.")
                    return None
                except:
                    return None
                try:
                    device_instance = Device.objects.get(pk=device_id)
                except Device.DoesNotExist:
                    print(f"Device with id={device_id} does not exists")
                    return None
                
                except Exception as e:
                    print(str(e))
                    return None
                
                return device_instance

        except jwt.ExpiredSignatureError:
            print("Token has expired")
            return None
        except jwt.InvalidTokenError:
            print("Invalid token")
            return None
        
        return decoded_payload