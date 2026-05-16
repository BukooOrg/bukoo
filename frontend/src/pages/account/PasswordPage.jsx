import { Loader2, Eye, EyeOff } from 'lucide-react';
import React, { useState } from 'react';
import { toast } from 'sonner';

import { PasswordStrengthMeter } from '@/components/auth/password-strength-meter';
import { useApiMutation } from '@/hooks/useApiMutation';
import { userApi } from '@/lib/apiClient';

export default function PasswordPage() {
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showCurrent, setShowCurrent] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [error, setError] = useState('');

  const { mutate: changePassword, loading } = useApiMutation(
    (variables) => userApi.changePassword(variables),
    {
      onSuccess: () => {
        toast.success('Password changed successfully!');
        setCurrentPassword('');
        setNewPassword('');
        setConfirmPassword('');
        setError('');
      },
      onError: (err) => {
        setError(err.response?.data?.error?.message || 'Failed to change password');
      },
    }
  );

  const validatePassword = (pwd) => {
    if (pwd.length < 8) return 'Password must be at least 8 characters';
    if (!/[A-Z]/.test(pwd)) return 'Must contain an uppercase letter';
    if (!/[a-z]/.test(pwd)) return 'Must contain a lowercase letter';
    if (!/[0-9]/.test(pwd)) return 'Must contain a number';
    if (!/[^A-Za-z0-9]/.test(pwd)) return 'Must contain a special character';
    return '';
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    setError('');

    if (!currentPassword) {
      setError('Current password is required');
      return;
    }

    const pwdError = validatePassword(newPassword);
    if (pwdError) {
      setError(pwdError);
      return;
    }

    if (newPassword !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    changePassword({
      changePasswordRequest: {
        currentPassword,
        newPassword,
      },
    });
  };

  const pwdError = validatePassword(newPassword);

  return (
    <div className='space-y-8'>
      <div>
        <h1 className='font-serif text-3xl font-black text-primary'>Change Password</h1>
        <p className='text-sm text-muted-foreground mt-1'>Update your account password</p>
      </div>

      <form onSubmit={handleSubmit} className='space-y-6'>
        {/* Current Password */}
        <div className='space-y-2'>
          <label className='block text-xs font-black uppercase tracking-[0.2em] text-primary/60'>
            Current Password
          </label>
          <div className='relative'>
            <input
              type={showCurrent ? 'text' : 'password'}
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              className='w-full px-4 py-3 pr-12 bg-white border border-primary/10 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/10 focus:border-primary/20'
            />
            <button
              type='button'
              onClick={() => setShowCurrent(!showCurrent)}
              className='absolute right-4 top-1/2 -translate-y-1/2 text-primary/40 hover:text-primary'>
              {showCurrent ? <EyeOff className='w-5 h-5' /> : <Eye className='w-5 h-5' />}
            </button>
          </div>
        </div>

        {/* New Password */}
        <div className='space-y-2'>
          <label className='block text-xs font-black uppercase tracking-[0.2em] text-primary/60'>
            New Password
          </label>
          <div className='relative'>
            <input
              type={showNew ? 'text' : 'password'}
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className='w-full px-4 py-3 pr-12 bg-white border border-primary/10 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/10 focus:border-primary/20'
            />
            <button
              type='button'
              onClick={() => setShowNew(!showNew)}
              className='absolute right-4 top-1/2 -translate-y-1/2 text-primary/40 hover:text-primary'>
              {showNew ? <EyeOff className='w-5 h-5' /> : <Eye className='w-5 h-5' />}
            </button>
          </div>
          <PasswordStrengthMeter password={newPassword} />
        </div>

        {/* Confirm Password */}
        <div className='space-y-2'>
          <label className='block text-xs font-black uppercase tracking-[0.2em] text-primary/60'>
            Confirm New Password
          </label>
          <div className='relative'>
            <input
              type={showConfirm ? 'text' : 'password'}
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className='w-full px-4 py-3 pr-12 bg-white border border-primary/10 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/10 focus:border-primary/20'
            />
            <button
              type='button'
              onClick={() => setShowConfirm(!showConfirm)}
              className='absolute right-4 top-1/2 -translate-y-1/2 text-primary/40 hover:text-primary'>
              {showConfirm ? <EyeOff className='w-5 h-5' /> : <Eye className='w-5 h-5' />}
            </button>
          </div>
          {confirmPassword && confirmPassword !== newPassword && (
            <p className='text-xs font-bold text-destructive'>Passwords do not match</p>
          )}
        </div>

        {error && (
          <div className='p-4 border bg-destructive/5 border-destructive/10 rounded-xl'>
            <p className='text-xs font-bold text-destructive'>{error}</p>
          </div>
        )}

        <button
          type='submit'
          disabled={
            loading ||
            !currentPassword ||
            !newPassword ||
            !confirmPassword ||
            !!pwdError ||
            newPassword !== confirmPassword
          }
          className='w-full py-4 bg-primary text-secondary rounded-xl font-bold uppercase tracking-[0.2em] hover:scale-[1.02] active:scale-[0.98] transition-all flex items-center justify-center gap-3 disabled:opacity-50'>
          {loading ? <Loader2 className='w-5 h-5 animate-spin' /> : 'Change Password'}
        </button>
      </form>
    </div>
  );
}
