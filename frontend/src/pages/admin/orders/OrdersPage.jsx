import { Loader2, Package, Truck } from 'lucide-react';
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { toast } from 'sonner';

import { OrderStatusBadge } from '@/components/orders/OrderStatusBadge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/data-display/table';
import { Spinner } from '@/components/ui/feedback/spinner';
import { Button } from '@/components/ui/forms/button';
import { orderApi, userApi } from '@/lib/apiClient';

function formatDate(date) {
  return new Date(date).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

export default function AdminOrdersPage() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [statusFilter, setStatusFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [actingId, setActingId] = useState(null);
  const [userNames, setUserNames] = useState({});

  useEffect(() => {
    async function loadOrders() {
      setLoading(true);
      setUserNames({});
      try {
        const response = await orderApi.findOrders({
          page,
          pageSize: 20,
          ...(statusFilter && { status: statusFilter }),
          ...(searchQuery && { search: searchQuery }),
        });
        const data = response.data;
        setOrders(data.items || []);
        setTotalPages(data.meta?.totalPages || 1);
      } catch {
        setOrders([]);
      } finally {
        setLoading(false);
      }
    }
    loadOrders();
  }, [page, statusFilter, searchQuery]);

  useEffect(() => {
    if (!orders.length) return;
    const userIds = [...new Set(orders.map((o) => o.userId).filter(Boolean))];
    if (!userIds.length) return;
    let cancelled = false;
    async function loadUsers() {
      const names = {};
      await Promise.all(
        userIds.map(async (id) => {
          if (cancelled) return;
          try {
            const res = await userApi.viewUserProfile({ userId: id });
            if (!cancelled) {
              names[id] = res.data.fullName || res.data.email || id;
            }
          } catch {
            if (!cancelled) {
              names[id] = id;
            }
          }
        })
      );
      if (!cancelled) {
        setUserNames(names);
      }
    }
    loadUsers();
    return () => {
      cancelled = true;
    };
  }, [orders]);

  const handleStatusUpdate = async (orderId, newStatus) => {
    setActingId(orderId);
    try {
      await orderApi.updateOrderStatus({
        orderId,
        updateOrderStatusRequest: { status: newStatus },
      });
      toast.success(`Order marked as ${newStatus}`);
      const response = await orderApi.findOrders({
        page,
        pageSize: 20,
        ...(statusFilter && { status: statusFilter }),
        ...(searchQuery && { search: searchQuery }),
      });
      const data = response.data;
      setOrders(data.items || []);
      setTotalPages(data.meta?.totalPages || 1);
    } catch (error) {
      console.error('Failed to update order status:', error);
      toast.error(`Failed to update order status: ${error.message || 'Unknown error'}`);
    } finally {
      setActingId(null);
    }
  };

  if (loading) {
    return (
      <div className='flex items-center justify-center min-h-[60vh]'>
        <Spinner size='lg' />
      </div>
    );
  }

  return (
    <div className='px-sides py-16'>
      <div className='max-w-7xl mx-auto'>
        {/* Header */}
        <div className='text-center pt-8'>
          <h1 className='text-4xl font-serif font-black mb-2 text-primary tracking-tighter'>
            Orders
          </h1>
          <p className='text-primary/40 font-bold italic text-sm'>
            Manage and track all customer orders
          </p>
        </div>

        {/* Top bar — filters */}
        <div className='flex flex-wrap items-center justify-end gap-3'>
          <input
            type='text'
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              setPage(1);
            }}
            placeholder='Search orders...'
            className='h-10 px-3 border rounded-lg text-sm w-64 border-primary/10 focus:border-primary/30 focus:outline-none focus:ring-2 focus:ring-primary/10 transition-all'
          />
          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPage(1);
            }}
            className='h-10 px-3 border rounded-lg text-sm border-primary/10 focus:border-primary/30 focus:outline-none focus:ring-2 focus:ring-primary/10 transition-all'>
            <option value=''>All Status</option>
            <option value='pending'>Pending</option>
            <option value='paid'>Paid</option>
            <option value='shipped'>Shipped</option>
            <option value='delivered'>Delivered</option>
            <option value='cancelled'>Cancelled</option>
          </select>
        </div>

        {/* Table */}
        <div className='overflow-hidden bg-white border rounded-2xl border-primary/5'>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Order ID</TableHead>
                <TableHead>Customer</TableHead>
                <TableHead className='w-32'>Date</TableHead>
                <TableHead className='w-28'>Status</TableHead>
                <TableHead className='w-20'>Items</TableHead>
                <TableHead className='w-28 text-right'>Total</TableHead>
                <TableHead className='w-20 text-right'>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {orders.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className='py-16 text-center'>
                    <p className='font-serif text-lg italic text-primary/30'>
                      No orders{statusFilter ? ` with status "${statusFilter}"` : ''} found
                    </p>
                  </TableCell>
                </TableRow>
              ) : (
                orders.map((order) => {
                  const status = order.status?.toLowerCase();
                  const isPaid = status === 'paid';
                  const isShipped = status === 'shipped';
                  const isActing = actingId === order.id;
                  return (
                    <TableRow key={order.id}>
                      <TableCell>
                        <Link
                          to={`/admin/orders/${order.id}`}
                          className='font-sans font-bold transition-colors text-primary hover:text-primary/70'>
                          #{order.id.slice(0, 8)}
                        </Link>
                      </TableCell>
                      <TableCell className='text-primary/60 text-sm'>
                        {order.userId ? (
                          <Link
                            to={`/admin/users/${order.userId}`}
                            className='transition-colors text-primary/60 hover:text-primary'>
                            {userNames[order.userId] || order.userId}
                          </Link>
                        ) : (
                          <span className='text-primary/30'>Deleted</span>
                        )}
                      </TableCell>
                      <TableCell className='text-sm text-primary/40'>
                        {formatDate(order.createdAt)}
                      </TableCell>
                      <TableCell>
                        <OrderStatusBadge status={order.status} />
                      </TableCell>
                      <TableCell className='text-sm text-primary/40'>{order.itemCount}</TableCell>
                      <TableCell className='text-sm font-semibold text-right'>
                        RM {Number(order.total).toFixed(2)}
                      </TableCell>
                      <TableCell className='text-right'>
                        <div className='flex items-center justify-end gap-1'>
                          {isPaid && (
                            <Button
                              onClick={() => handleStatusUpdate(order.id, 'shipped')}
                              disabled={isActing}
                              variant='ghost'
                              size='icon'
                              className='w-8 h-8 rounded-lg text-primary/40 hover:text-primary hover:bg-primary/5'>
                              {isActing ? (
                                <Loader2 className='w-4 h-4 animate-spin' />
                              ) : (
                                <Truck className='w-4 h-4' />
                              )}
                            </Button>
                          )}
                          {isShipped && (
                            <Button
                              onClick={() => handleStatusUpdate(order.id, 'delivered')}
                              disabled={isActing}
                              variant='ghost'
                              size='icon'
                              className='w-8 h-8 rounded-lg text-primary/40 hover:text-primary hover:bg-primary/5'>
                              {isActing ? (
                                <Loader2 className='w-4 h-4 animate-spin' />
                              ) : (
                                <Package className='w-4 h-4' />
                              )}
                            </Button>
                          )}
                          {!isPaid && !isShipped && (
                            <span className='text-xs text-primary/30'>—</span>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className='flex items-center justify-center gap-3 mt-8'>
            <Button
              variant='outline'
              disabled={page <= 1}
              onClick={() => setPage((p) => p - 1)}
              className='h-10'>
              Previous
            </Button>
            <span className='text-sm text-primary/40'>
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
