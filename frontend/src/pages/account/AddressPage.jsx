import { Loader2 } from 'lucide-react';
import React, { useState, useEffect } from 'react';
import { toast } from 'sonner';

import { useApiMutation, useApiQuery } from '@/hooks/useApiMutation';
import { usersApi } from '@/lib/apiClient';

export default function AddressPage() {
  const { data: address, loading: addressLoading } = useApiQuery(() => usersApi.getMyAddress(), {
    select: (res) => res.data,
    skipOnError: true,
  });

  const [form, setForm] = useState({
    recipientName: '',
    phone: '',
    addressLine1: '',
    addressLine2: '',
    city: '',
    state: '',
    postcode: '',
    country: '',
  });
  const [error, setError] = useState('');

  useEffect(() => {
    if (address) {
      setForm({
        recipientName: address.recipientName || '',
        phone: address.phone || '',
        addressLine1: address.addressLine1 || '',
        addressLine2: address.addressLine2 || '',
        city: address.city || '',
        state: address.state || '',
        postcode: address.postcode || '',
        country: address.country || '',
      });
    }
  }, [address]);

  const { mutate: saveAddress, loading: saving } = useApiMutation(
    (variables) => usersApi.upsertAddress(variables),
    {
      onSuccess: () => {
        toast.success('Address saved!');
        setError('');
      },
      onError: (err) => {
        setError(err.response?.data?.error?.message || 'Failed to save address');
      },
    }
  );

  const handleChange = (field, value) => {
    setForm((prev) => ({ ...prev, [field]: value }));
    setError('');
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    setError('');

    const required = [
      'recipientName',
      'phone',
      'addressLine1',
      'city',
      'state',
      'postcode',
      'country',
    ];
    for (const field of required) {
      if (!form[field].trim()) {
        setError(`${field.replace(/([A-Z])/g, ' $1').trim()} is required`);
        return;
      }
    }

    saveAddress({
      upsertAddressRequest: {
        recipientName: form.recipientName.trim(),
        phone: form.phone.trim(),
        addressLine1: form.addressLine1.trim(),
        addressLine2: form.addressLine2.trim() || undefined,
        city: form.city.trim(),
        state: form.state.trim(),
        postcode: form.postcode.trim(),
        country: form.country.trim(),
      },
    });
  };

  if (addressLoading) {
    return (
      <div className='animate-pulse space-y-6'>
        <div className='h-8 w-48 bg-primary/5 rounded-lg' />
        <div className='h-96 bg-primary/5 rounded-2xl' />
      </div>
    );
  }

  const fields = [
    { key: 'recipientName', label: 'Recipient Name', required: true },
    { key: 'phone', label: 'Phone Number', required: true },
    { key: 'addressLine1', label: 'Address Line 1', required: true },
    { key: 'addressLine2', label: 'Address Line 2', required: false },
    { key: 'city', label: 'City', required: true },
    { key: 'state', label: 'State', required: true },
    { key: 'postcode', label: 'Postcode', required: true },
    { key: 'country', label: 'Country', required: true },
  ];

  return (
    <div className='space-y-8'>
      <div>
        <h1 className='font-serif text-3xl font-black text-primary'>Shipping Address</h1>
        <p className='text-sm text-muted-foreground mt-1'>Manage your delivery address</p>
      </div>

      <form onSubmit={handleSubmit} className='space-y-6'>
        <div className='grid grid-cols-1 md:grid-cols-2 gap-4'>
          {fields.map((field) => (
            <div key={field.key} className='space-y-2'>
              <label className='block text-xs font-black uppercase tracking-[0.2em] text-primary/60'>
                {field.label} {field.required && <span className='text-destructive'>*</span>}
              </label>
              <input
                type='text'
                value={form[field.key]}
                onChange={(e) => handleChange(field.key, e.target.value)}
                className='w-full px-4 py-3 bg-white border border-primary/10 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/10 focus:border-primary/20'
              />
            </div>
          ))}
        </div>

        {error && (
          <div className='p-4 border bg-destructive/5 border-destructive/10 rounded-xl'>
            <p className='text-xs font-bold text-destructive'>{error}</p>
          </div>
        )}

        <button
          type='submit'
          disabled={saving}
          className='w-full py-4 bg-primary text-secondary rounded-xl font-bold uppercase tracking-[0.2em] hover:scale-[1.02] active:scale-[0.98] transition-all flex items-center justify-center gap-3 disabled:opacity-50'>
          {saving ? <Loader2 className='w-5 h-5 animate-spin' /> : 'Save Address'}
        </button>
      </form>
    </div>
  );
}
