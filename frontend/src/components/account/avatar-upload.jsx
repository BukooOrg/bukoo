import { Camera, Trash2, Loader2 } from 'lucide-react';
import React, { useRef, useState } from 'react';
import { toast } from 'sonner';

import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/data-display/avatar';
import { useApiMutation } from '@/hooks/useApiMutation';
import { uploadAvatar, userApi } from '@/lib/apiClient';
import { cn } from '@/lib/utils';

export function AvatarUpload({ currentAvatarUrl, fullName, onAvatarChange }) {
  const fileInputRef = useRef(null);
  const [preview, setPreview] = useState(currentAvatarUrl);

  const { mutate: upload, loading: uploading } = useApiMutation((file) => uploadAvatar(file), {
    onSuccess: (data) => {
      setPreview(data.avatar_url ? `${data.avatar_url}?t=${Date.now()}` : null);
      onAvatarChange?.(data);
      toast.success('Avatar updated!');
    },
    onError: () => toast.error('Failed to upload avatar'),
  });

  const { mutate: removeAvatar, loading: removing } = useApiMutation(() => userApi.removeAvatar(), {
    onSuccess: (data) => {
      setPreview(null);
      onAvatarChange?.(data.data);
      toast.success('Avatar removed');
    },
    onError: () => toast.error('Failed to remove avatar'),
  });

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      toast.error('Please select an image file');
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      toast.error('Image must be less than 5MB');
      return;
    }

    upload(file);
  };

  const loading = uploading || removing;

  return (
    <div className='flex items-center gap-6'>
      <div className='relative group'>
        <Avatar className={cn('w-24 h-24 border-2 border-primary/20', loading && 'opacity-50')}>
          <AvatarImage src={preview} alt={fullName} />
          <AvatarFallback className='text-2xl font-bold bg-primary text-background'>
            {fullName?.charAt(0)?.toUpperCase() ?? 'U'}
          </AvatarFallback>
        </Avatar>

        {!loading && (
          <button
            type='button'
            onClick={() => fileInputRef.current?.click()}
            className='absolute inset-0 flex items-center justify-center transition-opacity rounded-full opacity-0 bg-primary/40 group-hover:opacity-100'>
            <Camera className='w-6 h-6 text-secondary' />
          </button>
        )}

        {loading && (
          <div className='absolute inset-0 flex items-center justify-center'>
            <Loader2 className='w-6 h-6 animate-spin text-primary' />
          </div>
        )}

        <input
          ref={fileInputRef}
          type='file'
          accept='image/*'
          onChange={handleFileChange}
          className='hidden'
        />
      </div>

      <div className='space-y-2'>
        <p className='text-sm font-bold text-primary'>Profile Photo</p>
        <p className='text-xs text-muted-foreground'>
          Click the photo to upload. PNG, JPG up to 5MB.
        </p>
        {preview && (
          <button
            type='button'
            onClick={() => removeAvatar()}
            disabled={loading}
            className='flex items-center gap-2 text-xs font-bold text-destructive hover:underline disabled:opacity-50'>
            <Trash2 className='w-4 h-4' />
            Remove Photo
          </button>
        )}
      </div>
    </div>
  );
}
