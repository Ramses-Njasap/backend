from PIL import Image
import os
from skimage.metrics import structural_similarity as ssim
from skimage.metrics import peak_signal_noise_ratio as psnr
from skimage import io
import numpy as np

class ImageOptimizer:
    def __init__(self, max_size=(1920, 1080), quality=85):
        """
        Initialize the ImageOptimizer with parameters for image optimization.

        Parameters:
        - max_size: tuple, maximum width and height of the image
        - quality: int, quality of the output image (1-100, where 100 is best quality)
        """
        self.max_size = max_size
        self.quality = quality

    def optimize_image(self, input_path, output_path):
        """
        Optimize a single image and save it to the output path.

        Parameters:
        - input_path: str, path to the input image file
        - output_path: str, path to save the optimized image
        """
        with Image.open(input_path) as img:
            # Convert to RGB (required for JPEG)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize image if larger than max_size
            img.thumbnail(self.max_size, Image.LANCZOS)
            
            # Save image with optimization
            img.save(output_path, format='JPEG', quality=self.quality, optimize=True)
            
            print(f"Image optimized and saved to {output_path}")

    def batch_optimize_images(self, input_dir, output_dir):
        """
        Optimize all images in a directory.

        Parameters:
        - input_dir: str, path to the directory with images to optimize
        - output_dir: str, path to the directory where optimized images will be saved
        """
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        for filename in os.listdir(input_dir):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                input_path = os.path.join(input_dir, filename)
                output_path = os.path.join(output_dir, filename)
                self.optimize_image(input_path, output_path)
    
    def compare_images(self, image_path1, image_path2):
        # Load the images
        image1 = io.imread(image_path1, as_gray=True)  # Load as grayscale
        image2 = io.imread(image_path2, as_gray=True)  # Load as grayscale

        # Ensure both images have the same dimensions
        if image1.shape != image2.shape:
            raise ValueError("Images must have the same dimensions for comparison.")

        # Compute SSIM
        ssim_value, _ = ssim(image1, image2, full=True)
        
        # Compute PSNR
        psnr_value = psnr(image1, image2)

        return {
            'SSIM': ssim_value,
            'PSNR': psnr_value
        }


# Example usage
if __name__ == "__main__":
    optimizer = ImageOptimizer(max_size=(1920, 1080), quality=85)
    input_directory = '/home/ramses/Desktop/LaLougeBackend/LaLouge/properties/images/input'
    output_directory = '/home/ramses/Desktop/LaLougeBackend/LaLouge/properties/images/output'
    optimizer.batch_optimize_images(input_directory, output_directory)
    optimizer.compare_images('/home/ramses/Desktop/LaLougeBackend/LaLouge/properties/images/input/badimage.jpeg', '/home/ramses/Desktop/LaLougeBackend/LaLouge/properties/images/output/badimage.jpeg')
