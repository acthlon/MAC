from django.contrib.auth.backends import BaseBackend

from accounts.models import CustomUser


class EmailClassBackend(BaseBackend):


    def authenticate(self,request,email=None,password=None,**kwargs):

        try:
            user = CustomUser.objects.get(email=email,is_active = True)

            if user.check_password(password):
                return user
            
        except CustomUser.DoesNotExist:
            return None    

            
        