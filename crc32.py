import argparse
import zlib
import sys

def calculate_crc32_standard(data, polynomial=0x04C11DB7, initial_value=0xFFFFFFFF):
    """Calculates CRC32 using the standard polynomial (forward bit order)."""
    crc = initial_value
    for byte in data:
        crc ^= byte << 24  # Place the byte in the leftmost position of the 32-bit CRC
        for _ in range(8):
            if crc & 0x80000000:  # Check the leftmost bit
                crc = (crc << 1) ^ polynomial
            else:
                crc <<= 1
        crc &= 0xFFFFFFFF  # Ensure CRC remains 32-bit
    return crc ^ initial_value

def calculate_crc32_reversed(data, polynomial=0xEDB88320, initial_value=0xFFFFFFFF):
    """Calculates CRC32 using the reversed polynomial (zlib, PNG, ZIP)."""
    crc = initial_value
    for byte in data:
        crc ^= byte  # XOR byte into the rightmost position
        for _ in range(8):
            if crc & 1:  # Check the rightmost bit
                crc = (crc >> 1) ^ polynomial
            else:
                crc >>= 1
    return crc ^ initial_value

def main():
    # Set up argument parsing
    parser = argparse.ArgumentParser(
        description="Calculate the CRC32 checksum of a binary file using standard, reversed, or custom polynomial.",
        epilog="Example usage:\n"
               "  python crc32_calculator.py file.bin standard\n"
               "  python crc32_calculator.py file.bin reversed\n"
               "  python crc32_calculator.py file.bin custom 0x82F63B78\n",
        formatter_class=argparse.RawTextHelpFormatter
    )

    # Positional arguments
    parser.add_argument("file", help="The path to the binary file to calculate the CRC32 checksum for.")
    parser.add_argument("polynomial_type", choices=["standard", "reversed", "custom"],
                        help="The polynomial type to use: 'standard', 'reversed', or 'custom'.")

    # Optional argument for custom polynomial (required if polynomial_type is 'custom')
    parser.add_argument("custom_polynomial", nargs="?", default=None,
                        help="The custom polynomial to use, specified as a hexadecimal value (e.g., 0x1EDC6F41). "
                             "This is required only if 'polynomial_type' is set to 'custom'.")

    # Parse the arguments
    args = parser.parse_args()

    # Read the file content
    try:
        with open(args.file, 'rb') as f:
            data = f.read()
    except FileNotFoundError:
        print(f"Error: File '{args.file}' not found.")
        sys.exit(1)

    # Determine the CRC32 calculation method based on the polynomial type
    if args.polynomial_type == "standard":
        crc = calculate_crc32_standard(data)
        print(f"CRC32 (Standard Polynomial 0x04C11DB7) for '{args.file}': {crc:08x}")

    elif args.polynomial_type == "reversed":
        crc = calculate_crc32_reversed(data)
        print(f"CRC32 (Reversed Polynomial 0xEDB88320) for '{args.file}': {crc:08x}")

    elif args.polynomial_type == "custom":
        if not args.custom_polynomial:
            print("Error: Custom polynomial value is required when using 'custom' polynomial type.")
            sys.exit(1)

        # Convert the custom polynomial from hex string to integer
        try:
            custom_polynomial = int(args.custom_polynomial, 16)
        except ValueError:
            print(f"Error: '{args.custom_polynomial}' is not a valid hexadecimal polynomial.")
            sys.exit(1)

        # Calculate CRC32 using the custom polynomial (reversed bit order)
        crc = calculate_crc32_reversed(data, polynomial=custom_polynomial)
        print(f"CRC32 (Custom Polynomial {args.custom_polynomial}) for '{args.file}': {crc:08x}")
    else:
        print(f"Error: Unknown polynomial type '{args.polynomial_type}'.")
        sys.exit(1)

if __name__ == "__main__":
    main()

