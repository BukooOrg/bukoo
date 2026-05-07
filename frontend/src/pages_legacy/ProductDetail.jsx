import { Box, Image as ImageIcon } from 'lucide-react';
import React, { useState, useEffect, Suspense } from 'react';
import { useParams, Link } from 'react-router-dom';

import { BookViewer3D } from '@/components/3d-book/BookViewer3D';
import { AddToCart } from '@/components/cart/AddToCart';
import { PageLayout } from '@/components/layout/PageLayout';
import Prose from '@/components/Prose';
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbSeparator,
  BreadcrumbPage,
} from '@/components/ui/navigation/breadcrumb';
import { getCollection, getProduct } from '@/lib/sfcc';
import { storeCatalog } from '@/lib/sfcc/constants';
import { formatPrice } from '@/lib/sfcc/utils';
import { cn } from '@/lib/utils';

import { DesktopGallery } from './Product/desktop-gallery';
import { MobileGallerySlider } from './Product/mobile-gallery-slider';
import { VariantSelectorSlots } from './Product/VariantSelector-slots';

export default function ProductDetail() {
  const { handle } = useParams();
  const [product, setProduct] = useState(null);
  const [collection, setCollection] = useState(null);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState('3d'); // default to 3d for the wow effect

  useEffect(() => {
    async function loadData() {
      try {
        const prod = await getProduct(handle);
        if (prod) {
          setProduct(prod);
          if (prod.categoryId) {
            const coll = await getCollection(prod.categoryId);
            setCollection(coll);
          }
        }
      } catch (error) {
        console.error('Failed to load product', error);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [handle]);

  if (loading) {
    return (
      <PageLayout className='bg-muted'>
        <div className='pt-48 font-serif italic text-center opacity-50'>Opening the pages...</div>
      </PageLayout>
    );
  }

  if (!product) {
    return (
      <PageLayout className='bg-muted'>
        <div className='pt-48 font-serif text-2xl text-center'>Book not found.</div>
      </PageLayout>
    );
  }

  const rootParentCategory = collection?.parentCategoryTree?.find(
    (c) => c.id !== storeCatalog.rootCategoryId
  );

  const hasVariants = product.variants?.length > 1;

  return (
    <PageLayout className='min-h-screen bg-muted'>
      <div className='flex flex-col md:grid md:grid-cols-12 md:gap-sides'>
        {/* Mobile Gallery Slider */}
        <div className='md:hidden col-span-full h-[60vh] min-h-[400px] relative'>
          <div className='absolute z-10 flex gap-2 top-4 right-4'>
            <button
              onClick={() => setViewMode(viewMode === '2d' ? '3d' : '2d')}
              className='p-3 transition-transform border rounded-full shadow-lg bg-white/80 backdrop-blur-md border-white/40 hover:scale-110 active:scale-95'>
              {viewMode === '2d' ? <Box className='w-5 h-5' /> : <ImageIcon className='w-5 h-5' />}
            </button>
          </div>
          <Suspense fallback={null}>
            {viewMode === '2d' ? (
              <MobileGallerySlider product={product} />
            ) : (
              <div className='w-full h-full bg-white/40 backdrop-blur-sm'>
                <BookViewer3D
                  frontCoverUrl={product.images?.[0]?.url}
                  backCoverUrl={product.images?.[1]?.url}
                />
              </div>
            )}
          </Suspense>
        </div>

        <div className='sticky top-0 flex flex-col col-span-5 2xl:col-span-4 max-md:col-span-full md:h-screen max-md:p-sides md:pl-sides md:pt-32 max-md:static'>
          <div className='col-span-full'>
            <Breadcrumb className='mb-3 col-span-full md:mb-8'>
              <BreadcrumbList>
                <BreadcrumbItem>
                  <BreadcrumbLink asChild>
                    <Link to='/shop'>Shop</Link>
                  </BreadcrumbLink>
                </BreadcrumbItem>
                {rootParentCategory && (
                  <>
                    <BreadcrumbSeparator />
                    <BreadcrumbItem>
                      <BreadcrumbLink asChild>
                        <Link to={`/shop/${rootParentCategory.id}`}>{rootParentCategory.name}</Link>
                      </BreadcrumbLink>
                    </BreadcrumbItem>
                  </>
                )}
                <BreadcrumbSeparator />
                <BreadcrumbItem>
                  <BreadcrumbPage>{product.title}</BreadcrumbPage>
                </BreadcrumbItem>
              </BreadcrumbList>
            </Breadcrumb>

            <div className='flex flex-col gap-4 mb-10 col-span-full max-md:order-2'>
              <div className='flex flex-col px-10 py-8 border shadow-2xl rounded-3xl bg-white/80 backdrop-blur-3xl border-white/40'>
                <div className='mb-6'>
                  <h1 className='mb-2 font-serif text-4xl font-black tracking-tighter lg:text-5xl text-primary'>
                    {product.title}
                  </h1>
                  <p className='text-sm italic font-bold text-primary/40'>
                    {product.vendor || 'Bukoo Editions'}
                  </p>
                </div>

                <p className='mb-10 text-sm font-medium leading-relaxed text-primary/70'>
                  {product.description}
                </p>

                <div className='flex items-center justify-between pt-6 mt-auto border-t border-primary/5'>
                  <p className='font-serif text-3xl font-black text-primary'>
                    {formatPrice(
                      product.priceRange?.minVariantPrice?.amount || '0',
                      product.priceRange?.minVariantPrice?.currencyCode || 'GBP'
                    )}
                  </p>
                  <div className='flex items-center gap-3'>
                    <div className='px-4 py-1 bg-primary/5 rounded-full text-[10px] font-black uppercase tracking-widest text-primary/40'>
                      Hardcover
                    </div>
                  </div>
                </div>

                {/* View Mode Toggle */}
                <div className='flex flex-col gap-3 pt-6 mt-6 border-t border-primary/5'>
                  <p className='text-[10px] font-black uppercase tracking-widest text-primary/30'>
                    Display Mode
                  </p>
                  <div className='flex p-1 bg-primary/5 rounded-xl'>
                    <button
                      onClick={() => setViewMode('2d')}
                      className={cn(
                        'flex-1 py-2 px-4 rounded-lg text-xs font-bold uppercase tracking-widest transition-all flex items-center justify-center gap-2',
                        {
                          'bg-white shadow-sm text-primary': viewMode === '2d',
                          'text-primary/40 hover:text-primary/60': viewMode !== '2d',
                        }
                      )}>
                      <ImageIcon className='w-3.5 h-3.5' /> 2D Gallery
                    </button>
                    <button
                      onClick={() => setViewMode('3d')}
                      className={cn(
                        'flex-1 py-2 px-4 rounded-lg text-xs font-bold uppercase tracking-widest transition-all flex items-center justify-center gap-2',
                        {
                          'bg-white shadow-sm text-primary': viewMode === '3d',
                          'text-primary/40 hover:text-primary/60': viewMode !== '3d',
                        }
                      )}>
                      <Box className='w-3.5 h-3.5' /> 3D Viewer
                    </button>
                  </div>
                </div>
              </div>

              <div className='grid grid-cols-1 gap-4'>
                <Suspense fallback={null}>
                  <VariantSelectorSlots product={product} />
                </Suspense>

                <Suspense fallback={null}>
                  <AddToCart
                    product={product}
                    size='lg'
                    className={cn(
                      'w-full py-6 rounded-2xl bg-primary text-secondary font-sans font-bold uppercase tracking-[0.2em] shadow-2xl hover:scale-[1.02] active:scale-[0.98] transition-all',
                      {
                        'col-span-full': !hasVariants,
                      }
                    )}
                  />
                </Suspense>
              </div>
            </div>
          </div>

          <Prose
            className='mb-auto prose-sm col-span-full opacity-70 max-md:order-3 max-md:mt-6'
            html={product.descriptionHtml}
          />
        </div>

        {/* Desktop Gallery */}
        <div className='relative hidden w-full h-screen col-span-7 col-start-6 overflow-y-auto md:block bg-white/20'>
          <div className='w-full h-full'>
            <Suspense fallback={null}>
              {viewMode === '2d' ? (
                <DesktopGallery product={product} />
              ) : (
                <div className='w-full h-full duration-700 animate-in fade-in'>
                  <BookViewer3D
                    frontCoverUrl={product.images?.[0]?.url}
                    backCoverUrl={product.images?.[1]?.url}
                  />
                </div>
              )}
            </Suspense>
          </div>
        </div>
      </div>
    </PageLayout>
  );
}
