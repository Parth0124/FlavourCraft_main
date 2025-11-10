import { useState } from 'react';
import { uploadService } from '../lib/api/services/upload.service';
import type { 
  IngredientDetectionResult, 
  MultiUploadResult,
  ImageUrls 
} from '../types/api.types';

export function useImageUpload() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<IngredientDetectionResult | null>(null);
  const [multiResult, setMultiResult] = useState<MultiUploadResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);

  /**
   * Upload a single image
   * Returns detected ingredients and Cloudinary image URLs
   */
  const uploadImage = async (file: File): Promise<IngredientDetectionResult> => {
    setLoading(true);
    setError(null);
    setUploadProgress(0);
    
    try {
      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => Math.min(prev + 10, 90));
      }, 200);

      const response = await uploadService.uploadImage(file);
      
      clearInterval(progressInterval);
      setUploadProgress(100);
      setResult(response);
      
      return response;
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Upload failed');
      throw err;
    } finally {
      setLoading(false);
      setTimeout(() => setUploadProgress(0), 1000);
    }
  };

  /**
   * Upload multiple images
   * Returns combined ingredients and array of image URLs
   */
  const uploadMultipleImages = async (files: File[]): Promise<MultiUploadResult> => {
    setLoading(true);
    setError(null);
    setUploadProgress(0);
    
    try {
      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => Math.min(prev + 10, 90));
      }, 300);

      const response = await uploadService.uploadMultipleImages(files);
      
      clearInterval(progressInterval);
      setUploadProgress(100);
      setMultiResult(response);
      
      return response;
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Multi-upload failed');
      throw err;
    } finally {
      setLoading(false);
      setTimeout(() => setUploadProgress(0), 1000);
    }
  };

  /**
   * Verify and correct detected ingredients
   * This helps improve AI accuracy
   */
  const verifyIngredients = async (
    originalIngredients: string[],
    verifiedIngredients: string[],
    addedIngredients: string[] = [],
    removedIngredients: string[] = []
  ) => {
    try {
      const response = await uploadService.verifyIngredients({
        original_ingredients: originalIngredients,
        verified_ingredients: verifiedIngredients,
        added_ingredients: addedIngredients,
        removed_ingredients: removedIngredients
      });
      return response;
    } catch (err: any) {
      console.error('Verification failed:', err);
      throw err;
    }
  };

  /**
   * Get image URLs from result
   */
  const getImageUrls = (): ImageUrls | null => {
    return result?.image_urls || null;
  };

  /**
   * Get all image URLs from multi-upload
   */
  const getAllImageUrls = (): ImageUrls[] => {
    return multiResult?.image_urls_list || [];
  };

  /**
   * Reset all state
   */
  const reset = () => {
    setResult(null);
    setMultiResult(null);
    setError(null);
    setUploadProgress(0);
  };

  return { 
    uploadImage, 
    uploadMultipleImages,
    verifyIngredients,
    getImageUrls,
    getAllImageUrls,
    loading, 
    result, 
    multiResult,
    error, 
    uploadProgress,
    reset 
  };
}