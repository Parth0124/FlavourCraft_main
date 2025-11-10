import { useState } from 'react';
import { uploadService } from '@/lib/api/services/upload.service';
import type { IngredientDetectionResult } from '@/types/api.types';

export function useImageUpload() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<IngredientDetectionResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const uploadImage = async (file: File) => {
    setLoading(true);
    setError(null);
    try {
      const response = await uploadService.uploadImage(file);
      setResult(response);
      return response;
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Upload failed');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setResult(null);
    setError(null);
  };

  return { uploadImage, loading, result, error, reset };
}