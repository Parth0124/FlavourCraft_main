import { api } from '../client';
import type { IngredientDetectionResult } from '../../../types/api.types';

export const uploadService = {
  async uploadImage(file: File): Promise<IngredientDetectionResult> {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post('/upload/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  async uploadMultipleImages(files: File[]) {
    const formData = new FormData();
    files.forEach(file => formData.append('files', file));
    
    const response = await api.post('/upload/multi', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  async verifyIngredients(data: {
    original_ingredients: string[];
    verified_ingredients: string[];
    added_ingredients?: string[];
    removed_ingredients?: string[];
  }) {
    const response = await api.post('/upload/verify', data);
    return response.data;
  }
};