import logging
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model
from ldap3 import Server, Connection, ALL, NTLM

# Set up logger
logger = logging.getLogger(__name__)

class CustomLDAPBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None):
        if not username or not password:
            logger.warning("No username or password provided.")
            print("No username or password provided.")
            return None

        # Retrieve LDAP servers from settings
        from django.conf import settings
        ldap_servers = settings.LDAP_SERVERS

        # Attempt to authenticate against each server
        for server_config in ldap_servers:
            logger.info(f"Attempting to authenticate {username} on {server_config['URI']}")
            print(f"Attempting to authenticate {username} on {server_config['URI']}")
            
            user = self._authenticate_with_ldap(
                server_config['URI'],
                server_config['USER_DN_TEMPLATE'].format(user=username),
                password
            )
            if user:
                logger.info(f"Successfully authenticated {username} on {server_config['URI']}")
                print(f"Successfully authenticated {username} on {server_config['URI']}")
                return user
            else:
                logger.warning(f"Authentication failed for {username} on {server_config['URI']}")
                print(f"Authentication failed for {username} on {server_config['URI']}")

        # If all LDAP attempts fail, log and return None
        logger.error(f"All LDAP authentication attempts failed for {username}.")
        print(f"All LDAP authentication attempts failed for {username}.")
        return None

    def _authenticate_with_ldap(self, server_uri, user_dn, password):
        try:
            # Determine the domain for NTLM
            if "@johnsonelectric.com" in user_dn:
                domain = "JEHLI"  # Replace with the correct domain for this server
            elif "@stackpole.ca" in user_dn:
                domain = "STACKPOLE"  # Replace with the correct domain for this server
            else:
                domain = ""  # Default or handle unexpected cases

            ntlm_user = f"{domain}\\{user_dn.split('@')[0]}"  # DOMAIN\username

            logger.info(f"Connecting to LDAP server {server_uri} with user {ntlm_user}")
            print(f"Connecting to LDAP server {server_uri} with user {ntlm_user}")

            # Connect to the LDAP server
            server = Server(server_uri, get_info=ALL)
            conn = Connection(
                server,
                user=ntlm_user,
                password=password,
                authentication=NTLM,
                auto_bind=True
            )

            if conn.bound:
                logger.info(f"Connection established and user authenticated: {ntlm_user}")
                print(f"Connection established and user authenticated: {ntlm_user}")
                return self._get_or_create_user(user_dn.split("@")[0])  # Extract username
            else:
                logger.warning(f"Failed to bind connection for {ntlm_user} on {server_uri}")
                print(f"Failed to bind connection for {ntlm_user} on {server_uri}")

        except Exception as e:
            logger.error(f"LDAP authentication failed for {user_dn} on {server_uri}: {str(e)}")
            print(f"LDAP authentication failed for {user_dn} on {server_uri}: {str(e)}")

        return None

    def _get_or_create_user(self, username):
        User = get_user_model()
        try:
            logger.info(f"Looking up user {username} in Django database.")
            print(f"Looking up user {username} in Django database.")
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            logger.info(f"User {username} not found in database. Creating new user.")
            print(f"User {username} not found in database. Creating new user.")
            user = User.objects.create_user(username=username)
            # Automatically grant staff status to LDAP users
            user.is_staff = True
            user.save()
        return user


    def get_user(self, user_id):
        User = get_user_model()
        try:
            logger.info(f"Fetching user with ID {user_id} from Django database.")
            print(f"Fetching user with ID {user_id} from Django database.")
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            logger.warning(f"User with ID {user_id} not found in database.")
            print(f"User with ID {user_id} not found in database.")
            return None
