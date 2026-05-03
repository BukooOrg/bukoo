'use client';

import useEmblaCarousel from 'embla-carousel-react';
import React, { useState, useEffect, useCallback } from 'react';

import { useProductImages, useSelectedVariant } from '@/components/products/variant-selector';
import { Badge } from '@/components/ui/data-display/badge';

export function MobileGallerySlider({ product }) {
  const selectedVariant = useSelectedVariant(product);
  const images = useProductImages(product, selectedVariant?.selectedOptions);

  const [emblaRef, emblaApi] = useEmblaCarousel({
    align: 'start',
    dragFree: false,
    loop: false,
  });
  const [selectedIndex, setSelectedIndex] = useState(0);

  const onInit = useCallback(() => {
    // Initialize carousel
  }, []);
  const onSelect = useCallback((emblaApi) => {
    setSelectedIndex(emblaApi.selectedScrollSnap());
  }, []);

  useEffect(() => {
    if (!emblaApi) return;

    onInit();
    onSelect(emblaApi);
    emblaApi.on('reInit', onInit);
    emblaApi.on('select', onSelect);
  }, [emblaApi, onInit, onSelect]);

  const totalImages = images.length;

  if (totalImages === 0) return null;

  return (
    <div className='relative w-full h-full'>
      {/* Embla Carousel */}
      <div className='h-full overflow-hidden' ref={emblaRef}>
        <div className='flex h-full'>
          {images.map((image) => (
            <div
              key={`${image.url}-${image.selectedOptions
                ?.map((o) => `${o.name},${o.value}`)
                .join('-')}`}
              className='relative flex-shrink-0 w-full h-full'>
              <img
                style={{
                  aspectRatio: `${image.width} / ${image.height}`,
                }}
                src={image.url}
                alt={image.altText || ''}
                width={image.width}
                height={image.height}
                className='object-cover w-full h-full'
              />
            </div>
          ))}
        </div>
      </div>

      {/* Counter Badge */}
      {totalImages > 1 && (
        <div className='absolute z-10 transform -translate-x-1/2 bottom-4 left-1/2'>
          <Badge variant='outline-secondary'>
            {selectedIndex + 1}/{totalImages}
          </Badge>
        </div>
      )}
    </div>
  );
}
