import React from 'react';
import { Link } from 'react-router-dom';

import { Spinner } from '@/components/ui/feedback/spinner';
import { Button } from '@/components/ui/forms/button';
import { useWishlist } from '@/components/wishlist/WishlistContext';
import { WishlistItemCard } from '@/components/wishlist/WishlistItemCard';

export default function WishlistPage() {
  const { wishlist, loading } = useWishlist();

  if (loading) {
    return (
      <div className='flex items-center justify-center min-h-[60vh]'>
        <Spinner size='lg' />
      </div>
    );
  }

  if (!wishlist?.items?.length) {
    return (
      <div className='px-sides py-24'>
        <div className='max-w-2xl mx-auto text-center'>
          <h1 className='font-serif text-5xl font-black text-black tracking-tighter'>
            Your Wishlist is Empty
          </h1>
          <p className='mt-6 text-lg text-gray-500'>
            Save books you love and come back to them anytime.
          </p>
          <Link to='/shop'>
            <Button className='mt-10 bg-black text-white h-14 text-lg' size='lg'>
              Browse Books
            </Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className='px-sides py-16'>
      <div className='max-w-6xl mx-auto'>
        <h1 className='font-serif text-5xl font-black text-black tracking-tighter mb-10'>
          Your Wishlist ({wishlist.items.length})
        </h1>

        <div className='grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6'>
          {wishlist.items
            .sort((a, b) => a.book.title.localeCompare(b.book.title))
            .map((item) => (
              <WishlistItemCard key={item.id} item={item} />
            ))}
        </div>
      </div>
    </div>
  );
}
