import React, { useState, useEffect } from 'react';
import { Link, useParams } from 'react-router-dom';
import { toast } from 'sonner';

import { ConfirmDialog } from '@/components/cart/ConfirmDialog';
import { OrderStatusBadge } from '@/components/orders/OrderStatusBadge';
import { Spinner } from '@/components/ui/feedback/spinner';
import { Button } from '@/components/ui/forms/button';
import { orderApi } from '@/lib/apiClient';

function formatDate(dateValue) {
  if (!dateValue) return '';
  const d = typeof dateValue === 'string' ? new Date(dateValue) : dateValue;
  return d.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
}

function formatPrice(amount, currency = 'RM') {
  return `${currency} ${Number(amount).toFixed(2)}`;
}

function OrderItemCard({ item }) {
  return (
    <div className='flex gap-8 p-8 border border-gray-200 rounded-lg bg-white'>
      <div className='w-32 h-44 shrink-0 overflow-hidden rounded bg-gray-100'>
        {item.bookCoverUrl ? (
          <img
            src={item.bookCoverUrl}
            alt={item.bookTitle}
            className='w-full h-full object-cover'
          />
        ) : (
          <div className='w-full h-full flex items-center justify-center text-gray-400 text-base'>
            No cover
          </div>
        )}
      </div>

      <div className='flex-1 min-w-0'>
        <p className='text-2xl font-medium font-serif line-clamp-1'>{item.bookTitle}</p>
        <p className='text-lg text-gray-500 mt-2'>RM {Number(item.unitPrice).toFixed(2)}</p>

        <div className='flex items-center justify-between mt-6'>
          <span className='text-lg text-gray-500'>Qty: {item.quantity}</span>
          <span className='text-xl font-medium'>RM {Number(item.lineTotal).toFixed(2)}</span>
        </div>
      </div>
    </div>
  );
}

function AdminOrderSummary({ order }) {
  return (
    <div className='bg-white border border-gray-200 rounded-lg p-8 space-y-6'>
      <h2 className='font-serif text-2xl font-bold text-black'>Summary</h2>
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

      {order.user && (
        <div className='pt-6 border-t border-gray-200'>
          <h3 className='text-base font-bold text-gray-700 mb-2'>Customer</h3>
          <p className='text-base text-gray-600'>{order.user?.name || 'N/A'}</p>
          <p className='text-base text-gray-500'>{order.user?.email || 'N/A'}</p>
        </div>
      )}

      {order.addressSnapshot && (
        <div className='pt-6 border-t border-gray-200'>
          <h3 className='text-base font-bold text-gray-700 mb-2'>Shipping Address</h3>
          <p className='text-base text-gray-600'>
            {order.addressSnapshot.address_line1}
            {order.addressSnapshot.address_line2 && (
              <>
                <br />
                {order.addressSnapshot.address_line2}
              </>
            )}
            <br />
            {order.addressSnapshot.city}, {order.addressSnapshot.state}{' '}
            {order.addressSnapshot.postcode}
          </p>
        </div>
      )}

      {order.payment && (
        <div className='pt-6 border-t border-gray-200'>
          <h3 className='text-base font-bold text-gray-700 mb-2'>Payment</h3>
          <p className='text-base text-gray-600 capitalize'>
            Method: {order.payment.method?.replace('_', ' ')}
          </p>
          <p className='text-base text-gray-600 capitalize'>Status: {order.payment.status}</p>
          {order.payment.simulatedRef && (
            <p className='text-base text-gray-500 mt-1'>Ref: {order.payment.simulatedRef}</p>
          )}
        </div>
      )}
    </div>
  );
}

export default function AdminOrderDetailPage() {
  const { orderId } = useParams();
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const [cancelDialog, setCancelDialog] = useState(false);
  const [cancelling, setCancelling] = useState(false);

  useEffect(() => {
    async function loadOrder() {
      if (!orderId) return;
      try {
        const response = await orderApi.viewOrderDetail({ orderId });
        setOrder(response.data);
      } catch {
        toast.error('Order not found');
      } finally {
        setLoading(false);
      }
    }
    loadOrder();
  }, [orderId]);

  const handleStatusUpdate = async (newStatus) => {
    setUpdating(true);
    try {
      await orderApi.updateOrderStatus({
        orderId,
        body: { status: newStatus },
      });
      toast.success(`Order status updated to ${newStatus}`);
      const response = await orderApi.viewOrderDetail({ orderId });
      setOrder(response.data);
    } catch {
      toast.error('Failed to update order status');
    } finally {
      setUpdating(false);
    }
  };

  const handleCancel = async () => {
    setCancelling(true);
    try {
      await orderApi.cancelOrder({ orderId });
      toast.success('Order cancelled');
      const response = await orderApi.viewOrderDetail({ orderId });
      setOrder(response.data);
    } catch {
      toast.error('Failed to cancel order');
    } finally {
      setCancelling(false);
      setCancelDialog(false);
    }
  };

  if (loading) {
    return (
      <div className='flex items-center justify-center min-h-[60vh]'>
        <Spinner size='lg' />
      </div>
    );
  }

  if (!order) {
    return (
      <div className='px-sides py-24'>
        <div className='max-w-2xl mx-auto text-center'>
          <h1 className='font-serif text-4xl font-black tracking-tighter text-primary'>
            Order Not Found
          </h1>
          <p className='text-primary/40 font-bold italic text-sm mt-2'>
            This order could not be found
          </p>
          <Link to='/admin/orders' className='mt-4 text-primary underline'>
            Back to Orders
          </Link>
        </div>
      </div>
    );
  }

  const status = order.status?.toLowerCase();
  const isPending = status === 'pending';
  const isPaid = status === 'paid';
  const isShipped = status === 'shipped';

  return (
    <>
      <div className='px-sides py-16'>
        <div className='max-w-6xl mx-auto'>
          <div className='flex items-center justify-between mb-10'>
            <div>
              <h1 className='font-serif text-4xl font-black tracking-tighter text-primary'>
                Order #{order.id.slice(0, 8)}
              </h1>
              <p className='text-primary/40 font-bold italic text-sm mt-1'>
                {formatDate(order.createdAt)}
              </p>
            </div>
            <div className='flex items-center gap-3'>
              <OrderStatusBadge status={order.status} className='text-base px-4 py-1' />
              {isPending && (
                <Button
                  onClick={() => handleStatusUpdate('paid')}
                  disabled={updating}
                  variant='outline'
                  className='h-12 text-base'>
                  {updating ? 'Processing...' : 'Mark as Paid'}
                </Button>
              )}
              {isPaid && (
                <Button
                  onClick={() => handleStatusUpdate('shipped')}
                  disabled={updating}
                  className='h-12 text-base bg-primary text-white hover:bg-primary/90'>
                  {updating ? 'Processing...' : 'Ship Order'}
                </Button>
              )}
              {isShipped && (
                <Button
                  onClick={() => handleStatusUpdate('delivered')}
                  disabled={updating}
                  className='h-12 text-base bg-primary text-white hover:bg-primary/90'>
                  {updating ? 'Processing...' : 'Mark as Delivered'}
                </Button>
              )}
              {(isPending || isPaid) && (
                <Button
                  onClick={() => setCancelDialog(true)}
                  disabled={cancelling}
                  variant='outline'
                  className='h-12 text-base text-red-600 border-red-300 hover:bg-red-50'>
                  {cancelling ? 'Cancelling...' : 'Cancel'}
                </Button>
              )}
            </div>
          </div>

          <div className='grid grid-cols-1 lg:grid-cols-3 gap-10'>
            <div className='lg:col-span-2 space-y-6'>
              <h2 className='font-serif text-2xl font-bold text-black'>
                Items ({order.items.length})
              </h2>
              {order.items.map((item) => (
                <OrderItemCard key={item.id} item={item} />
              ))}
            </div>

            <div className='lg:col-span-1'>
              <div className='sticky top-24'>
                <AdminOrderSummary order={order} />
              </div>
            </div>
          </div>
        </div>
      </div>

      <ConfirmDialog
        open={cancelDialog}
        onOpenChange={setCancelDialog}
        title='Cancel Order?'
        description='This will cancel the order and restore stock. This action cannot be undone.'
        onConfirm={handleCancel}
        loading={cancelling}
      />
    </>
  );
}
