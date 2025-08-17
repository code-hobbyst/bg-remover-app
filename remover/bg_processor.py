from PIL import Image, ImageFilter, ImageEnhance, ImageOps
import numpy as np

def advanced_background_removal(image_path):
    """
    Advanced background removal using multiple techniques
    """
    try:
        # Open and prepare image
        img = Image.open(image_path)
        original = img.convert("RGBA")
        
        # Method 1: GrabCut-like algorithm simulation
        result1 = grabcut_simulation(img)
        
        # Method 2: Advanced color clustering
        result2 = color_clustering_removal(img)
        
        # Method 3: Edge-based segmentation
        result3 = advanced_edge_segmentation(img)
        
        # Combine results (take the best parts from each)
        final_result = combine_results([result1, result2, result3], original)
        
        return final_result
        
    except Exception as e:
        print(f"Error in advanced removal: {e}")
        return smart_background_removal_v2(image_path)

def grabcut_simulation(img):
    """
    Simulate GrabCut algorithm behavior
    """
    img_array = np.array(img)
    height, width = img_array.shape[:2]
    
    # Create initial mask - assume center region is foreground
    mask = np.zeros((height, width), dtype=np.uint8)
    
    # Define probable foreground (center region)
    center_x, center_y = width // 2, height // 2
    margin_x, margin_y = width // 4, height // 4
    
    mask[center_y-margin_y:center_y+margin_y, 
         center_x-margin_x:center_x+margin_x] = 255
    
    # Expand mask based on color similarity
    center_color = img_array[center_y, center_x]
    
    for y in range(height):
        for x in range(width):
            pixel_color = img_array[y, x]
            color_diff = np.sqrt(np.sum((pixel_color[:3] - center_color[:3]) ** 2))
            
            if color_diff < 50:  # Similar to center
                mask[y, x] = 255
    
    # Apply morphological operations
    mask_img = Image.fromarray(mask)
    mask_img = mask_img.filter(ImageFilter.MedianFilter(size=3))
    
    # Convert back to RGBA
    result = Image.new('RGBA', img.size, (0, 0, 0, 0))
    img_rgba = img.convert('RGBA')
    
    for x in range(width):
        for y in range(height):
            if mask_img.getpixel((x, y)) > 128:
                result.putpixel((x, y), img_rgba.getpixel((x, y)))
    
    return result

def color_clustering_removal(img):
    """
    Advanced color clustering for background removal
    """
    img_array = np.array(img.convert('RGB'))
    height, width = img_array.shape[:2]
    
    # Sample edge pixels for background colors
    edge_pixels = []
    
    # Top and bottom edges
    edge_pixels.extend(img_array[0, :].tolist())
    edge_pixels.extend(img_array[-1, :].tolist())
    
    # Left and right edges
    edge_pixels.extend(img_array[:, 0].tolist())
    edge_pixels.extend(img_array[:, -1].tolist())
    
    # Find dominant background color using simple clustering
    edge_pixels = np.array(edge_pixels)
    
    # Simple k-means like clustering
    bg_color = np.mean(edge_pixels, axis=0)
    
    # Create mask based on distance to background color
    mask = np.zeros((height, width), dtype=np.uint8)
    
    for y in range(height):
        for x in range(width):
            pixel = img_array[y, x]
            distance = np.sqrt(np.sum((pixel - bg_color) ** 2))
            
            # Adaptive threshold based on position
            edge_distance = min(x, y, width-x-1, height-y-1)
            threshold = 60 + (edge_distance * 0.5)  # Higher threshold for center pixels
            
            if distance > threshold:
                mask[y, x] = 255
    
    # Smooth the mask
    mask_img = Image.fromarray(mask)
    mask_img = mask_img.filter(ImageFilter.GaussianBlur(radius=2))
    
    # Apply mask
    result = Image.new('RGBA', img.size, (0, 0, 0, 0))
    img_rgba = img.convert('RGBA')
    
    for x in range(width):
        for y in range(height):
            if mask_img.getpixel((x, y)) > 100:
                result.putpixel((x, y), img_rgba.getpixel((x, y)))
    
    return result

def advanced_edge_segmentation(img):
    """
    Advanced edge-based segmentation
    """
    # Convert to grayscale and enhance
    gray = img.convert('L')
    
    # Multiple edge detection approaches
    edges1 = gray.filter(ImageFilter.FIND_EDGES)
    
    # Enhance contrast before edge detection
    enhancer = ImageEnhance.Contrast(gray)
    enhanced = enhancer.enhance(2.0)
    edges2 = enhanced.filter(ImageFilter.EDGE_ENHANCE_MORE)
    
    # Combine edge maps
    edges_combined = Image.blend(edges1, edges2, 0.5)
    
    # Create distance transform simulation
    mask = create_distance_mask(edges_combined)
    
    # Apply mask to original
    result = Image.new('RGBA', img.size, (0, 0, 0, 0))
    img_rgba = img.convert('RGBA')
    
    for x in range(img.width):
        for y in range(img.height):
            if mask.getpixel((x, y)) > 128:
                result.putpixel((x, y), img_rgba.getpixel((x, y)))
    
    return result

def create_distance_mask(edges):
    """
    Create a mask based on distance from edges
    """
    width, height = edges.size
    mask = Image.new('L', (width, height), 0)
    
    # Find edge pixels
    edge_pixels = []
    for x in range(width):
        for y in range(height):
            if edges.getpixel((x, y)) > 50:
                edge_pixels.append((x, y))
    
    # For each pixel, find distance to nearest edge
    for x in range(width):
        for y in range(height):
            min_distance = float('inf')
            
            for ex, ey in edge_pixels[:100]:  # Limit for performance
                distance = ((x - ex) ** 2 + (y - ey) ** 2) ** 0.5
                min_distance = min(min_distance, distance)
            
            # Convert distance to mask value
            if min_distance < 20:
                mask_value = 255
            elif min_distance < 50:
                mask_value = int(255 * (50 - min_distance) / 30)
            else:
                mask_value = 0
            
            mask.putpixel((x, y), mask_value)
    
    return mask

def combine_results(results, original):
    """
    Combine multiple background removal results
    """
    width, height = original.size
    final_result = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    
    for x in range(width):
        for y in range(height):
            # Vote-based combination
            votes = 0
            pixel_sum = [0, 0, 0, 0]
            
            for result in results:
                pixel = result.getpixel((x, y))
                if pixel[3] > 0:  # If not transparent
                    votes += 1
                    for i in range(4):
                        pixel_sum[i] += pixel[i]
            
            if votes >= 2:  # Majority vote
                final_pixel = tuple(pixel_sum[i] // votes for i in range(4))
                final_result.putpixel((x, y), final_pixel)
    
    return final_result

def smart_background_removal_v2(image_path):
    """
    Improved smart background removal
    """
    try:
        img = Image.open(image_path)
        img = img.convert("RGBA")
        
        width, height = img.size
        
        # Sample more points for better background detection
        sample_points = []
        
        # Sample border pixels more densely
        border_width = min(width, height) // 20
        
        for i in range(0, width, max(1, width//50)):
            for j in range(border_width):
                sample_points.append(img.getpixel((i, j)))  # Top
                sample_points.append(img.getpixel((i, height-1-j)))  # Bottom
        
        for i in range(0, height, max(1, height//50)):
            for j in range(border_width):
                sample_points.append(img.getpixel((j, i)))  # Left
                sample_points.append(img.getpixel((width-1-j, i)))  # Right
        
        # Find most common background color
        from collections import Counter
        color_counts = Counter(sample_points)
        bg_color = color_counts.most_common(1)[0][0]
        
        # Create mask with adaptive threshold
        data = img.getdata()
        new_data = []
        
        center_x, center_y = width // 2, height // 2
        
        for i, item in enumerate(data):
            x = i % width
            y = i // width
            
            # Distance from center (for adaptive threshold)
            center_distance = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
            max_distance = ((width/2) ** 2 + (height/2) ** 2) ** 0.5
            
            # Adaptive tolerance (higher for edges, lower for center)
            base_tolerance = 30
            distance_factor = center_distance / max_distance
            tolerance = base_tolerance + (distance_factor * 40)
            
            # Color distance
            color_distance = (
                (item[0] - bg_color[0]) ** 2 +
                (item[1] - bg_color[1]) ** 2 +
                (item[2] - bg_color[2]) ** 2
            ) ** 0.5
            
            if color_distance < tolerance:
                new_data.append((255, 255, 255, 0))  # Transparent
            else:
                new_data.append(item)
        
        img.putdata(new_data)
        
        # Post-process: remove small isolated regions
        img = remove_small_regions(img)
        
        return img
        
    except Exception as e:
        print(f"Error: {e}")
        original = Image.open(image_path)
        return original.convert('RGBA')

def remove_small_regions(img):
    """
    Remove small isolated regions
    """
    # Convert to binary mask
    mask = Image.new('L', img.size, 0)
    
    for x in range(img.width):
        for y in range(img.height):
            if img.getpixel((x, y))[3] > 0:
                mask.putpixel((x, y), 255)
    
    # Apply morphological operations
    mask = mask.filter(ImageFilter.MedianFilter(size=3))
    
    # Apply back to image
    result = Image.new('RGBA', img.size, (0, 0, 0, 0))
    
    for x in range(img.width):
        for y in range(img.height):
            if mask.getpixel((x, y)) > 128:
                result.putpixel((x, y), img.getpixel((x, y)))
    
    return result

# Keep the original functions for compatibility
def remove_white_background(image_path):
    return smart_background_removal_v2(image_path)

def smart_background_removal(image_path):
    return advanced_background_removal(image_path)

def edge_based_removal(image_path):
    return advanced_edge_segmentation(Image.open(image_path))

def color_threshold_removal(image_path):
    return color_clustering_removal(Image.open(image_path))