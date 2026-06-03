import {
  Search,
  Plus,
  AlertCircle,
  Loader2,
  Users,
  ChevronLeft,
  ChevronRight,
  Power,
  Eye,
} from 'lucide-react';
import React, { useState, useCallback, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { toast } from 'sonner';

import { RoleBadge, StatusBadge } from '@/components/admin/users/UserStatusBadge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/data-display/table';
import { Button } from '@/components/ui/forms/button';
import { userApi } from '@/lib/apiClient';
import { cn } from '@/lib/utils';

const ROLE_OPTIONS = [
  { value: 'all', label: 'All Roles' },
  { value: 'admin', label: 'Admin' },
  { value: 'user', label: 'User' },
];

const STATUS_OPTIONS = [
  { value: 'all', label: 'All Status' },
  { value: 'active', label: 'Active' },
  { value: 'pending', label: 'Pending' },
  { value: 'suspended', label: 'Suspended' },
];

function formatDate(dateStr) {
  if (!dateStr) return '—';
  return new Date(dateStr).toLocaleDateString('en-MY', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

function formatLastLogin(dateStr) {
  if (!dateStr) return 'Never';
  return formatDate(dateStr);
}

export default function UsersPage() {
  const [users, setUsers] = useState([]);
  const [pagination, setPagination] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [role, setRole] = useState('all');
  const [status, setStatus] = useState('all');
  const [actionLoading, setActionLoading] = useState(null);
  const searchTimeout = useRef(null);
  const searchTerm = useRef('');

  const fetchUsers = useCallback(async (searchVal, pageNum, roleVal, statusVal) => {
    setLoading(true);
    setError('');
    try {
      const res = await userApi.findUsers({
        page: pageNum,
        pageSize: 20,
        role: roleVal !== 'all' ? roleVal : undefined,
        status: statusVal !== 'all' ? statusVal : undefined,
        search: searchVal || undefined,
      });
      setUsers(res.data?.items || []);
      setPagination(res.data?.pagination || null);
    } catch (err) {
      console.error('Failed to load users:', err);
      setError('Failed to load users');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUsers(searchTerm.current, page, role, status);
  }, [page, role, status, fetchUsers]);

  const handleSearchChange = (e) => {
    const val = e.target.value;
    setSearch(val);
    searchTerm.current = val;
    if (searchTimeout.current) clearTimeout(searchTimeout.current);
    searchTimeout.current = setTimeout(() => {
      setPage(1);
      fetchUsers(val, 1, role, status);
    }, 400);
  };

  const handleRoleChange = (newRole) => {
    setRole(newRole);
    setPage(1);
  };

  const handleStatusChange = (newStatus) => {
    setStatus(newStatus);
    setPage(1);
  };

  const handleToggleStatus = async (user) => {
    setActionLoading(user.id);
    try {
      if (user.status === 'suspended') {
        await userApi.activateUser({ userId: user.id });
        toast.success(`${user.fullName} activated`);
      } else {
        await userApi.suspendUser({ userId: user.id });
        toast.success(`${user.fullName} suspended`);
      }
      fetchUsers(searchTerm.current, page, role, status);
    } catch (err) {
      const msg = err?.response?.data?.error?.message || err?.message || 'Action failed';
      toast.error(msg);
    } finally {
      setActionLoading(null);
    }
  };

  const pageCount = pagination?.totalPages || 1;
  const hasPrev = page > 1;
  const hasNext = page < pageCount;

  return (
    <div className='space-y-8'>
      {/* Header */}
      <div className='text-center pt-8'>
        <h1 className='text-4xl font-serif font-black mb-2 text-primary tracking-tighter'>Users</h1>
        <p className='text-primary/40 font-bold italic text-sm'>
          {pagination ? `${pagination.totalItems} users total` : 'Manage user accounts'}
        </p>
      </div>

      {/* Top bar — filters + actions */}
      <div className='flex flex-wrap items-center justify-end gap-3'>
        <div className='flex p-1 bg-primary/5 rounded-2xl'>
          {ROLE_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => handleRoleChange(opt.value)}
              className={cn(
                'px-4 py-2 rounded-2xl text-xs font-bold uppercase tracking-widest transition-all',
                role === opt.value
                  ? 'bg-white shadow-sm text-primary'
                  : 'text-primary/40 hover:text-primary/60'
              )}>
              {opt.label}
            </button>
          ))}
        </div>
        <div className='flex p-1 bg-primary/5 rounded-2xl'>
          {STATUS_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => handleStatusChange(opt.value)}
              className={cn(
                'px-4 py-2 rounded-2xl text-xs font-bold uppercase tracking-widest transition-all',
                status === opt.value
                  ? 'bg-white shadow-sm text-primary'
                  : 'text-primary/40 hover:text-primary/60'
              )}>
              {opt.label}
            </button>
          ))}
        </div>
        <Link to='/admin/users/new'>
          <Button className='gap-2 font-sans font-bold uppercase tracking-[0.1em] bg-primary text-secondary rounded-2xl hover:scale-[1.02] active:scale-[0.98] transition-all'>
            <Plus className='w-4 h-4' />
            New Admin
          </Button>
        </Link>
      </div>

      {/* Search bar */}
      <div className='relative group'>
        <div className='absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none'>
          <Search className='w-5 h-5 text-primary/30 group-focus-within:text-primary transition-colors' />
        </div>
        <input
          type='text'
          value={search}
          onChange={handleSearchChange}
          placeholder='Search users by name or email...'
          className='w-full pl-12 pr-4 py-4 bg-white/40 border border-primary/5 rounded-2xl focus:outline-none focus:ring-2 focus:ring-primary/10 focus:border-primary/20 transition-all font-sans font-bold text-sm'
        />
      </div>

      {/* Error */}
      {error && (
        <div className='flex items-start gap-3 p-4 border bg-destructive/5 border-destructive/10 rounded-2xl animate-in slide-in-from-top-2'>
          <AlertCircle className='w-5 h-5 text-destructive shrink-0' />
          <p className='text-xs font-bold leading-relaxed text-destructive'>{error}</p>
        </div>
      )}

      {/* Table */}
      {loading ? (
        <div className='animate-pulse space-y-3'>
          {[...Array(8)].map((_, i) => (
            <div key={i} className='h-16 bg-primary/5 rounded-xl' />
          ))}
        </div>
      ) : (
        <>
          <div className='overflow-hidden bg-white border rounded-2xl border-primary/5'>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead className='w-24'>Role</TableHead>
                  <TableHead className='w-28'>Status</TableHead>
                  <TableHead className='w-32'>Last Login</TableHead>
                  <TableHead className='w-32'>Created</TableHead>
                  <TableHead className='w-28 text-right'>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {users.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className='py-16 text-center'>
                      <Users className='w-10 h-10 mx-auto mb-3 text-primary/20' />
                      <p className='font-serif text-lg italic text-primary/30'>No users found</p>
                    </TableCell>
                  </TableRow>
                ) : (
                  users.map((user) => (
                    <TableRow key={user.id}>
                      <TableCell>
                        <Link
                          to={`/admin/users/${user.id}`}
                          className='font-sans font-bold transition-colors text-primary hover:text-primary/70'>
                          {user.fullName}
                        </Link>
                      </TableCell>
                      <TableCell className='text-primary/60 text-sm'>{user.email}</TableCell>
                      <TableCell>
                        <RoleBadge role={user.role} />
                      </TableCell>
                      <TableCell>
                        <StatusBadge status={user.status} />
                      </TableCell>
                      <TableCell className='text-sm text-primary/40'>
                        {formatLastLogin(user.lastLoginAt)}
                      </TableCell>
                      <TableCell className='text-sm text-primary/40'>
                        {formatDate(user.createdAt)}
                      </TableCell>
                      <TableCell className='text-right'>
                        <div className='flex items-center justify-end gap-1'>
                          <Link to={`/admin/users/${user.id}`}>
                            <Button
                              variant='ghost'
                              size='icon'
                              className='w-8 h-8 rounded-2xl text-primary/40 hover:text-primary hover:bg-primary/5'>
                              <Eye className='w-4 h-4' />
                            </Button>
                          </Link>
                          {user.status !== 'suspended' && user.role !== 'admin' && (
                            <Button
                              variant='ghost'
                              size='icon'
                              onClick={() => handleToggleStatus(user)}
                              disabled={actionLoading === user.id}
                              className='w-8 h-8 rounded-2xl text-primary/40 hover:text-destructive hover:bg-destructive/5'>
                              {actionLoading === user.id ? (
                                <Loader2 className='w-4 h-4 animate-spin' />
                              ) : (
                                <Power className='w-4 h-4' />
                              )}
                            </Button>
                          )}
                          {user.status === 'suspended' && (
                            <Button
                              variant='ghost'
                              size='icon'
                              onClick={() => handleToggleStatus(user)}
                              disabled={actionLoading === user.id}
                              className='w-8 h-8 rounded-2xl text-primary/40 hover:text-primary hover:bg-primary/5'>
                              {actionLoading === user.id ? (
                                <Loader2 className='w-4 h-4 animate-spin' />
                              ) : (
                                <Power className='w-4 h-4' />
                              )}
                            </Button>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>

          {/* Pagination */}
          {pageCount > 1 && (
            <div className='flex items-center justify-between'>
              <p className='text-xs font-bold text-primary/40'>
                Page {page} of {pageCount}
              </p>
              <div className='flex items-center gap-2'>
                <Button
                  variant='outline'
                  size='sm'
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={!hasPrev}
                  className='gap-1 rounded-2xl text-xs font-bold uppercase tracking-widest'>
                  <ChevronLeft className='w-4 h-4' />
                  Prev
                </Button>
                <Button
                  variant='outline'
                  size='sm'
                  onClick={() => setPage((p) => Math.min(pageCount, p + 1))}
                  disabled={!hasNext}
                  className='gap-1 rounded-2xl text-xs font-bold uppercase tracking-widest'>
                  Next
                  <ChevronRight className='w-4 h-4' />
                </Button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
