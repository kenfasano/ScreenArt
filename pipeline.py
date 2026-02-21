import os
import cv2 
import random 
from pathlib import Path

# Adjust the import path based on your folder structure
from .screenArt import ScreenArt 

class ImageProcessingPipeline(ScreenArt):
    def __init__(self):
        # 1. Inherit singleton config, logger, and OS detection
        super().__init__("ScreenArt")
        
        # 2. Grab paths directly from the inherited config
        self.out_dir = self.config["paths"]["transformers_out"]
        self.reject_dir = self.config["paths"]["rejected_out"]
        
        self.accepted = 0
        self.rejected = 0
        self.stats = []

    def run(self, source_dir: str, transformers: list = None):
        """Processes all images in a source directory through a list of transformers."""
        if transformers is None:
            transformers = []
            
        # Filter for valid image files
        image_files = [f for f in os.listdir(source_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        
        if not image_files:
            self.log.info(f"No images found in {source_dir} to process.")
            return

        for filename in image_files:
            input_path = os.path.join(source_dir, filename)
            
            # Read image using OpenCV
            img_np = cv2.imread(input_path)
            if img_np is None:
                self.log.error(f"Failed to read image: {input_path}")
                continue

            metadata_tags = []
            
            # Run the image through the pipeline
            for transformer in transformers:
                self.log.debug(f"Applying {transformer.__class__.__name__} to {filename}")
                
                # THE NEW STANDARD: call .run()
                img_np = transformer.run(img_np) 
                
                metadata_tags.append(transformer.get_image_metadata())

            # Construct the final filename based on the transformations
            base_name = Path(filename).stem
            joined_tags = "_".join(metadata_tags)
            
            # 1. Calculate the Grade
            grade = self._calculate_grade(img_np)
            
            # 2. Append the grade to the filename
            new_filename = f"{base_name}_{joined_tags}_Grade-{grade}.png"
            
            # 3. Route and Save
            self._evaluate_and_save(img_np, new_filename, grade)

    def _calculate_grade(self, img_np) -> str:
        """
        Analyzes the image array and returns a letter grade: A, B, C, D, or F.
        PLACEHOLDER: Replace this with your actual OpenCV math.
        """
        # For testing the routing, we randomly assign a grade
        return random.choice(['A', 'B', 'C', 'D', 'F'])

    def _evaluate_and_save(self, img_np, filename: str, grade: str):
        """Routes the image to the correct folder based on the letter grade."""
        
        # A, B, and C go to the accepted output directory
        if grade in ['A', 'B', 'C']:
            final_path = os.path.join(self.out_dir, filename)
            self.accepted += 1
            status = "ACCEPTED"
            
        # D and F go to the rejected directory
        elif grade in ['D', 'F']:
            final_path = os.path.join(self.reject_dir, filename)
            self.rejected += 1
            status = "REJECTED"
            
        else:
            self.log.error(f"Unknown grade '{grade}' generated. Defaulting to Reject.")
            final_path = os.path.join(self.reject_dir, filename)
            self.rejected += 1
            status = "REJECTED"

        # Save the file using the inherited log for output
        cv2.imwrite(final_path, img_np)
        self.log.info(f"[{status} - Grade: {grade}] Saved to: {final_path}")

    def get_performance_stats(self):
        return self.stats
