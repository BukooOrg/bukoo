import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import { OrderStatusBadge } from '@/components/orders/OrderStatusBadge';
import { Spinner } from '@/components/ui/feedback/spinner';
import { Button } from '@/components/ui/forms/button';
import { orderApi } from '@/lib/apiClient';

export default function AccountOrdersPage() {
  const navigate = useNavigate();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [statusFilter, setStatusFilter] = useState('');
  const [hasLoadedOnce, setHasLoadedOnce] = useState(false);

  useEffect(() => {
    async function loadOrders() {
      setLoading(true);
      try {
        const response = await orderApi.findOrders({
          page,
          pageSize: 10,
          ...(statusFilter && { status: statusFilter }),
        });
        const data = response.data;
        setOrders(data.items || []);
        setTotalPages(data.meta?.totalPages || 1);
        if (!hasLoadedOnce && data.items?.length === 0 && !statusFilter) {
          setHasLoadedOnce(true);
        }
        if (data.items?.length > 0) {
          setHasLoadedOnce(true);
        }
      } catch {
        setOrders([]);
      } finally {
        setLoading(false);
      }
    }
    loadOrders();
  }, [page, statusFilter]);

  if (loading) {
    return (
      <div className='flex items-center justify-center min-h-[60vh]'>
        <Spinner size='lg' />
      </div>
    );
  }

  const showEmptyState = !orders.length && !hasLoadedOnce && !statusFilter;

  if (showEmptyState) {
    return (
      <div className='px-sides py-24'>
        <div className='max-w-2xl mx-auto text-center'>
          <h1 className='font-serif text-4xl font-black tracking-tighter text-primary'>
            No Orders Yet
          </h1>
          <p className='text-primary/40 font-bold italic text-sm mt-2'>
            Start shopping to see your orders here.
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
        <div className='flex items-center justify-between mb-8'>
          <div>
            <h1 className='font-serif text-4xl font-black tracking-tighter text-primary'>Orders</h1>
            <p className='text-primary/40 font-bold italic text-sm mt-1'>
              Track and manage your orders
            </p>
          </div>
          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPage(1);
            }}
            className='h-10 px-3 border border-gray-200 rounded text-sm'>
            <option value=''>All Status</option>
            <option value='pending'>Pending</option>
            <option value='paid'>Paid</option>
            <option value='shipped'>Shipped</option>
            <option value='delivered'>Delivered</option>
            <option value='cancelled'>Cancelled</option>
          </select>
        </div>

        {!orders.length ? (
          <div className='text-center py-24'>
            <p className='font-serif text-2xl italic text-primary/40'>
              No orders{statusFilter ? ` with status "${statusFilter}"` : ''} found.
            </p>
          </div>
        ) : (
          <div className='space-y-4'>
            {orders.map((order) => {
              const isPending = order.status?.toLowerCase() === 'pending';
              return (
                <div
                  key={order.id}
                  className='flex items-center justify-between p-6 border border-gray-200 rounded-lg bg-white hover:border-black transition-colors'>
                  <Link to={`/account/orders/${order.id}`} className='flex-1'>
                    <div>
                      <p className='text-lg font-medium font-serif'>
                        Order #{order.id.slice(0, 8)}
                      </p>
                      <p className='text-sm text-gray-500 mt-1'>
                        {new Date(order.createdAt).toLocaleDateString('en-US', {
                          year: 'numeric',
                          month: 'long',
                          day: 'numeric',
                        })}
                      </p>
                    </div>
                  </Link>
                  <div className='flex items-center gap-4'>
                    <div className='text-right'>
                      <OrderStatusBadge status={order.status} />
                      <p className='text-lg font-bold mt-2'>RM {Number(order.total).toFixed(2)}</p>
                      <p className='text-sm text-gray-500'>{order.itemCount} items</p>
                    </div>
                    {isPending && (
                      <Button
                        onClick={() => navigate(`/checkout/payment?orderId=${order.id}`)}
                        className='h-10 text-sm bg-primary text-white hover:bg-primary/90'>
                        Pay Now
                      </Button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {totalPages > 1 && (
          <div className='flex items-center justify-center gap-3 mt-8'>
            <Button
              variant='outline'
              disabled={page <= 1}
              onClick={() => setPage((p) => p - 1)}
              className='h-10'>
              Previous
            </Button>
            <span className='text-sm text-gray-500'>
              Page {page} of {totalPages}
            </span>
            <Button
              variant='outline'
              disabled={page >= totalPages}
              onClick={() => setPage((p) => p + 1)}
              className='h-10'>
              Next
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
