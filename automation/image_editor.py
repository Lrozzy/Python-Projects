from PIL import Image, ImageEnhance, ImageFilter
import os

# Correctly join paths (works in Windows, not Unix)
path = r"C:\Users\leoro\OneDrive\Coding Practice\python_projects\automation\imgs"
pathOut = r"C:\Users\leoro\OneDrive\Coding Practice\python_projects\automation\editedImgs"  

# Create the output directory if it doesn't exist
os.makedirs(pathOut, exist_ok=True)
os.makedirs(path, exist_ok=True)

for filename in os.listdir(path):
    # Full path to the image file
    full_path = os.path.join(path, filename)
    
    # Skip directories
    if os.path.isdir(full_path):
        continue
    
    try:
        # Open the image file
        img = Image.open(full_path)
        
        # Apply filters and rotate
        edit = img.filter(ImageFilter.SHARPEN).convert('L').rotate(90)  # Convert to grayscale and rotate
        
        # Enhance contrast
        factor = 1.5
        enhancer = ImageEnhance.Contrast(edit)
        edit = enhancer.enhance(factor)
        
        # Construct output filename
        clean_name = os.path.splitext(filename)[0]
        output_path = os.path.join(pathOut, f'{clean_name}_edited.jpg')
        
        # Save the edited image
        edit.save(output_path)
        
        
    except IOError:
        print(f"Cannot open {filename}")
print(f"Edited {len(os.listdir(pathOut))} image(s). Saved to {pathOut}")