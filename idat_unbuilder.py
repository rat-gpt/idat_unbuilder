import zlib
import argparse
import os
import struct
import sys

# Define the functions

def find_idat_chunks(file_data, include_magic=False):
    """
    Finds and extracts IDAT chunks and their CRC32 checksums from the binary file data.

    :param file_data: The binary data of the PNG file.
    :param include_magic: Whether to include the 'IDAT' magic bytes in the output.
    :return: A list of tuples containing (IDAT chunk data, CRC32 checksum).
    """
    # PNG files must start with an 8-byte signature
    png_signature = b'\x89PNG\r\n\x1a\n'
    if file_data[:8] != png_signature:
        print("Error: The file is not a valid PNG.")
        return []

    idat_chunks = []  # List to store extracted IDAT chunks and their CRC32 values
    idx = 8  # Start searching after the PNG header

    while idx < len(file_data):
        # Search for the IDAT marker in the binary data
        idx = file_data.find(b'IDAT', idx)
        if idx == -1:
            break  # No more IDAT chunks found

        # Read the 4 bytes before the 'IDAT' marker to get the chunk length
        length_start = idx - 4
        if length_start < 0:
            print(f"Error: Invalid IDAT chunk found at index {idx}.")
            break

        # Extract the chunk length (4 bytes, big-endian)
        length = struct.unpack('>I', file_data[length_start:idx])[0]

        # Calculate the start and end indices of the chunk data
        data_start = idx + 4  # After 'IDAT' marker
        data_end = data_start + length

        # Ensure the end index is within the file bounds
        if data_end + 4 > len(file_data):  # Include 4 bytes for the CRC32
            print(f"Error: Incomplete IDAT chunk at index {idx}.")
            break

        # Extract the chunk data and optionally include the 'IDAT' marker
        chunk_data = file_data[idx:data_end] if include_magic else file_data[data_start:data_end]

        # Extract the CRC32 bytes (4 bytes right after the chunk data)
        crc32_start = data_end
        crc32_end = crc32_start + 4
        crc32_bytes = file_data[crc32_start:crc32_end]

        # Append the IDAT chunk and its CRC32 to the list
        idat_chunks.append((chunk_data, crc32_bytes))

        # Skip over this IDAT chunk and its CRC32 for the next iteration
        idx = crc32_end  # Move past the chunk data and CRC32

    return idat_chunks


def decompress_idat_chunks(idat_chunks):
    """
    Decompresses a list of IDAT chunks using zlib.

    :param idat_chunks: A list of tuples containing (IDAT chunk data, CRC32 checksum).
    :return: Decompressed IDAT data as a bytes object.
    """
    combined_data = b''.join([chunk for chunk, crc in idat_chunks])  # Combine all IDAT chunk data
    try:
        print(f"[i] info : Total length of combined IDAT : {len(combined_data)} bytes")
        decompressed_data = zlib.decompress(combined_data)
        return decompressed_data
    except zlib.error as e:
        print(f"Error: Failed to decompress IDAT data: {e}")
        return None


def unfilter_idat_data(decompressed_data, width, bytes_per_pixel, height, verbose= False):
    """
    Unfilters the decompressed IDAT data based on the filter type for each scanline.

    :param decompressed_data: Decompressed raw IDAT data.
    :param width: The width of the image in pixels.
    :param bytes_per_pixel: The number of bytes representing a single pixel.
    :param height: The height of the image in pixels.
    :return: Unfiltered image data as a bytes object.
    """
    sys.path.append('lib')
    from unfilter_decompressed_idat import unfilter_scanlines

    print(f"[i] DEBUG: Unfiltering decompressed data with width={width}, height={height}, bytes_per_pixel={bytes_per_pixel}")
    unfiltered_data = unfilter_scanlines(decompressed_data, width, bytes_per_pixel, height, verbose)
    return unfiltered_data


def write_result_to_file(data, output_file, dirpath= '.'):
    """
    Writes the given data to a specified output file.

    :param data: Data to be written to the file.
    :param output_file: Path to the output file.
    """
    # Create the directory if it doesn't exist
    os.makedirs(dirpath, exist_ok=True)

    # Construct the full file path
    full_file_path = os.path.join(dirpath, output_file)

    with open(full_file_path, 'wb') as out_f:
        out_f.write(data)
    print(f"Data saved to '{full_file_path}'")


def get_png_ihdr_info(png_file):
    """
    Extracts the IHDR chunk information (width, height, bit depth, color type) from the PNG file.

    :param png_file: Path to the PNG file.
    :return: (width, height, bytes_per_pixel)
    """
    try:
        with open(png_file, 'rb') as file:
            # Read and check the PNG signature (first 8 bytes)
            png_signature = file.read(8)
            if png_signature != b'\x89PNG\r\n\x1a\n':
                print(f"Error: '{png_file}' is not a valid PNG file.")
                return None, None, None

            # Loop through the chunks to find the IHDR chunk
            while True:
                # Read the length (4 bytes) and type (4 bytes)
                chunk_length_data = file.read(4)
                chunk_type = file.read(4)

                if len(chunk_length_data) < 4 or len(chunk_type) < 4:
                    print("Error: Unexpected end of file.")
                    return None, None, None

                # Convert chunk length from bytes to integer
                chunk_length = struct.unpack('>I', chunk_length_data)[0]

                # Check if it's the IHDR chunk
                if chunk_type == b'IHDR':
                    print(f"[i] Found IHDR chunk at offset {file.tell() - 8}")
                    
                    # Read the IHDR chunk data (13 bytes)
                    ihdr_data = file.read(13)
                    width, height, bit_depth, color_type = struct.unpack('>IIBB', ihdr_data[:10])

                    # Calculate bytes per pixel based on bit depth and color type
                    if color_type == 0:  # Grayscale
                        bytes_per_pixel = bit_depth // 8
                    elif color_type == 2:  # RGB
                        bytes_per_pixel = (bit_depth // 8) * 3
                    elif color_type == 3:  # Indexed-color
                        bytes_per_pixel = 1
                    elif color_type == 4:  # Grayscale with alpha
                        bytes_per_pixel = (bit_depth // 8) * 2
                    elif color_type == 6:  # RGB with alpha
                        bytes_per_pixel = (bit_depth // 8) * 4
                    else:
                        print(f"Unsupported color type: {color_type}")
                        return None, None, None

                    print(f"Width: {width}, Height: {height}, Bit Depth: {bit_depth}, Color Type: {color_type}, Bytes per Pixel: {bytes_per_pixel}")
                    return width, height, bytes_per_pixel
                
                # Skip the chunk data and the CRC (chunk length + 4 bytes for CRC)
                file.seek(chunk_length + 4, 1)

    except FileNotFoundError:
        print(f"Error: File '{png_file}' not found.")
    except Exception as e:
        print(f"Error processing PNG file: {e}")
    
    return None, None, None


def main():
    # Set up argument parsing
    parser = argparse.ArgumentParser(
        description="Decompress IDAT chunks from a PNG file and optionally unfilter the decompressed data.",
        epilog="Example usage:\n"
               "  python png_process.py input.png --extract-idat\n"
               "  python png_process.py input.png --extract-idat --decompress --unfilter -v",
        formatter_class=argparse.RawTextHelpFormatter
    )

    # Positional argument for the input PNG file
    parser.add_argument("file", help="The path to the input PNG file.")

    # Optional argument to extract and save IDAT chunks
    parser.add_argument("--extract-idat", action='store_true', help="Extract IDAT chunks and their CRC32 checksums.")

    # Optional argument for saving decompressed data to file
    parser.add_argument("--decompress", action='store_true', help="Save decompressed data to file.")

    # Optional argument for unfiltering the decompressed data
    parser.add_argument("--unfilter", action='store_true', help="Unfilter the decompressed data using dimensions from the provided PNG file.")

    # Optional argument for verbosity
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose mode')

    # Parse the arguments
    args = parser.parse_args()

    # Step 1: Read the PNG file and extract IDAT chunks
    try:
        with open(args.file, 'rb') as f:
            file_data = f.read()
    except FileNotFoundError:
        print(f"Error: File '{args.file}' not found.")
        return

    # Step x: Create directory for artifacts
    artifacts_dir= f"_{args.file.split('.')[0]}"
    os.makedirs(artifacts_dir, exist_ok=True)

    # Step 2: Extract IDAT chunks and CRC32 checksums
    idat_chunks = find_idat_chunks(file_data)
    if args.extract_idat:
        chunks_subdir = os.path.join(artifacts_dir, f"_idat_chunks")
        os.makedirs(chunks_subdir, exist_ok=True)
        for i, (chunk_data, crc32_bytes) in enumerate(idat_chunks):
            idat_output_file = os.path.join(chunks_subdir, f"idat_chunk_{i + 1:03d}.bin")
            crc32_output_file = os.path.join(chunks_subdir, f"idat_chunk_{i + 1:03d}_crc32.bin")
            write_result_to_file(b"IDAT" + chunk_data, idat_output_file)
            write_result_to_file(crc32_bytes, crc32_output_file)

    # Step 3: Decompress the IDAT chunks
    decompressed_data = decompress_idat_chunks(idat_chunks)
    if decompressed_data is None:
        print("Error: Decompression failed. Exiting.")
        return

    # Step y: Save the decompressed data to the specified output file
    if args.decompress:
        decompressed_output_file= f"idat_uncompressed.bin"
        write_result_to_file(decompressed_data, decompressed_output_file, artifacts_dir)

    # Step 4: Extract width, height, and bytes_per_pixel from the PNG file for unfiltering
    width, height, bytes_per_pixel = get_png_ihdr_info(args.file)
    if width is None or height is None or bytes_per_pixel is None:
        print("Error: Failed to extract IHDR information from the PNG file. Exiting.")
        return

    # Step 5: If unfiltering is required, perform unfiltering
    if args.unfilter:
        unfiltered_data = unfilter_idat_data(decompressed_data, width, bytes_per_pixel, height, args.verbose)

        # Save the unfiltered data to a new file with "_unfiltered" suffix
        unfiltered_output_file = f"idat_unfiltered.bin"
        write_result_to_file(unfiltered_data, unfiltered_output_file, artifacts_dir)


if __name__ == "__main__":
    main()

