#-----
# idat_unbuilder.py
#

usage: idat_unbuilder.py [-h] [--extract-idat] [--decompress] [--unfilter]
                         [-v]
                         file

Decompress IDAT chunks from a PNG file and optionally unfilter the decompressed data.

positional arguments:
  file            The path to the input PNG file.

options:
  -h, --help      show this help message and exit
  --extract-idat  Extract IDAT chunks and their CRC32 checksums.
  --decompress    Save decompressed data to file.
  --unfilter      Unfilter the decompressed data using dimensions from the provided PNG file.
  -v, --verbose   Enable verbose mode

Example usage:
  python png_process.py input.png --extract-idat
  python png_process.py input.png --extract-idat --decompress --unfilter -v


#-----
# crc32.py
#

usage: crc32.py [-h] file {standard,reversed,custom} [custom_polynomial]

Calculate the CRC32 checksum of a binary file using standard, reversed, or custom polynomial.

positional arguments:
  file                  The path to the binary file to calculate the CRC32 checksum for.
  {standard,reversed,custom}
                        The polynomial type to use: 'standard', 'reversed', or 'custom'.
  custom_polynomial     The custom polynomial to use, specified as a hexadecimal value (e.g., 0x1EDC6F41). This is required only if 'polynomial_type' is set to 'custom'.

options:
  -h, --help            show this help message and exit

Example usage:
  python crc32_calculator.py file.bin standard
  python crc32_calculator.py file.bin reversed
  python crc32_calculator.py file.bin custom 0x82F63B78

