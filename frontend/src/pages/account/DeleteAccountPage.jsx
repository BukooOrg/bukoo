import { AlertTriangle, Loader2 } from 'lucide-react';
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';

import { useAuth } from '@/context/AuthContext';
import { useApiMutation } from '@/hooks/useApiMutation';
import { userApi } from '@/lib/apiClient';

export default function DeleteAccountPage() {
  const navigate = useNavigate();
  const { logout } = useAuth();
  const [confirmation, setConfirmation] = useState('');
  const [error, setError] = useState('');

  const { mutate: deleteAccount, loading } = useApiMutation(() => userApi.softDeleteMe(), {
    onSuccess: () => {
      toast.success('Account deleted successfully');
      logout();
      navigate('/');
    },
    onError: (err) => {
      setError(err.response?.data?.error?.message || 'Failed to delete account');
    },
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    setError('');

    if (confirmation !== 'DELETE') {
      setError('Please type DELETE to confirm');
      return;
    }

    deleteAccount();
  };

  const isDisabled = confirmation !== 'DELETE' || loading;

  return (
    <div className='space-y-8'>
      <div className='text-center'>
        <div className='flex justify-center mb-4'>
          <div className='w-14 h-14 bg-destructive/5 rounded-full flex items-center justify-center'>
            <AlertTriangle className='w-7 h-7 text-destructive' />
          </div>
        </div>
        <h1 className='text-4xl font-serif font-black mb-2 text-destructive tracking-tighter'>
          Delete Account
        </h1>
        <p className='text-primary/40 font-bold italic text-sm'>This action cannot be undone</p>
      </div>

      <div className='p-6 rounded-2xl border border-destructive/20 bg-destructive/5'>
        <div className='flex items-start gap-4'>
          <AlertTriangle className='w-8 h-8 text-destructive shrink-0 mt-1' />
          <div>
            <h3 className='font-bold text-destructive mb-2'>Warning</h3>
            <ul className='text-sm text-destructive/80 space-y-1'>
              <li>• All your personal data will be permanently deleted</li>
              <li>• Your order history will be lost</li>
              <li>• Your reviews and wishlist will be removed</li>
              <li>• This action cannot be reversed</li>
            </ul>
          </div>
        </div>
      </div>

      <form onSubmit={handleSubmit} className='space-y-6'>
        <div className='space-y-2'>
          <label className='block text-xs font-black uppercase tracking-[0.2em] text-primary/60'>
            Type <span className='text-destructive'>DELETE</span> to confirm
          </label>
          <input
            type='text'
            value={confirmation}
            onChange={(e) => setConfirmation(e.target.value)}
            className='w-full px-4 py-4 bg-white border border-destructive/30 rounded-2xl focus:outline-none focus:ring-2 focus:ring-destructive/10 focus:border-destructive/20 font-sans font-bold'
            placeholder='DELETE'
          />
        </div>

        {error && (
          <div className='p-4 border bg-destructive/5 border-destructive/10 rounded-2xl'>
            <p className='text-xs font-bold text-destructive'>{error}</p>
          </div>
        )}

        <button
          type='submit'
          disabled={isDisabled}
          className='w-full py-5 bg-destructive text-white rounded-2xl font-sans font-bold uppercase tracking-[0.2em] shadow-2xl hover:scale-[1.02] active:scale-[0.98] transition-all flex items-center justify-center gap-3 disabled:opacity-50 disabled:hover:scale-100'>
          {loading ? (
            <Loader2 className='w-5 h-5 animate-spin' />
          ) : (
            <>
              <AlertTriangle className='w-5 h-5' />
              <span>Permanently Delete Account</span>
            </>
          )}
        </button>
      </form>
    </div>
  );
}
