import os
from PIL import Image, ImageOps

def create_pixel_strip(image_folder=".", output_name="result.png"):
    # 1. Gather and sort all PNGs alphabetically
    valid_extensions = (".png", ".PNG")
    images = sorted([f for f in os.listdir(image_folder) if f.endswith(valid_extensions)])
    
    if not images:
        print("No PNG images found in the specified folder.")
        return

    print(f"Found {len(images)} images. Processing...")

    processed_images = []
    
    # Target sizes (excluding border)
    target_w, target_h = 60, 40
    # Pixelation factor (lower = more pixelated/blocky)
    pixel_scale = 2

    for img_name in images:
        img_path = os.path.join(image_folder, img_name)
        with Image.open(img_path) as img:
            # Ensure image is in RGB format
            img = img.convert("RGB")
            
            # --- Step 1: Apply 8-bit Pixelation Effect ---
            # Shrink down to a tiny size
            small_w = max(1, target_w // pixel_scale)
            small_h = max(1, target_h // pixel_scale)
            img_small = img.resize((small_w, small_h), resample=Image.Resampling.BILINEAR)
            
            # Scale back up using NEAREST neighbor to get blocky pixels
            img_pixelated = img_small.resize((target_w, target_h), resample=Image.Resampling.NEAREST)
            
            # --- Step 2: Add 1px Black Border ---
            # This adds 1px to all sides, turning 60x40 into 62x42
            img_with_border = ImageOps.expand(img_pixelated, border=1, fill="black")
            
            # Keep track of the final frame
            processed_images.append(img_with_border)

    # --- Step 3: Stitch Images Side-by-Side ---
    frame_w, frame_h = processed_images[0].size  # This will be 62x42
    total_width = frame_w * len(processed_images) # 62 * 48 = 2976
    total_height = frame_h                        # 42

    # Create the giant blank canvas
    strip_image = Image.new("RGB", (total_width, total_height))

    # Paste each image one after another
    for index, proc_img in enumerate(processed_images):
        x_offset = index * frame_w
        strip_image.paste(proc_img, (x_offset, 0))

    # Save the final masterpiece
    strip_image.save(output_name)
    print(f"Success! Final image saved as '{output_name}' with size {total_width}x{total_height}.")

if __name__ == "__main__":
    # Runs in the current directory by default
    create_pixel_strip()