import re
from django.core.exceptions import ValidationError

def validate_password_strength(password):

    if not  re.search(r'[A-Z]',password):
        raise ValidationError('Password must contain at least one upper case letter ')
    
    if not re.search(r'[a-z]',password):
        raise ValidationError('Password must contain at least one lower case letter ') 
    
    if not re.search('[\W_]',password):
        raise ValidationError('Password must contain at least one special character') 
    
    if not re.search('[0-9]',password):
        raise ValidationError('Password must contain at least one number')     
    
    if len(password) < 8:
        raise ValidationError('Password must be at least 8 characters long')
    
    return password