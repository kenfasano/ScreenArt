def convert(hex_color: str) -> tuple[int, int, int]:
    """
    Converts a hexadecimal color string to an RGB tuple.

    Args:
        hex_color: A 6-digit hex color string (e.g., 'FFA500') or 7-digit
                   with a '#' prefix (e.g., '#FFA500').

    Returns:
        A tuple of three integers (R, G, B), each in the range 0-255.
    
    Raises:
        ValueError: If the input hex string is not a valid 6-digit hex color.
    """
    # Remove the '#' prefix if it exists
    if hex_color.startswith('#'):
        hex_color = hex_color[1:]

    # Check if the hex string has the correct length
    if len(hex_color) != 6:
        raise ValueError("Invalid hex color string. Must be 6 digits.")

    try:
        # Convert each 2-character hex pair to an integer
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return (r, g, b)
    except ValueError:
        # Handle cases where the string contains non-hexadecimal characters
        raise ValueError("Invalid hexadecimal characters in the color string.")

