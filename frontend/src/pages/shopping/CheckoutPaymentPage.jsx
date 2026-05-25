import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { toast } from 'sonner';

import { Spinner } from '@/components/ui/feedback/spinner';
import { Button } from '@/components/ui/forms/button';
import { orderApi } from '@/lib/apiClient';

function formatPrice(amount, currency = 'RM') {
  return `${currency} ${Number(amount).toFixed(2)}`;
}

export default function CheckoutPaymentPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const orderId = searchParams.get('orderId');
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);
  const [paymentMethod, setPaymentMethod] = useState('online_banking');
  const [processing, setProcessing] = useState(false);

  const [bankName, setBankName] = useState('');
  const [accountNumber, setAccountNumber] = useState('');
  const [cardNumber, setCardNumber] = useState('');
  const [expiryDate, setExpiryDate] = useState('');
  const [cvv, setCvv] = useState('');

  useEffect(() => {
    async function loadOrder() {
      if (!orderId) {
        setLoading(false);
        return;
      }
      try {
        const response = await orderApi.viewOrderDetail({ orderId });
        setOrder(response.data);
      } catch {
        toast.error('Order not found');
        navigate('/account/orders');
      } finally {
        setLoading(false);
      }
    }
    loadOrder();
  }, [orderId, navigate]);

  if (loading) {
    return (
      <div className='flex items-center justify-center min-h-[60vh]'>
        <Spinner size='lg' />
      </div>
    );
  }

  if (!orderId || !order) {
    return (
      <div className='px-sides py-24'>
        <div className='max-w-2xl mx-auto text-center'>
          <h1 className='font-serif text-4xl font-black tracking-tighter text-primary'>
            Invalid Order
          </h1>
          <p className='text-primary/40 font-bold italic text-sm mt-2'>
            This order could not be found
          </p>
          <Link to='/account/orders' className='mt-4 text-primary underline'>
            Back to Orders
          </Link>
        </div>
      </div>
    );
  }

  if (order.status?.toLowerCase() !== 'pending') {
    return (
      <div className='px-sides py-24'>
        <div className='max-w-2xl mx-auto text-center'>
          <h1 className='font-serif text-4xl font-black tracking-tighter text-primary'>
            Payment Not Required
          </h1>
          <p className='text-primary/40 font-bold italic text-sm mt-2'>
            This order has already been {order.status}
          </p>
          <Link to={`/account/orders/${orderId}`} className='mt-4 text-primary underline'>
            View Order
          </Link>
        </div>
      </div>
    );
  }

  const handlePay = async () => {
    if (paymentMethod === 'online_banking' && (!bankName || !accountNumber)) {
      toast.error('Please fill in all bank details');
      return;
    }
    if (paymentMethod === 'card' && (!cardNumber || !expiryDate || !cvv)) {
      toast.error('Please fill in all card details');
      return;
    }

    setProcessing(true);
    try {
      const body =
        paymentMethod === 'online_banking'
          ? {
              paymentMethod: 'online_banking',
              outcome: 'success',
              bankName: bankName,
              accountNumber: accountNumber,
            }
          : {
              paymentMethod: 'card',
              outcome: 'success',
              cardNumber: cardNumber,
              expiryDate: expiryDate,
              cvv,
            };

      await orderApi.payOrder({ orderId, body });
      navigate(`/checkout/confirmation?orderId=${orderId}`);
    } catch (error) {
      console.error('Payment failed:', error);
      toast.error('Payment failed');
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div className='px-sides py-16'>
      <div className='max-w-4xl mx-auto'>
        <div className='mb-10'>
          <h1 className='font-serif text-4xl font-black tracking-tighter text-primary'>Payment</h1>
          <p className='text-primary/40 font-bold italic text-sm mt-1'>
            Order #{order.id.slice(0, 8)} &middot; {formatPrice(order.total)}
          </p>
        </div>

        <div className='grid grid-cols-1 lg:grid-cols-3 gap-10'>
          <div className='lg:col-span-2'>
            <div className='bg-white border border-gray-200 rounded-lg p-8 space-y-6'>
              <div className='space-y-3'>
                <label className='flex items-center gap-3 p-4 border border-gray-200 rounded-lg cursor-pointer hover:border-primary'>
                  <input
                    type='radio'
                    name='payment'
                    value='online_banking'
                    checked={paymentMethod === 'online_banking'}
                    onChange={() => setPaymentMethod('online_banking')}
                    className='size-4'
                  />
                  <span className='text-base font-medium'>Online Banking</span>
                </label>

                {paymentMethod === 'online_banking' && (
                  <div className='space-y-3 pl-4'>
                    <div>
                      <label className='block text-sm font-medium text-gray-700 mb-1'>
                        Bank Name
                      </label>
                      <input
                        type='text'
                        value={bankName}
                        onChange={(e) => setBankName(e.target.value)}
                        placeholder='e.g. Maybank'
                        className='w-full h-10 px-3 border border-gray-200 rounded text-sm'
                      />
                    </div>
                    <div>
                      <label className='block text-sm font-medium text-gray-700 mb-1'>
                        Account Number
                      </label>
                      <input
                        type='text'
                        value={accountNumber}
                        onChange={(e) => setAccountNumber(e.target.value)}
                        placeholder='e.g. 1234567890'
                        className='w-full h-10 px-3 border border-gray-200 rounded text-sm'
                      />
                    </div>
                  </div>
                )}
              </div>

              <div className='space-y-3'>
                <label className='flex items-center gap-3 p-4 border border-gray-200 rounded-lg cursor-pointer hover:border-primary'>
                  <input
                    type='radio'
                    name='payment'
                    value='card'
                    checked={paymentMethod === 'card'}
                    onChange={() => setPaymentMethod('card')}
                    className='size-4'
                  />
                  <span className='text-base font-medium'>Credit / Debit Card</span>
                </label>

                {paymentMethod === 'card' && (
                  <div className='space-y-3 pl-4'>
                    <div>
                      <label className='block text-sm font-medium text-gray-700 mb-1'>
                        Card Number
                      </label>
                      <input
                        type='text'
                        value={cardNumber}
                        onChange={(e) => setCardNumber(e.target.value)}
                        placeholder='e.g. 4111111111111111'
                        className='w-full h-10 px-3 border border-gray-200 rounded text-sm'
                      />
                    </div>
                    <div className='grid grid-cols-2 gap-3'>
                      <div>
                        <label className='block text-sm font-medium text-gray-700 mb-1'>
                          Expiry Date
                        </label>
                        <input
                          type='text'
                          value={expiryDate}
                          onChange={(e) => setExpiryDate(e.target.value)}
                          placeholder='MM/YY'
                          className='w-full h-10 px-3 border border-gray-200 rounded text-sm'
                        />
                      </div>
                      <div>
                        <label className='block text-sm font-medium text-gray-700 mb-1'>CVV</label>
                        <input
                          type='text'
                          value={cvv}
                          onChange={(e) => setCvv(e.target.value)}
                          placeholder='123'
                          className='w-full h-10 px-3 border border-gray-200 rounded text-sm'
                        />
                      </div>
                    </div>
                  </div>
                )}
              </div>

              <Button
                onClick={handlePay}
                disabled={processing}
                className='w-full bg-primary text-white h-14 text-lg hover:bg-primary/90'
                size='lg'>
                {processing ? 'Processing...' : `Pay ${formatPrice(order.total)}`}
              </Button>
            </div>
          </div>

          <div className='lg:col-span-1'>
            <div className='sticky top-24 bg-white border border-gray-200 rounded-lg p-8 space-y-6'>
              <h2 className='font-serif text-2xl font-bold text-black'>Order Summary</h2>
              <div className='space-y-4 text-base'>
                <div className='flex justify-between'>
                  <span className='text-gray-500'>Subtotal</span>
                  <span>{formatPrice(order.subtotal)}</span>
                </div>
                <div className='flex justify-between'>
                  <span className='text-gray-500'>Shipping</span>
                  <span>{formatPrice(order.shippingCost)}</span>
                </div>
              </div>
              <div className='pt-6 border-t border-gray-200'>
                <div className='flex justify-between items-baseline'>
                  <span className='font-serif text-xl font-bold text-black'>Total</span>
                  <span className='font-serif text-3xl font-black text-black'>
                    {formatPrice(order.total)}
                  </span>
                </div>
              </div>

              <div className='pt-6 border-t border-gray-200'>
                <h3 className='text-base font-bold text-gray-700 mb-2'>
                  Items ({order.items.length})
                </h3>
                <div className='space-y-3'>
                  {order.items.map((item) => (
                    <div key={item.id} className='flex justify-between text-sm'>
                      <span className='text-gray-600 truncate mr-2'>{item.bookTitle}</span>
                      <span className='text-gray-500 shrink-0'>x{item.quantity}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
