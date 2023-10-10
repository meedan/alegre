import json
import datetime

def safe_serializer(obj):
    """
    Serialize datetime objects into string format.
    
    Args:
    - obj (object): The object to be serialized
    
    Returns:
    - str: The string representation of the datetime object
    """
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")
