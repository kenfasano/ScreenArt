import numpy as np # type: ignore
from PIL import Image # type: ignore
from skimage.color import rgb2hsv # type: ignore
from multiprocessing import Pool
from functools import partial
import time
from typing import Optional, List, TextIO
import sys # Import sys for stderr
import argparse # <-- Import argparse

# --- Constants ---
NUM_CORES: int = 4
NUM_HUE_BUCKETS: int = 12  # 12 buckets, 30 degrees each (0-360)

# Define saturation/value thresholds to filter out grayscale-like pixels
# Pixels below these thresholds will not be counted in hue buckets
SATURATION_THRESHOLD: float = 0.1
VALUE_THRESHOLD: float = 0.1

# --- Removed hardcoded paths ---

def write(f: TextIO, s: str): 
    print(s)
    f.write(f"{s}\n")

def process_chunk(rgb_chunk: np.ndarray, num_buckets: int) -> np.ndarray:
    """
    Worker function to be run on each core.
    Converts a chunk of an image to HSV and computes its hue histogram.
    """
    try:
        # 1. Convert the RGB chunk (float 0-1) to HSV
        # hsv_chunk.shape will be (height_chunk, width, 3)
        hsv_chunk: np.ndarray = rgb2hsv(rgb_chunk)

        # 2. Separate the H, S, and V channels
        hue: np.ndarray = hsv_chunk[..., 0]        # Hue (0.0 to 1.0)
        saturation: np.ndarray = hsv_chunk[..., 1] # Saturation (0.0 to 1.0)
        value: np.ndarray = hsv_chunk[..., 2]      # Value (0.0 to 1.0)

        # 3. Create a mask to find "chromatic" (non-grayscale) pixels
        # We only care about the hue of pixels that actually have color
        mask: np.ndarray = (saturation > SATURATION_THRESHOLD) & (value > VALUE_THRESHOLD)

        # 4. Get only the hues of the pixels that pass the mask
        chromatic_hues: np.ndarray = hue[mask]

        if chromatic_hues.size == 0:
            # This chunk is entirely grayscale/black/white
            return np.zeros(num_buckets, dtype=np.int64)

        # 5. Define the edges for our 12 buckets
        bins: np.ndarray = np.linspace(0.0, 1.0, num_buckets + 1)

        # 6. Use numpy.histogram to efficiently count pixels in each bucket
        hist: np.ndarray
        _: np.ndarray
        hist, _ = np.histogram(chromatic_hues, bins=bins)

        return hist.astype(np.int64)
    
    except Exception as e:
        # Cannot write to file 'f' from a child process.
        # Print to stderr instead.
        print(f"Error processing chunk: {e}", file=sys.stderr)
        return np.zeros(num_buckets, dtype=np.int64)

# --- Updated function signature to accept 'f' ---
def analyze_image_hues(image_path: str, num_cores: int, num_buckets: int, f: TextIO) -> Optional[np.ndarray]:
    """
    Main function to load, split, and process an image in parallel.
    """
    try:
        image_path = f"/Users/kenfasano/Library/Mobile Documents/com~apple~CloudDocs/Scripts/ScreenArt/Images/TransformedImages/{image_path}"
        # 1. Load Image and convert to NumPy array
        with Image.open(image_path).convert('RGB') as img:
            # Convert to numpy array and normalize to float [0.0, 1.0]
            image_data: np.ndarray = np.array(img).astype(np.float32) / 255.0
            
            if image_data.size == 0:
                write(f, "Error: Image data is empty.")
                return None
        
        # --- Use the provided image_path directly ---
        write(f, f"\nImage loaded: {image_path}:\n{image_data.shape[1]}x{image_data.shape[0]} pixels")

        # 2. Split the image data into chunks for each core
        chunks: List[np.ndarray] = np.array_split(image_data, num_cores, axis=0)
        write(f, f"Image split into {len(chunks)} chunks for {num_cores} cores.")

        # Use functools.partial to create a version of our worker function
        # that already has the 'num_buckets' argument filled in.
        worker_func = partial(process_chunk, num_buckets=num_buckets)

        # 3. Create the multiprocessing Pool
        write(f, "Starting multiprocessing pool...")
        start_time: float = time.time()
        
        results: List[np.ndarray]
        with Pool(processes=num_cores) as pool:
            # pool.map applies the worker_func to each item in 'chunks'
            # and returns a list of the results [hist1, hist2, hist3, hist4]
            results = pool.map(worker_func, chunks)

        end_time: float = time.time()
        write(f, f"Processing finished in {end_time - start_time:.4f} seconds.")

        # 4. Aggregate the results
        # Sum the histograms from all chunks to get the total
        total_histogram: np.ndarray = np.sum(results, axis=0)

        return total_histogram

    except FileNotFoundError:
        write(f, f"Error: File not found at {image_path}")
        return None
    except Exception as e:
        write(f, f"An error occurred: {e}")
        return None

def main():
    # --- Set up argparse ---
    parser = argparse.ArgumentParser(
        description="Analyze hue distributions in one or more images."
    )
    
    # --- Add positional argument for image files (one or more) ---
    parser.add_argument(
        'image_files', 
        nargs='+',  # This accepts one or more arguments
        help="One or more paths to image files to analyze."
    )
    
    # --- Add optional argument for the output file ---
    parser.add_argument(
        '-o', '--output',
        default='analyze_hues.txt', # Default to a local file
        help="Path to the output log file. (Default: analyze_hues.txt)"
    )
    
    args = parser.parse_args()
    
    # --- Use the parsed arguments ---
    with open(args.output, "w") as f:
        
        # --- Iterate over the files from the command line ---
        for image_file in args.image_files:
            
            # --- Pass 'f' as an argument ---
            histogram: Optional[np.ndarray] = analyze_image_hues(
                image_file, NUM_CORES, NUM_HUE_BUCKETS, f
            )

            if histogram is not None:
                write(f, "\n--- Hue Bucket Analysis Results ---")
                
                # Get the total number of *chromatic* pixels counted
                total_chromatic_pixels: np.int64 = np.sum(histogram)
                
                if total_chromatic_pixels == 0:
                    write(f, "Image appears to be entirely grayscale, black, or white.")
                else:
                    # Define hue labels for writeing
                    hue_labels: List[str] = [
                        "Red/Pink", "Orange", "Yellow", "Chartreuse", "Green",
                        "Spring Green", "Cyan", "Azure", "Blue", "Violet",
                        "Magenta", "Rose"
                    ]

                    write(f, f"Total chromatic pixels (non-gray) found: {total_chromatic_pixels}")
                    write(f, "\nPixel distribution by hue bucket:")

                    # Calculate and write percentages
                    percentages: np.ndarray = (histogram / total_chromatic_pixels) * 100.0
                    
                    for i in range(NUM_HUE_BUCKETS):
                        write(f, f"  - {hue_labels[i]:<14}: {histogram[i]:>10} pixels ({percentages[i]:.2f}%)")

                    # --- Example Rejection Logic ---
                    write(f, "\n--- Rejection Test ---")
                    
                    REJECTION_THRESHOLD_PERCENT: float = 90.0
                    
                    # --- Test 1: Check for any SINGLE bucket over the threshold ---
                    max_percentage: np.float64 = np.max(percentages)
                    max_bucket_index: np.int64 = np.argmax(percentages)
                    
                    is_monochromatic: bool = False
                    rejection_reason: str = ""

                    if max_percentage > REJECTION_THRESHOLD_PERCENT:
                        is_monochromatic = True
                        rejection_reason = (
                            f"{max_percentage:.2f}% of colorful pixels are in one hue bucket "
                            f"({hue_labels[max_bucket_index]})."
                        )
                    
                    # --- Test 2: Check for ADJACENT buckets over the threshold ---
                    if not is_monochromatic:
                        # We check all adjacent pairs (i) and (i+1)
                        for i in range(NUM_HUE_BUCKETS):
                            # Get the index of the next bucket, wrapping around
                            # (e.g., if i=11, next_i=0)
                            next_i = (i + 1) % NUM_HUE_BUCKETS 
                            
                            adjacent_sum_percent = percentages[i] + percentages[next_i]
                            
                            if adjacent_sum_percent > REJECTION_THRESHOLD_PERCENT:
                                is_monochromatic = True
                                rejection_reason = (
                                    f"{adjacent_sum_percent:.2f}% of colorful pixels are in two adjacent "
                                    f"hue buckets ({hue_labels[i]} and {hue_labels[next_i]})."
                                )
                                # Found a match, no need to keep checking
                                break
                    
                    # --- Final Verdict ---
                    if is_monochromatic:
                        write(f, "REJECT: Image is monochromatic.")
                        write(f, f"Reason: {rejection_reason}")
                    else:
                        write(f, "ACCEPT: Image is sufficiently colorful.")
                        write(f, f"Reason: No single or adjacent pair of hue buckets exceeds the "
                              f"{REJECTION_THRESHOLD_PERCENT}% threshold.")
                        write(f, f"(Most dominant bucket: {hue_labels[max_bucket_index]} at {max_percentage:.2f}%)")

# --- Main execution ---
if __name__ == "__main__":
    main()
