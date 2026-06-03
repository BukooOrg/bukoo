import React, { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { toast } from 'sonner';

import { useCart } from '@/components/cart/CartContext';
import { Spinner } from '@/components/ui/feedback/spinner';
import { Button } from '@/components/ui/forms/button';
import { useApiQuery } from '@/hooks/useApiQuery';
import { bookApi, orderApi, userApi } from '@/lib/apiClient';

function getErrorMessage(error) {
  const code = error?.response?.data?.error?.code;
  const message = error?.response?.data?.error?.message;
  switch (code) {
    case 'OUT_OF_STOCK':
      return message || 'One or more items in your cart are out of stock';
    case 'BOOK_NOT_FOUND':
      return 'A book in your cart is no longer available';
    case 'CART_ITEM_NOT_FOUND':
      return 'An item in your cart was not found. Please refresh and try again';
    case 'ADDRESS_NOT_FOUND':
      return 'Please add a shipping address before checkout';
    default:
      return message || 'Failed to place order';
  }
}

export default function CheckoutPage() {
  const { cart, loading: cartLoading } = useCart();
  const navigate = useNavigate();
  const [placing, setPlacing] = useState(false);
  const [addressChecked, setAddressChecked] = useState(false);
  const [bookData, setBookData] = useState(null);
  const [validating, setValidating] = useState(false);

  const fetchAddress = useCallback(() => userApi.getMyAddress(), []);

  const { data: address, loading: addressLoading } = useApiQuery(fetchAddress, {
    skipOnError: true,
  });

  useEffect(() => {
    if (!addressLoading && addressChecked === false) {
      setAddressChecked(true);
      if (!address) {
        toast.error('Please add a shipping address before checkout');
        navigate('/account/address', { replace: true });
      }
    }
  }, [addressLoading, address, addressChecked, navigate]);

  useEffect(() => {
    setBookData(null);
  }, [cart?.items?.length]);

  useEffect(() => {
    if (cart?.items?.length && !bookData && !validating) {
      setValidating(true);
      const bookIds = cart.items.map((item) => item.bookId);
      Promise.allSettled(bookIds.map((id) => bookApi.viewBookDetail({ bookId: id })))
        .then((results) => {
          const data = {};
          const errors = [];
          results.forEach((result, idx) => {
            if (result.status === 'fulfilled') {
              data[bookIds[idx]] = result.value.data;
            } else {
              errors.push(bookIds[idx]);
            }
          });
          setBookData(data);
          if (errors.length > 0) {
            toast.warning('Some books could not be verified');
          }
        })
        .finally(() => setValidating(false));
    }
  }, [cart?.items, bookData, validating]);

  const isLoading = cartLoading || addressLoading || !addressChecked || validating;

  if (isLoading) {
    return (
      <div className='flex items-center justify-center min-h-[60vh]'>
        <Spinner size='lg' />
      </div>
    );
  }

  if (!address) {
    return null;
  }

  if (!cart?.items?.length) {
    return (
      <div className='px-sides py-24'>
        <div className='max-w-2xl mx-auto text-center'>
          <h1 className='font-sans text-4xl font-bold text-black tracking-tight'>
            Your Cart is Empty
          </h1>
          <p className='mt-4 text-base text-gray-500'>
            Add some books to your cart before checking out.
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

  const subtotal = cart.items.reduce(
    (sum, item) => sum + Number(item.book.price) * item.quantity,
    0
  );
  const shipping = 5.0;
  const total = subtotal + shipping;

  const validateCart = () => {
    if (!bookData) return true;

    const issues = [];
    for (const item of cart.items) {
      const current = bookData[item.bookId];
      if (!current) {
        issues.push(`"${item.book.title}" is no longer available`);
        continue;
      }
      if (current.stockQuantity === 0) {
        issues.push(`"${item.book.title}" is out of stock`);
      } else if (current.stockQuantity < item.quantity) {
        issues.push(`"${item.book.title}" only has ${current.stockQuantity} left`);
      }
      const cartPrice = Number(item.book.price);
      const currentPrice = Number(current.price);
      if (Math.abs(cartPrice - currentPrice) > 0.001) {
        issues.push(
          `"${item.book.title}" price changed from RM ${cartPrice.toFixed(2)} to RM ${currentPrice.toFixed(2)}`
        );
      }
    }

    if (issues.length > 0) {
      toast.error('Cart issues', { description: issues.join('\n') });
      return false;
    }
    return true;
  };

  const handlePlaceOrder = async () => {
    if (!validateCart()) return;

    setPlacing(true);
    try {
      const cartItemIds = cart.items.map((item) => item.id);
      const response = await orderApi.placeOrder({
        placeOrderRequest: { cartItemIds },
      });
      const order = response.data;
      navigate(`/checkout/payment?orderId=${order.id}`);
    } catch (error) {
      toast.error(getErrorMessage(error));
    } finally {
      setPlacing(false);
    }
  };

  return (
    <div className='px-sides py-16'>
      <div className='max-w-4xl mx-auto'>
        <h1 className='font-sans text-3xl font-bold text-black tracking-tight mb-8'>Checkout</h1>

        <div className='grid grid-cols-1 lg:grid-cols-3 gap-8'>
          <div className='lg:col-span-2 space-y-4'>
            <h2 className='text-base font-bold text-black'>Order Items ({cart.items.length})</h2>
            {cart.items
              .sort((a, b) => a.book.title.localeCompare(b.book.title))
              .map((item) => (
                <div
                  key={item.id}
                  className='flex gap-4 p-4 border border-gray-200 rounded-2xl bg-white'>
                  <div className='w-16 h-24 shrink-0 overflow-hidden rounded-2xl bg-gray-100'>
                    {item.book.coverUrl ? (
                      <img
                        src={item.book.coverUrl}
                        alt={item.book.title}
                        referrerpolicy='no-referrer'
                        className='w-full h-full object-contain bg-gray-100'
                      />
                    ) : (
                      <div className='w-full h-full flex items-center justify-center text-gray-400 text-xs'>
                        No cover
                      </div>
                    )}
                  </div>
                  <div className='flex-1 min-w-0'>
                    <p className='text-sm font-semibold font-sans truncate text-black'>
                      {item.book.title}
                    </p>
                    <div className='flex items-center gap-4 mt-2 text-xs text-gray-500'>
                      <span>RM {Number(item.book.price).toFixed(2)} each</span>
                      <span>&middot;</span>
                      <span>Qty: {item.quantity}</span>
                    </div>
                  </div>
                  <div className='shrink-0 text-right'>
                    <p className='text-base font-medium'>
                      RM {(Number(item.book.price) * item.quantity).toFixed(2)}
                    </p>
                  </div>
                </div>
              ))}
          </div>

          <div className='lg:col-span-1'>
            <div className='sticky top-24 bg-white border border-gray-200 rounded-2xl p-6 space-y-4'>
              <h2 className='text-base font-bold text-black'>Order Summary</h2>
              <div className='space-y-2 text-sm'>
                <div className='flex justify-between'>
                  <span className='text-gray-500'>Subtotal</span>
                  <span>RM {subtotal.toFixed(2)}</span>
                </div>
                <div className='flex justify-between'>
                  <span className='text-gray-500'>Shipping</span>
                  <span>RM {shipping.toFixed(2)}</span>
                </div>
              </div>
              <div className='pt-4 border-t border-gray-200'>
                <div className='flex justify-between items-baseline'>
                  <span className='text-base font-bold text-black'>Total</span>
                  <span className='text-2xl font-bold text-black'>RM {total.toFixed(2)}</span>
                </div>
              </div>
              <Button
                onClick={handlePlaceOrder}
                disabled={placing}
                className='w-full bg-black text-white h-14 text-lg'
                size='lg'>
                {placing ? 'Placing Order...' : 'Place Order'}
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
