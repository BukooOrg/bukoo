import { Suspense } from 'react';
import { Link } from 'react-router-dom';

import { cn } from '@/lib/utils';

import { AddToCart } from '../cart/add-to-cart';
import { Badge } from '../ui/data-display/badge';

export function FeaturedProductLabel({ product, principal = false, className }) {
  if (principal) {
    return (
      <div
        className={cn(
          'p-8 bg-card backdrop-blur-md w-fit border border-secondary/30 flex flex-col gap-y-4 shadow-xl',
          className
        )}>
        <div>
          <Badge className='bg-primary text-white font-sans font-bold uppercase tracking-widest px-3 py-1 text-[10px]'>
            {product.categoryId === 'top-seller' ? 'Staff Pick' : 'Best Seller'}
          </Badge>
        </div>
        <div className='flex flex-col gap-1'>
          <Link
            to={`/product/${product.handle}`}
            className='text-4xl font-serif font-black tracking-tighter text-primary hover:opacity-70 transition-opacity'>
            {product.title}
          </Link>
          <p className='text-lg font-sans font-bold italic opacity-60'>{product.vendor}</p>
        </div>
        <div className='max-w-md'>
          <p className='text-sm font-sans font-medium leading-relaxed opacity-80'>
            {product.description}
          </p>
        </div>
        <div className='flex items-center justify-between mt-4'>
          <p className='text-2xl font-serif font-black text-primary'>
            ${Number(product.priceRange.minVariantPrice.amount)}
          </p>
          <Suspense fallback={null}>
            <AddToCart className='ml-8' size='lg' product={product} />
          </Suspense>
        </div>
      </div>
    );
  }

  return (
    <div
      className={cn(
        'p-4 bg-card/90 backdrop-blur-md border border-secondary/30 w-fit flex items-center gap-6 shadow-lg',
        className
      )}>
      <div className='leading-tight pr-4'>
        <Link
          to={`/product/${product.handle}`}
          className='block text-xl font-serif font-black text-primary hover:opacity-70 transition-opacity'>
          {product.title}
        </Link>
        <p className='text-sm font-sans font-bold italic opacity-60 mb-2'>{product.vendor}</p>
        <p className='text-lg font-serif font-black text-primary'>
          ${Number(product.priceRange.minVariantPrice.amount)}
        </p>
      </div>
      <Suspense fallback={null}>
        <AddToCart product={product} iconOnly={true} variant='default' size='icon-lg' />
      </Suspense>
    </div>
  );
}
