import re
from typing import List, Optional

def validate_password(password: str) -> tuple[bool, Optional[List[str]]]:
    """
    Validate password against defined rules
    
    Password Rules:
    - At least 8 characters long
    - Contains at least one uppercase letter
    - Contains at least one lowercase letter
    - Contains at least one digit
    - Contains at least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)
    
    Returns:
        tuple: (is_valid, list_of_error_messages)
    """
    errors = []
    
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")

    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter")

    if not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter")

    if not re.search(r'\d', password):
        errors.append("Password must contain at least one number")

    if not re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', password):
        errors.append("Password must contain at least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)")

    is_valid = len(errors) == 0
    return is_valid, errors if not is_valid else None
