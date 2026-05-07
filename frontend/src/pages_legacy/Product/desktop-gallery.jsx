'use client';

import { useProductImages, useSelectedVariant } from '@/components/products/VariantSelector';

export const DesktopGallery = ({ product }) => {
  const selectedVariant = useSelectedVariant(product);
  const images = useProductImages(product, selectedVariant?.selectedOptions);

  return images.map((image) => (
    <img
      style={{
        aspectRatio: `${image.width} / ${image.height}`,
      }}
      key={`${image.url}-${image.selectedOptions?.map((o) => `${o.name},${o.value}`).join('-')}`}
      src={image.url}
      alt={image.altText}
      width={image.width}
      height={image.height}
      className='w-full object-cover'
      quality={100}
    />
  ));
};
