from django.db import models
from django.utils import timezone

class ProcessedImage(models.Model):
    original_image = models.ImageField(upload_to='original/')
    processed_image = models.ImageField(upload_to='processed/', null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"ProcessedImage {self.id} - {self.created_at}"
    
    class Meta:
        ordering = ['-created_at']