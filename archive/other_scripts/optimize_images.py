import os
import sys
from pathlib import Path
from PIL import Image
from concurrent.futures import ThreadPoolExecutor
import shutil

def convert_to_webp(source):
    """Convert image to WebP format."""
    destination = source.with_suffix(".webp")
    
    # Skip if already converted
    if destination.exists():
        return f"Skipped (already exists): {source.name}"
    
    try:
        # Open and convert image
        image = Image.open(source)
        
        # Convert to RGB if necessary (for PNG with transparency)
        if image.mode in ('RGBA', 'LA'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[-1])
            image = background
        
        # Save as WebP with quality 80 (good balance between quality and size)
        image.save(destination, 'webp', quality=80, method=6)
        
        # Get size difference
        original_size = os.path.getsize(source)
        new_size = os.path.getsize(destination)
        saved = ((original_size - new_size) / original_size) * 100
        
        return f"Converted: {source.name} ({saved:.1f}% smaller)"
    except Exception as e:
        return f"Error converting {source.name}: {str(e)}"

def optimize_png_jpg(source):
    """Optimize PNG and JPG images."""
    try:
        # Get original size
        original_size = os.path.getsize(source)
        
        # Open and re-save with optimization
        img = Image.open(source)
        
        # For PNG with transparency
        if img.mode in ('RGBA', 'LA'):
            # Create a white background
            background = Image.new('RGB', img.size, (255, 255, 255))
            # Paste the image on the background, using the alpha channel as mask
            background.paste(img, mask=img.split()[-1])
            img = background
            
        # For JPG, use a higher quality setting
        quality = 85 if source.suffix.lower() in ('.jpg', '.jpeg') else 80
        
        # Save with optimization
        img.save(
            source, 
            optimize=True, 
            quality=quality,
            progressive=True  # For JPGs
        )
        
        # Get new size
        new_size = os.path.getsize(source)
        saved = ((original_size - new_size) / original_size) * 100
        
        return f"Optimized: {source.name} ({saved:.1f}% smaller)"
    except Exception as e:
        return f"Error optimizing {source.name}: {str(e)}"

def process_image(file_path):
    """Process a single image file."""
    try:
        # Skip already processed files
        if file_path.suffix.lower() == '.webp' or file_path.name.startswith('.'):
            return f"Skipped: {file_path.name} (already processed or hidden)"
            
        # Skip if it's not an image
        if file_path.suffix.lower() not in ('.png', '.jpg', '.jpeg'):
            return f"Skipped: {file_path.name} (not a supported image)"
        
        # For PNG and JPG, first optimize the original
        if file_path.suffix.lower() in ('.png', '.jpg', '.jpeg'):
            result = optimize_png_jpg(file_path)
            
            # Then create a WebP version
            webp_result = convert_to_webp(file_path)
            return f"{result}\n{webp_result}"
            
        return f"Skipped: {file_path.name} (unsupported format)"
    except Exception as e:
        return f"Error processing {file_path.name}: {str(e)}"

def find_images(directory):
    """Find all image files in the directory and its subdirectories."""
    image_extensions = ('.png', '.jpg', '.jpeg', '.webp')
    images = []
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(image_extensions):
                images.append(Path(root) / file)
    
    return images

def main():
    if len(sys.argv) < 2:
        print("Usage: python optimize_images.py <directory>")
        sys.exit(1)
    
    directory = Path(sys.argv[1])
    if not directory.exists() or not directory.is_dir():
        print(f"Error: Directory '{directory}' does not exist")
        sys.exit(1)
    
    print(f"🔍 Searching for images in {directory}...")
    images = find_images(directory)
    
    if not images:
        print("No images found to optimize.")
        return
    
    print(f"🖼️  Found {len(images)} images to process...")
    print("🔄 Optimizing images (this may take a while)...\n")
    
    # Process images in parallel for better performance
    with ThreadPoolExecutor() as executor:
        results = list(executor.map(process_image, images))
    
    # Print results
    for result in results:
        for line in str(result).split('\n'):
            if line.strip():
                print(f"  {line}")
    
    print("\n✨ Image optimization complete!")
    print("💡 Tip: Update your HTML to use .webp images with fallbacks")
    print("      Example: <picture><source srcset='image.webp' type='image/webp'><img src='image.jpg' alt='...'></picture>")

if __name__ == "__main__":
    main()
