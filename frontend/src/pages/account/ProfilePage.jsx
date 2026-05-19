import { Loader2, User, Calendar, UserCircle, AlertCircle } from 'lucide-react';
import React, { useState, useEffect, useRef } from 'react';
import { toast } from 'sonner';

import { AvatarUpload } from '@/components/account/avatar-upload';
import { useApiMutation } from '@/hooks/useApiMutation';
import { useApiQuery } from '@/hooks/useApiQuery';
import { userApi } from '@/lib/apiClient';

export default function ProfilePage() {
  const { data: profile, loading: profileLoading } = useApiQuery(() => userApi.getMe(), {
    select: (res) => res.data,
  });

  const [fullName, setFullName] = useState('');
  const [dateOfBirth, setDateOfBirth] = useState('');
  const [error, setError] = useState('');
  const initialized = useRef(false);

  useEffect(() => {
    if (profile && !initialized.current) {
      setFullName(profile.fullName || '');
      if (profile.dateOfBirth) {
        const d = new Date(profile.dateOfBirth);
        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        setDateOfBirth(`${year}-${month}-${day}`);
      } else {
        setDateOfBirth('');
      }
      initialized.current = true;
    }
  }, [profile]);

  const {
    mutate: updateProfile,
    loading: updating,
    error: mutationError,
  } = useApiMutation((variables) => userApi.updateProfile(variables), {
    onSuccess: () => {
      toast.success('Profile updated!');
      setError('');
    },
    onError: (err) => {
      const msg = err?.response?.data?.error?.message || err?.message || 'Failed to update profile';
      console.error('Profile update error:', err);
      setError(msg);
    },
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    setError('');

    if (fullName.trim().length < 2) {
      setError('Full name must be at least 2 characters');
      return;
    }

    const dobValue = dateOfBirth ? new Date(dateOfBirth + 'T00:00:00') : null;

    updateProfile({
      updateProfileRequest: {
        fullName: fullName.trim(),
        dateOfBirth: dobValue,
      },
    });
  };

  if (profileLoading) {
    return (
      <div className='animate-pulse space-y-6'>
        <div className='h-32 bg-primary/5 rounded-2xl' />
        <div className='h-48 bg-primary/5 rounded-2xl' />
      </div>
    );
  }

  return (
    <div className='space-y-8'>
      <div className='text-center pt-8'>
        <h1 className='text-4xl font-serif font-black mb-2 text-primary tracking-tighter'>
          Profile
        </h1>
        <p className='text-primary/40 font-bold italic text-sm'>Update your personal details</p>
      </div>

      <div className='max-w-lg mx-auto'>
        <form onSubmit={handleSubmit} className='space-y-5'>
          {/* Avatar */}
          <AvatarUpload currentAvatarUrl={profile?.avatarUrl} fullName={profile?.fullName} />

          {/* Full Name */}
          <div className='space-y-2'>
            <label className='block text-xs font-black uppercase tracking-[0.2em] text-primary/60 pl-1'>
              Full Name
            </label>
            <div className='relative group'>
              <div className='absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none'>
                <User className='w-5 h-5 text-primary/30 group-focus-within:text-primary transition-colors' />
              </div>
              <input
                type='text'
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder='Enter your full name'
                className='w-full pl-12 pr-4 py-4 bg-white/40 border border-primary/5 rounded-2xl focus:outline-none focus:ring-2 focus:ring-primary/10 focus:border-primary/20 transition-all font-sans font-bold'
              />
            </div>
          </div>

          {/* Date of Birth */}
          <div className='space-y-2'>
            <label className='block text-xs font-black uppercase tracking-[0.2em] text-primary/60 pl-1'>
              Date of Birth
            </label>
            <div className='relative group'>
              <div className='absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none'>
                <Calendar className='w-5 h-5 text-primary/30 group-focus-within:text-primary transition-colors' />
              </div>
              <input
                type='date'
                value={dateOfBirth}
                onChange={(e) => setDateOfBirth(e.target.value)}
                className='w-full pl-12 pr-4 py-4 bg-white/40 border border-primary/5 rounded-2xl focus:outline-none focus:ring-2 focus:ring-primary/10 focus:border-primary/20 transition-all font-sans font-bold'
              />
            </div>
          </div>

          {/* Error Message */}
          {(error || mutationError) && (
            <div className='flex items-start gap-3 p-4 duration-300 border bg-destructive/5 border-destructive/10 rounded-2xl animate-in slide-in-from-top-2'>
              <AlertCircle className='w-5 h-5 text-destructive shrink-0' />
              <p className='text-xs font-bold leading-relaxed text-destructive'>
                {error || mutationError?.message || 'An error occurred'}
              </p>
            </div>
          )}

          {/* Submit Button */}
          <button
            type='submit'
            disabled={updating}
            className='w-full py-5 bg-primary text-secondary rounded-2xl font-sans font-bold uppercase tracking-[0.2em] shadow-2xl hover:scale-[1.02] active:scale-[0.98] transition-all flex items-center justify-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100'>
            {updating ? (
              <Loader2 className='w-5 h-5 animate-spin' />
            ) : (
              <>
                <UserCircle className='w-5 h-5' />
                <span>Save Changes</span>
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
