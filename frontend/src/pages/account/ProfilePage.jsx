import { Loader2 } from 'lucide-react';
import React, { useState, useEffect } from 'react';
import { toast } from 'sonner';

import { AvatarUpload } from '@/components/account/avatar-upload';
import { useApiMutation } from '@/hooks/useApiMutation';
import { useApiQuery } from '@/hooks/useApiQuery';
import { usersApi } from '@/lib/apiClient';

export default function ProfilePage() {
  const { data: profile, loading: profileLoading } = useApiQuery(() => usersApi.getMe(), {
    select: (res) => res.data,
  });

  const [fullName, setFullName] = useState('');
  const [dateOfBirth, setDateOfBirth] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    if (profile) {
      setFullName(profile.fullName || '');
      setDateOfBirth(profile.dateOfBirth || '');
    }
  }, [profile]);

  const { mutate: updateProfile, loading: updating } = useApiMutation(
    (variables) => usersApi.updateProfile(variables),
    {
      onSuccess: () => {
        toast.success('Profile updated!');
        setError('');
      },
      onError: (err) => {
        setError(err.response?.data?.error?.message || 'Failed to update profile');
      },
    }
  );

  const handleSubmit = (e) => {
    e.preventDefault();
    setError('');

    if (fullName.trim().length < 2) {
      setError('Full name must be at least 2 characters');
      return;
    }

    updateProfile({
      updateProfileRequest: {
        fullName: fullName.trim(),
        dateOfBirth: dateOfBirth || undefined,
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
      <div>
        <h1 className='font-serif text-3xl font-black text-primary'>Profile</h1>
        <p className='text-sm text-muted-foreground mt-1'>Update your personal details</p>
      </div>

      <form onSubmit={handleSubmit} className='space-y-8'>
        {/* Avatar */}
        <AvatarUpload currentAvatarUrl={profile?.avatarUrl} fullName={profile?.fullName} />

        {/* Full Name */}
        <div className='space-y-2'>
          <label className='block text-xs font-black uppercase tracking-[0.2em] text-primary/60'>
            Full Name
          </label>
          <input
            type='text'
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            className='w-full px-4 py-3 bg-white border border-primary/10 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/10 focus:border-primary/20'
          />
        </div>

        {/* Date of Birth */}
        <div className='space-y-2'>
          <label className='block text-xs font-black uppercase tracking-[0.2em] text-primary/60'>
            Date of Birth
          </label>
          <input
            type='date'
            value={dateOfBirth}
            onChange={(e) => setDateOfBirth(e.target.value)}
            className='w-full px-4 py-3 bg-white border border-primary/10 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/10 focus:border-primary/20'
          />
        </div>

        {error && (
          <div className='p-4 border bg-destructive/5 border-destructive/10 rounded-xl'>
            <p className='text-xs font-bold text-destructive'>{error}</p>
          </div>
        )}

        <button
          type='submit'
          disabled={updating}
          className='w-full py-4 bg-primary text-secondary rounded-xl font-bold uppercase tracking-[0.2em] hover:scale-[1.02] active:scale-[0.98] transition-all flex items-center justify-center gap-3 disabled:opacity-50'>
          {updating ? <Loader2 className='w-5 h-5 animate-spin' /> : 'Save Changes'}
        </button>
      </form>
    </div>
  );
}
