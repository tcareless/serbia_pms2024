from django.contrib.auth.backends import ModelBackend
from django_auth_ldap.backend import LDAPBackend
from django.contrib.auth import get_user_model  # Correct import for User model
import traceback

class CustomLDAPBackend:
    def authenticate(self, request, username=None, password=None):
        print(f"ldap1 req. [request]: user-name={username}")

        # First, try the Active Directory LDAP
        try:
            ldap_backend = LDAPBackend()
            ldap_backend.settings_prefix = 'AUTH_LDAP_'
            user = ldap_backend.authenticate(request, username, password)
            if user:
                return user
            else:
                print(f"ldap1 no user. user=({user})")
        except Exception as e:
            print(f"ldap1 failed. Exception: {str(e)}")
            print(traceback.format_exc())  # This will print the full stack trace

        # If the first LDAP server fails, try the second one
        try:
            print(f"ldap2 user-name={username}")
            ldap_backend2 = LDAPBackend()
            ldap_backend2.settings_prefix = 'AUTH_LDAP2_'
            user = ldap_backend2.authenticate(request, username, password)
            if user:
                return user
        except Exception as e:
            print(f"ldap2 failed. Exception: {str(e)}")
            print(traceback.format_exc())  # This will print the full stack trace

        # Finally, fall back to the default database authentication
        return ModelBackend().authenticate(request, username, password)

    def get_user(self, user_id):
        User = get_user_model()
        print(f"modelbknd userid= {user_id}. User={User}")
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
