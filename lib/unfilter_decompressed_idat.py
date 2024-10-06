def unfilter_scanlines(decompressed_data, width, bytes_per_pixel, height, verbose= False):
    """
    Unfilters the scanlines of a decompressed PNG data based on their filter type.

    :param decompressed_data: The decompressed raw data of the PNG file.
    :param width: The width of the image in pixels.
    :param bytes_per_pixel: The number of bytes representing a single pixel.
    :param height: The height of the image (number of scanlines).
    :return: The reconstructed image data after unfiltering.
    """
    stride = width * bytes_per_pixel  # Number of bytes in a scanline without the filter byte
    index = 0  # Position in the decompressed data
    reconstructed_image = bytearray()  # To hold the final unfiltered image data

    # Loop through each scanline
    for scanline_number in range(height):
        # Get the filter type (first byte of the scanline)
        filter_type = decompressed_data[index]
        index += 1  # Move past the filter byte

        # Get the scanline data (excluding the filter type)
        scanline_data = decompressed_data[index:index + stride]
        index += stride  # Move past the scanline data

        # Display the filter type for the current scanline if verbose= True
        if verbose:
            print(f"Scanline {scanline_number}: Filter Type = {filter_type}")

        # Unfilter the scanline based on the filter type
        if filter_type == 0:  # None
            reconstructed_scanline = scanline_data
        elif filter_type == 1:  # Sub
            reconstructed_scanline = unfilter_sub(scanline_data, bytes_per_pixel)
        elif filter_type == 2:  # Up
            prev_scanline = reconstructed_image[-stride:] if reconstructed_image else None
            reconstructed_scanline = unfilter_up(scanline_data, prev_scanline)
        elif filter_type == 3:  # Average
            prev_scanline = reconstructed_image[-stride:] if reconstructed_image else None
            reconstructed_scanline = unfilter_average(scanline_data, prev_scanline, bytes_per_pixel)
        elif filter_type == 4:  # Paeth
            prev_scanline = reconstructed_image[-stride:] if reconstructed_image else None
            reconstructed_scanline = unfilter_paeth(scanline_data, prev_scanline, bytes_per_pixel)
        else:
            raise ValueError(f"Unknown filter type: {filter_type}")

        # Add the reconstructed scanline to the image data
        reconstructed_image.extend(reconstructed_scanline)

    return reconstructed_image


# Helper functions to handle each filter type
def unfilter_sub(scanline, bytes_per_pixel):
    result = bytearray()
    for i in range(len(scanline)):
        if i < bytes_per_pixel:
            result.append(scanline[i])  # No left byte, so it's the same
        else:
            result.append((scanline[i] + result[i - bytes_per_pixel]) % 256)
    return result

def unfilter_up(scanline, prev_scanline):
    if not prev_scanline:
        return scanline  # No previous scanline, so it's the same
    return bytearray((scanline[i] + prev_scanline[i]) % 256 for i in range(len(scanline)))

def unfilter_average(scanline, prev_scanline, bytes_per_pixel):
    result = bytearray()
    for i in range(len(scanline)):
        left = result[i - bytes_per_pixel] if i >= bytes_per_pixel else 0
        up = prev_scanline[i] if prev_scanline else 0
        result.append((scanline[i] + (left + up) // 2) % 256)
    return result

def unfilter_paeth(scanline, prev_scanline, bytes_per_pixel):
    def paeth_predictor(a, b, c):
        # a = left, b = above, c = upper-left
        p = a + b - c
        pa = abs(p - a)
        pb = abs(p - b)
        pc = abs(p - c)
        if pa <= pb and pa <= pc:
            return a
        elif pb <= pc:
            return b
        else:
            return c

    result = bytearray()
    for i in range(len(scanline)):
        left = result[i - bytes_per_pixel] if i >= bytes_per_pixel else 0
        up = prev_scanline[i] if prev_scanline else 0
        upper_left = prev_scanline[i - bytes_per_pixel] if prev_scanline and i >= bytes_per_pixel else 0
        result.append((scanline[i] + paeth_predictor(left, up, upper_left)) % 256)
    return result

