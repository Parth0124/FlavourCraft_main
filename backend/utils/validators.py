"""
Input validation utilities
"""
import re
import os
from typing import List
from fastapi import UploadFile
import magic


def validate_email(email: str) -> bool:
    """
    Validate email format
    
    Args:
        email: Email string to validate
        
    Returns:
        True if valid email format
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_username(username: str) -> bool:
    """
    Validate username format
    - 3-50 characters
    - Alphanumeric and underscores only
    
    Args:
        username: Username string to validate
        
    Returns:
        True if valid username format
    """
    if len(username) < 3 or len(username) > 50:
        return False
    pattern = r'^[a-zA-Z0-9_]+$'
    return bool(re.match(pattern, username))


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password strength
    Requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    
    Args:
        password: Password string to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    
    return True, ""


async def validate_image_file(file: UploadFile) -> tuple[bool, str]:
    """
    Validate uploaded image file
    - Check file size
    - Check file extension
    - Check actual file type (MIME)
    
    Args:
        file: Uploaded file object
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Read credentials directly from environment variables
    max_upload_size = int(os.getenv('MAX_UPLOAD_SIZE', '10485760'))  # 10MB default
    allowed_extensions = os.getenv('ALLOWED_EXTENSIONS', 'jpg,jpeg,png,webp')
    allowed_extensions_list = [ext.strip() for ext in allowed_extensions.split(',')]
    
    # Check file size
    content = await file.read()
    file_size = len(content)
    await file.seek(0)  # Reset file pointer
    
    if file_size > max_upload_size:
        max_mb = max_upload_size / (1024 * 1024)
        return False, f"File size exceeds maximum allowed size of {max_mb}MB"
    
    # Check file extension
    if not file.filename:
        return False, "No filename provided"
    
    file_ext = file.filename.split('.')[-1].lower()
    if file_ext not in allowed_extensions_list:
        return False, f"File type .{file_ext} not allowed. Allowed types: {allowed_extensions}"
    
    # Check actual file type using magic
    try:
        mime_type = magic.from_buffer(content, mime=True)
        allowed_mimes = ['image/jpeg', 'image/png', 'image/webp']
        
        if mime_type not in allowed_mimes:
            return False, f"Invalid file type. File appears to be {mime_type}"
    except Exception as e:
        return False, f"Error validating file type: {str(e)}"
    
    return True, ""


def validate_ingredients(ingredients: List[str]) -> List[str]:
    """
    Validate and clean ingredient list
    - Remove empty strings
    - Strip whitespace
    - Remove duplicates
    - Limit length
    
    Args:
        ingredients: List of ingredient strings
        
    Returns:
        Cleaned list of ingredients
    """
    # Clean and filter
    cleaned = []
    seen = set()
    
    for ingredient in ingredients:
        # Strip whitespace and convert to lowercase for comparison
        cleaned_ingredient = ingredient.strip()
        ingredient_lower = cleaned_ingredient.lower()
        
        # Skip empty strings and duplicates
        if cleaned_ingredient and ingredient_lower not in seen:
            cleaned.append(cleaned_ingredient)
            seen.add(ingredient_lower)
    
    return cleaned


def validate_recipe_format(recipe_data: dict) -> tuple[bool, str]:
    """
    Validate recipe data format
    
    Args:
        recipe_data: Dictionary containing recipe data
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    required_fields = ['title', 'steps', 'estimated_time', 'difficulty']
    
    for field in required_fields:
        if field not in recipe_data:
            return False, f"Missing required field: {field}"
    
    if not isinstance(recipe_data['steps'], list) or len(recipe_data['steps']) < 3:
        return False, "Recipe must have at least 3 steps"
    
    if recipe_data['difficulty'] not in ['easy', 'medium', 'hard']:
        return False, "Difficulty must be 'easy', 'medium', or 'hard'"
    
    if not isinstance(recipe_data['estimated_time'], int) or recipe_data['estimated_time'] <= 0:
        return False, "Estimated time must be a positive integer"
    
    return True, ""


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent directory traversal and other issues
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove any directory components
    filename = filename.split('/')[-1].split('\\')[-1]
    
    # Remove any non-alphanumeric characters except dots, dashes, and underscores
    filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    
    return filename