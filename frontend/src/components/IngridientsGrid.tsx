import { Plus, X, FileImage, ExternalLink, ZoomIn } from "lucide-react";
import { useState, useEffect } from "react";
import type { ImageUrls } from "@/types/api.types";

interface UploadedImage {
  id: number;
  file: File;
  preview: string;
  name: string;
  cloudinaryUrls?: ImageUrls;
}

interface IngredientGridProps {
  uploadedImages: UploadedImage[];
  onRemoveImage: (id: number) => void;
  onAddMore: () => void;
}

const IngredientGrid: React.FC<IngredientGridProps> = ({
  uploadedImages,
  onRemoveImage,
  onAddMore,
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [animatedItems, setAnimatedItems] = useState<Set<number>>(new Set());
  const [lightboxImage, setLightboxImage] = useState<string | null>(null);

  // Trigger initial animation
  useEffect(() => {
    const timer = setTimeout(() => {
      setIsVisible(true);
    }, 100);
    return () => clearTimeout(timer);
  }, []);

  // Animate items in sequence
  useEffect(() => {
    if (isVisible && uploadedImages.length > 0) {
      uploadedImages.forEach((image, index) => {
        setTimeout(() => {
          setAnimatedItems(prev => new Set([...prev, image.id]));
        }, index * 150);
      });
    }
  }, [isVisible, uploadedImages]);

  // Add new items with animation
  useEffect(() => {
    const newItems = uploadedImages.filter(image => !animatedItems.has(image.id));
    newItems.forEach((image, index) => {
      setTimeout(() => {
        setAnimatedItems(prev => new Set([...prev, image.id]));
      }, index * 150);
    });
  }, [uploadedImages, animatedItems]);

  // Open image in lightbox
  const openLightbox = (imageUrl: string) => {
    console.log("📸 Opening lightbox for:", imageUrl);
    setLightboxImage(imageUrl);
  };

  // Close lightbox
  const closeLightbox = () => {
    setLightboxImage(null);
  };

  // Format file size
  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  return (
    <div className="h-full">
      {/* Header with slide-in animation */}
      <div 
        className={`flex items-center justify-between mb-6 transform transition-all duration-700 ease-out ${
          isVisible 
            ? 'translate-y-0 opacity-100' 
            : '-translate-y-4 opacity-0'
        }`}
      >
        <h3 className="text-2xl font-bold text-gray-800">
          Your Ingredients ({uploadedImages.length})
        </h3>
        <button
          onClick={onAddMore}
          className="inline-flex items-center px-4 py-2 bg-white border-2 border-orange-300 text-orange-600 rounded-xl hover:bg-orange-50 transition-all duration-200 hover:scale-105 hover:shadow-md"
        >
          <Plus className="w-4 h-4 mr-2" />
          Add More
        </button>
      </div>

      {/* Grid with attachment-style cards */}
      <div 
        className={`space-y-3 max-h-[70vh] overflow-y-auto pr-2 transform transition-all duration-500 ease-out ${
          isVisible 
            ? 'translate-y-0 opacity-100' 
            : 'translate-y-8 opacity-0'
        }`}
      >
        {uploadedImages.map((image, index) => {
          const isAnimated = animatedItems.has(image.id);
          const fullSizeUrl = image.cloudinaryUrls?.url || image.preview;
          const fileSize = formatFileSize(image.file.size);
          
          return (
            <div 
              key={image.id} 
              className={`relative group transform transition-all duration-500 ease-out ${
                isAnimated 
                  ? 'translate-y-0 opacity-100 scale-100' 
                  : 'translate-y-6 opacity-0 scale-95'
              }`}
              style={{
                transitionDelay: isAnimated ? '0ms' : `${index * 100}ms`
              }}
            >
              {/* Attachment Card - Email/Gmail style */}
              <div className="bg-white rounded-lg border-2 border-gray-200 p-4 hover:border-orange-300 hover:shadow-md transition-all duration-200">
                <div className="flex items-center gap-4">
                  {/* File Icon */}
                  <div className="flex-shrink-0">
                    <div className="w-12 h-12 bg-gradient-to-br from-orange-100 to-red-100 rounded-lg flex items-center justify-center">
                      <FileImage className="w-6 h-6 text-orange-600" />
                    </div>
                  </div>

                  {/* File Info */}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-800 truncate">
                      {image.name}
                    </p>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-xs text-gray-500">{fileSize}</span>
                      {image.cloudinaryUrls && (
                        <>
                          <span className="text-xs text-gray-300">•</span>
                          <div className="flex items-center gap-1">
                            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                            <span className="text-xs text-green-600 font-medium">Uploaded</span>
                          </div>
                        </>
                      )}
                      {!image.cloudinaryUrls && (
                        <>
                          <span className="text-xs text-gray-300">•</span>
                          <div className="flex items-center gap-1">
                            <div className="w-2 h-2 bg-yellow-500 rounded-full animate-pulse"></div>
                            <span className="text-xs text-yellow-600 font-medium">Uploading...</span>
                          </div>
                        </>
                      )}
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex items-center gap-2">
                    {/* View Button */}
                    <button
                      onClick={() => openLightbox(fullSizeUrl)}
                      className="p-2 rounded-lg bg-orange-50 text-orange-600 hover:bg-orange-100 transition-colors"
                      title="View image"
                    >
                      <ZoomIn className="w-4 h-4" />
                    </button>

                    {/* Remove Button */}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onRemoveImage(image.id);
                      }}
                      className="p-2 rounded-lg bg-red-50 text-red-600 hover:bg-red-100 transition-colors"
                      title="Remove image"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                {/* Cloudinary URL indicator (hover to show) */}
                {image.cloudinaryUrls && (
                  <div className="mt-3 pt-3 border-t border-gray-100 opacity-0 group-hover:opacity-100 transition-opacity">
                    <div className="flex items-center gap-2 text-xs text-gray-500">
                      <ExternalLink className="w-3 h-3" />
                      <span className="truncate">Stored in cloud</span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Empty state with bounce animation */}
      {uploadedImages.length === 0 && (
        <div 
          className={`flex flex-col items-center justify-center h-64 text-gray-500 transform transition-all duration-700 ease-out ${
            isVisible 
              ? 'translate-y-0 opacity-100 scale-100' 
              : 'translate-y-8 opacity-0 scale-95'
          }`}
        >
          <div className="animate-bounce mb-4">
            <div className="w-16 h-16 bg-gradient-to-r from-orange-200 to-red-200 rounded-2xl flex items-center justify-center">
              <Plus className="w-8 h-8 text-orange-600" />
            </div>
          </div>
          <p className="text-lg font-medium">No ingredients yet</p>
          <p className="text-sm mt-1">Upload some photos to get started!</p>
        </div>
      )}

      {/* Floating action hint */}
      {uploadedImages.length > 0 && (
        <div 
          className={`absolute bottom-4 right-4 transform transition-all duration-1000 ease-out ${
            isVisible 
              ? 'translate-y-0 opacity-100' 
              : 'translate-y-4 opacity-0'
          }`}
        >
          <div className="bg-gradient-to-r from-orange-400 to-red-500 text-white px-3 py-2 rounded-full text-xs font-medium shadow-lg animate-pulse">
            {uploadedImages.length} ready to cook!
          </div>
        </div>
      )}

      {/* Lightbox Modal */}
      {lightboxImage && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-90 z-50 flex items-center justify-center p-4 animate-fadeIn"
          onClick={closeLightbox}
        >
          <button
            className="absolute top-4 right-4 text-white hover:text-gray-300 transition-colors z-50"
            onClick={closeLightbox}
          >
            <X className="w-8 h-8" />
          </button>
          <div className="relative max-w-5xl max-h-[90vh]">
            <img
              src={lightboxImage}
              alt="Full size"
              className="max-w-full max-h-[90vh] object-contain rounded-lg shadow-2xl"
              onClick={(e) => e.stopPropagation()}
              onError={(e) => {
                console.error("❌ Lightbox image failed to load:", lightboxImage);
              }}
              onLoad={() => {
                console.log("✅ Lightbox image loaded:", lightboxImage);
              }}
            />
          </div>
        </div>
      )}

      {/* CSS for fadeIn animation */}
      <style>{`
        @keyframes fadeIn {
          from {
            opacity: 0;
          }
          to {
            opacity: 1;
          }
        }
        
        .animate-fadeIn {
          animation: fadeIn 0.3s ease-in-out;
        }
      `}</style>
    </div>
  );
};

export default IngredientGrid;