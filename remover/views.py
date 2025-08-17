from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.files.base import ContentFile
from .models import ProcessedImage
from .bg_processor import (
    remove_white_background, 
    smart_background_removal, 
    edge_based_removal,
    color_threshold_removal
)
import io
import os

def home(request):
    """Home page with upload form"""
    if request.method == 'POST' and request.FILES.get('image'):
        try:
            # Save uploaded image
            uploaded_file = request.FILES['image']
            processed_image = ProcessedImage(original_image=uploaded_file)
            processed_image.save()
            
            # Get processing method
            method = request.POST.get('method', 'smart')
            
            # Process the image based on selected method
            original_path = processed_image.original_image.path
            
            if method == 'white':
                result_img = remove_white_background(original_path)
            elif method == 'edge':
                result_img = edge_based_removal(original_path)
            elif method == 'color':
                result_img = color_threshold_removal(original_path)
            else:  # smart (default)
                result_img = smart_background_removal(original_path)
            
            # Save processed image
            img_io = io.BytesIO()
            result_img.save(img_io, format='PNG')
            img_content = ContentFile(img_io.getvalue())
            
            # Generate filename
            original_name = os.path.splitext(uploaded_file.name)[0]
            processed_filename = f"processed_{original_name}_{method}.png"
            
            processed_image.processed_image.save(
                processed_filename,
                img_content,
                save=True
            )
            
            messages.success(request, f'Background removed successfully using {method} method!')
            return redirect('result', pk=processed_image.pk)
            
        except Exception as e:
            messages.error(request, f'Error processing image: {str(e)}')
    
    # Get recent images
    recent_images = ProcessedImage.objects.filter(processed_image__isnull=False)[:6]
    
    return render(request, 'home.html', {'recent_images': recent_images})

def result(request, pk):
    """Show result"""
    processed_image = get_object_or_404(ProcessedImage, pk=pk)
    return render(request, 'result.html', {'processed_image': processed_image})

def gallery(request):
    """Gallery view"""
    images = ProcessedImage.objects.filter(processed_image__isnull=False)
    return render(request, 'gallery.html', {'images': images})