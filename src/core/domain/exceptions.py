class GarmentNotFoundError(Exception):
    """Raised when a garment with a specific ID is not found."""
    pass

class DuplicateGarmentError(Exception):
    """Raised when trying to create a garment that already exists."""
    pass