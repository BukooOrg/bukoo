import {
  ArrowLeft,
  Loader2,
  AlertCircle,
  Shield,
  Mail,
  Calendar,
  Clock,
  Power,
  Key,
  Trash2,
  Eye,
  EyeOff,
} from 'lucide-react';
import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { toast } from 'sonner';

import { RoleBadge, StatusBadge } from '@/components/admin/users/UserStatusBadge';
import { PasswordStrengthMeter } from '@/components/auth/password-strength-meter';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/feedback/alert-dialog';
import { DetailSkeleton } from '@/components/ui/feedback/page-skeleton';
import { Button } from '@/components/ui/forms/button';
import { BreadcrumbNav } from '@/components/ui/navigation/breadcrumb-nav';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/overlays/dialog';
import { userApi } from '@/lib/apiClient';

function formatDate(dateStr) {
  if (!dateStr) return '—';
  return new Date(dateStr).toLocaleDateString('en-MY', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export default function UserDetailPage() {
  const { userId } = useParams();
  const navigate = useNavigate();

  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Action dialogs
  const [suspendDialog, setSuspendDialog] = useState(false);
  const [activateDialog, setActivateDialog] = useState(false);
  const [deleteDialog, setDeleteDialog] = useState(false);
  const [resetDialog, setResetDialog] = useState(false);

  // Action loading states
  const [actionLoading, setActionLoading] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);

  // Password reset form
  const [newPassword, setNewPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  useEffect(() => {
    async function loadUser() {
      setLoading(true);
      setError('');
      try {
        const res = await userApi.viewUserProfile({ userId });
        setUser(res.data);
      } catch (err) {
        console.error('Failed to load user:', err);
        setError('Failed to load user profile');
      } finally {
        setLoading(false);
      }
    }
    loadUser();
  }, [userId]);

  const handleSuspend = async () => {
    setActionLoading(true);
    try {
      await userApi.suspendUser({ userId });
      toast.success(`${user.fullName} suspended`);
      setUser((prev) => ({ ...prev, status: 'suspended' }));
      setSuspendDialog(false);
    } catch (err) {
      const msg = err?.response?.data?.error?.message || err?.message || 'Suspend failed';
      toast.error(msg);
    } finally {
      setActionLoading(false);
    }
  };

  const handleActivate = async () => {
    setActionLoading(true);
    try {
      await userApi.activateUser({ userId });
      toast.success(`${user.fullName} activated`);
      setUser((prev) => ({ ...prev, status: 'active' }));
      setActivateDialog(false);
    } catch (err) {
      const msg = err?.response?.data?.error?.message || err?.message || 'Activate failed';
      toast.error(msg);
    } finally {
      setActionLoading(false);
    }
  };

  const handleDelete = async () => {
    setDeleteLoading(true);
    try {
      await userApi.softDeleteUser({ userId });
      toast.success(`${user.fullName} deleted`);
      setDeleteDialog(false);
      navigate('/admin/users');
    } catch (err) {
      const msg = err?.response?.data?.error?.message || err?.message || 'Delete failed';
      toast.error(msg);
    } finally {
      setDeleteLoading(false);
    }
  };

  const handleResetPassword = async () => {
    if (!newPassword) {
      toast.error('Password is required');
      return;
    }
    setActionLoading(true);
    try {
      await userApi.forceSetUserPassword({
        userId,
        forceSetUserPasswordRequest: { newPassword },
      });
      toast.success(`Password reset for ${user.fullName}`);
      setResetDialog(false);
      setNewPassword('');
    } catch (err) {
      const msg = err?.response?.data?.error?.message || err?.message || 'Password reset failed';
      toast.error(msg);
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return <DetailSkeleton sections={2} />;
  }

  if (error || !user) {
    return (
      <div className='space-y-8'>
        <Link
          to='/admin/users'
          className='inline-flex items-center gap-2 text-xs font-sans font-black uppercase tracking-widest text-primary/40 hover:text-primary transition-colors'>
          <ArrowLeft className='w-4 h-4' />
          Back to Users
        </Link>
        <div className='flex items-start gap-3 p-4 border bg-destructive/5 border-destructive/10 rounded-2xl'>
          <AlertCircle className='w-5 h-5 text-destructive shrink-0' />
          <p className='text-xs font-bold leading-relaxed text-destructive'>
            {error || 'User not found'}
          </p>
        </div>
      </div>
    );
  }

  const canSuspend = user.status !== 'suspended' && user.role !== 'admin';
  const canActivate = user.status === 'suspended';
  const isViewingAdmin = user.role === 'admin';

  return (
    <div className='space-y-8 '>
      <BreadcrumbNav />

      <Link
        to='/admin/users'
        className='inline-flex items-center gap-2 text-xs font-sans font-black uppercase tracking-widest text-primary/40 hover:text-primary transition-colors'>
        <ArrowLeft className='w-4 h-4' />
        Back to Users
      </Link>

      {/* Header */}
      <div className='text-center pt-8'>
        <h1 className='text-4xl font-serif font-black mb-2 text-primary tracking-tighter'>
          {user.fullName}
        </h1>
        <div className='flex items-center justify-center gap-3'>
          <RoleBadge role={user.role} />
          <StatusBadge status={user.status} />
        </div>
      </div>

      {/* Profile Details */}
      <div className='grid grid-cols-1 md:grid-cols-2 gap-6'>
        <div className='space-y-6'>
          <div className='p-6 bg-white/40 border border-primary/5 rounded-2xl'>
            <h3 className='text-xs font-black uppercase tracking-[0.2em] text-primary/60 mb-4'>
              Account Info
            </h3>
            <div className='space-y-4'>
              <div className='flex items-start gap-3'>
                <Mail className='w-5 h-5 text-primary/30 shrink-0 mt-0.5' />
                <div>
                  <p className='text-xs font-bold text-primary/40'>Email</p>
                  <p className='text-sm font-sans font-bold text-primary'>{user.email}</p>
                </div>
              </div>
              <div className='flex items-start gap-3'>
                <Shield className='w-5 h-5 text-primary/30 shrink-0 mt-0.5' />
                <div>
                  <p className='text-xs font-bold text-primary/40'>Role</p>
                  <p className='text-sm font-sans font-bold text-primary capitalize'>{user.role}</p>
                </div>
              </div>
              <div className='flex items-start gap-3'>
                <Calendar className='w-5 h-5 text-primary/30 shrink-0 mt-0.5' />
                <div>
                  <p className='text-xs font-bold text-primary/40'>Date of Birth</p>
                  <p className='text-sm font-sans font-bold text-primary'>
                    {formatDate(user.dateOfBirth)}
                  </p>
                </div>
              </div>
              <div className='flex items-start gap-3'>
                <Eye className='w-5 h-5 text-primary/30 shrink-0 mt-0.5' />
                <div>
                  <p className='text-xs font-bold text-primary/40'>Has Password</p>
                  <p className='text-sm font-sans font-bold text-primary'>
                    {user.havePassword ? 'Yes' : 'No'}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className='space-y-6'>
          <div className='p-6 bg-white/40 border border-primary/5 rounded-2xl'>
            <h3 className='text-xs font-black uppercase tracking-[0.2em] text-primary/60 mb-4'>
              Activity
            </h3>
            <div className='space-y-4'>
              <div className='flex items-start gap-3'>
                <Clock className='w-5 h-5 text-primary/30 shrink-0 mt-0.5' />
                <div>
                  <p className='text-xs font-bold text-primary/40'>Last Login</p>
                  <p className='text-sm font-sans font-bold text-primary'>
                    {formatDate(user.lastLoginAt)}
                  </p>
                </div>
              </div>
              <div className='flex items-start gap-3'>
                <Calendar className='w-5 h-5 text-primary/30 shrink-0 mt-0.5' />
                <div>
                  <p className='text-xs font-bold text-primary/40'>Created</p>
                  <p className='text-sm font-sans font-bold text-primary'>
                    {formatDate(user.createdAt)}
                  </p>
                </div>
              </div>
              <div className='flex items-start gap-3'>
                <Calendar className='w-5 h-5 text-primary/30 shrink-0 mt-0.5' />
                <div>
                  <p className='text-xs font-bold text-primary/40'>Last Updated</p>
                  <p className='text-sm font-sans font-bold text-primary'>
                    {formatDate(user.updatedAt)}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Actions */}
      {(canSuspend || canActivate || !isViewingAdmin) && (
        <div className='p-6 bg-white/40 border border-primary/5 rounded-2xl'>
          <h3 className='text-xs font-black uppercase tracking-[0.2em] text-primary/60 mb-4'>
            Actions
          </h3>
          <div className='flex flex-wrap gap-3'>
            {canSuspend && (
              <Button
                variant='outline'
                onClick={() => setSuspendDialog(true)}
                className='gap-2 rounded-2xl text-xs font-bold uppercase tracking-widest border-destructive/20 text-destructive hover:bg-destructive/5'>
                <Power className='w-4 h-4' />
                Suspend User
              </Button>
            )}
            {canActivate && (
              <Button
                variant='outline'
                onClick={() => setActivateDialog(true)}
                className='gap-2 rounded-2xl text-xs font-bold uppercase tracking-widest border-primary/20 text-primary hover:bg-primary/5'>
                <Power className='w-4 h-4' />
                Activate User
              </Button>
            )}
            {!isViewingAdmin && (
              <Button
                variant='outline'
                onClick={() => setResetDialog(true)}
                className='gap-2 rounded-2xl text-xs font-bold uppercase tracking-widest border-primary/20 text-primary hover:bg-primary/5'>
                <Key className='w-4 h-4' />
                Reset Password
              </Button>
            )}
            {!isViewingAdmin && (
              <Button
                variant='outline'
                onClick={() => setDeleteDialog(true)}
                className='gap-2 rounded-2xl text-xs font-bold uppercase tracking-widest border-destructive/20 text-destructive hover:bg-destructive/5'>
                <Trash2 className='w-4 h-4' />
                Delete User
              </Button>
            )}
          </div>
        </div>
      )}

      {/* Suspend Dialog */}
      <AlertDialog open={suspendDialog} onOpenChange={setSuspendDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Suspend User?</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to suspend {user.fullName}? They will not be able to log in to
              their account.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleSuspend}
              disabled={actionLoading}
              className='bg-destructive text-secondary'>
              {actionLoading ? <Loader2 className='w-4 h-4 animate-spin' /> : 'Suspend User'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Activate Dialog */}
      <AlertDialog open={activateDialog} onOpenChange={setActivateDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Activate User?</AlertDialogTitle>
            <AlertDialogDescription>
              Activate {user.fullName}? They will regain access to their account.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleActivate} disabled={actionLoading}>
              {actionLoading ? <Loader2 className='w-4 h-4 animate-spin' /> : 'Activate User'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Delete Dialog */}
      <AlertDialog open={deleteDialog} onOpenChange={setDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className='text-destructive'>Delete User?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently delete {user.fullName} and all associated data. This action
              cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              disabled={deleteLoading}
              className='bg-destructive text-secondary'>
              {deleteLoading ? <Loader2 className='w-4 h-4 animate-spin' /> : 'Delete User'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Password Reset Dialog */}
      <Dialog open={resetDialog} onOpenChange={setResetDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Force Password Reset</DialogTitle>
          </DialogHeader>
          <div className='space-y-4 py-4'>
            <p className='text-sm text-primary/60'>
              This will immediately reset the password for {user.fullName}.
            </p>
            <div className='relative'>
              <input
                type={showPassword ? 'text' : 'password'}
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder='Enter new password'
                className='w-full px-4 py-4 bg-white/40 border border-primary/5 rounded-2xl focus:outline-none focus:ring-2 focus:ring-primary/10 focus:border-primary/20 transition-all font-sans font-bold text-sm pr-12'
              />
              <button
                type='button'
                onClick={() => setShowPassword(!showPassword)}
                className='absolute inset-y-0 right-0 pr-4 flex items-center text-primary/30 hover:text-primary transition-colors'>
                {showPassword ? <EyeOff className='w-5 h-5' /> : <Eye className='w-5 h-5' />}
              </button>
            </div>
            <PasswordStrengthMeter password={newPassword} />
          </div>
          <DialogFooter>
            <Button variant='outline' onClick={() => setResetDialog(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleResetPassword}
              disabled={actionLoading || !newPassword}
              className='text-white'>
              {actionLoading ? <Loader2 className='w-4 h-4 animate-spin' /> : 'Reset Password'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
