import { Loader2, MapPin, Phone, User, Building2, AlertCircle } from 'lucide-react';
import React, { useState, useEffect, useRef } from 'react';
import { toast } from 'sonner';

import { useApiMutation } from '@/hooks/useApiMutation';
import { useApiQuery } from '@/hooks/useApiQuery';
import { userApi } from '@/lib/apiClient';

const MALAYSIAN_STATES = [
  'Johor',
  'Kedah',
  'Kelantan',
  'Melaka',
  'Negeri Sembilan',
  'Pahang',
  'Perak',
  'Perlis',
  'Pulau Pinang',
  'Sabah',
  'Sarawak',
  'Selangor',
  'Terengganu',
  'W.P. Kuala Lumpur',
  'W.P. Labuan',
  'W.P. Putrajaya',
];

const PHONE_REGEX = /^(\+?60|0)[1-9]\d{7,9}$/;
const POSTCODE_REGEX = /^\d{5}$/;

export default function AddressPage() {
  const { data: address, loading: addressLoading } = useApiQuery(() => userApi.getMyAddress(), {
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
    country: 'Malaysia',
  });
  const [fieldErrors, setFieldErrors] = useState({});
  const [error, setError] = useState('');
  const initialized = useRef(false);

  useEffect(() => {
    if (address && !initialized.current) {
      setForm({
        recipientName: address.recipientName || '',
        phone: address.phone || '',
        addressLine1: address.addressLine1 || '',
        addressLine2: address.addressLine2 || '',
        city: address.city || '',
        state: address.state || '',
        postcode: address.postcode || '',
        country: address.country || 'Malaysia',
      });
      initialized.current = true;
    }
  }, [address]);

  const { mutate: saveAddress, loading: saving } = useApiMutation(
    (variables) => userApi.upsertAddress(variables),
    {
      onSuccess: () => {
        toast.success('Address saved!');
        setError('');
        setFieldErrors({});
      },
      onError: (err) => {
        const msg = err?.response?.data?.error?.message || err?.message || 'Failed to save address';
        console.error('Address save error:', err);
        setError(msg);
      },
    }
  );

  const handleChange = (field, value) => {
    setForm((prev) => ({ ...prev, [field]: value }));
    setFieldErrors((prev) => ({ ...prev, [field]: '' }));
    setError('');
  };

  const validateField = (field, value) => {
    switch (field) {
      case 'recipientName':
        if (!value.trim()) return 'Recipient name is required';
        if (value.trim().length < 2) return 'Name must be at least 2 characters';
        return '';
      case 'phone':
        if (!value.trim()) return 'Phone number is required';
        if (!PHONE_REGEX.test(value.replace(/[\s-]/g, '')))
          return 'Enter a valid Malaysian phone number';
        return '';
      case 'addressLine1':
        if (!value.trim()) return 'Address line is required';
        if (value.trim().length < 5) return 'Address must be at least 5 characters';
        return '';
      case 'city':
        if (!value.trim()) return 'City is required';
        if (value.trim().length < 2) return 'City must be at least 2 characters';
        return '';
      case 'state':
        if (!value) return 'Please select a state';
        return '';
      case 'postcode':
        if (!value.trim()) return 'Postcode is required';
        if (!POSTCODE_REGEX.test(value.trim())) return 'Postcode must be exactly 5 digits';
        return '';
      case 'country':
        if (!value.trim()) return 'Country is required';
        return '';
      default:
        return '';
    }
  };

  const handleBlur = (field) => {
    const err = validateField(field, form[field]);
    setFieldErrors((prev) => ({ ...prev, [field]: err }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    setError('');

    const requiredFields = [
      'recipientName',
      'phone',
      'addressLine1',
      'city',
      'state',
      'postcode',
      'country',
    ];
    const errors = {};
    let hasErrors = false;

    for (const field of requiredFields) {
      const err = validateField(field, form[field]);
      if (err) {
        errors[field] = err;
        hasErrors = true;
      }
    }

    if (hasErrors) {
      setFieldErrors(errors);
      setError('Please fix the errors below');
      return;
    }

    saveAddress({
      upsertAddressRequest: {
        recipientName: form.recipientName.trim(),
        phone: form.phone.trim(),
        addressLine1: form.addressLine1.trim(),
        addressLine2: form.addressLine2.trim() || undefined,
        city: form.city.trim(),
        state: form.state,
        postcode: form.postcode.trim(),
        country: form.country.trim(),
      },
    });
  };

  const inputClass = (field) =>
    `w-full px-4 py-4 bg-white/40 border rounded-2xl focus:outline-none focus:ring-2 focus:ring-primary/10 font-sans font-bold transition-all ${
      fieldErrors[field]
        ? 'border-destructive/40 focus:border-destructive/20'
        : 'border-primary/5 focus:border-primary/20'
    }`;

  if (addressLoading) {
    return (
      <div className='animate-pulse space-y-6'>
        <div className='h-8 w-48 bg-primary/5 rounded-2xl' />
        <div className='h-96 bg-primary/5 rounded-2xl' />
      </div>
    );
  }

  const fields = [
    {
      key: 'recipientName',
      label: 'Recipient Name',
      required: true,
      type: 'text',
      icon: User,
      placeholder: 'Enter recipient name',
    },
    {
      key: 'phone',
      label: 'Phone Number',
      required: true,
      type: 'tel',
      icon: Phone,
      placeholder: 'e.g. 012-3456789',
    },
    {
      key: 'addressLine1',
      label: 'Address Line 1',
      required: true,
      type: 'text',
      icon: MapPin,
      placeholder: 'Street address',
    },
    {
      key: 'addressLine2',
      label: 'Address Line 2',
      required: false,
      type: 'text',
      icon: MapPin,
      placeholder: 'Apartment, suite, etc.',
    },
    {
      key: 'city',
      label: 'City',
      required: true,
      type: 'text',
      icon: Building2,
      placeholder: 'Enter city',
    },
    { key: 'state', label: 'State', required: true, type: 'select' },
    {
      key: 'postcode',
      label: 'Postcode',
      required: true,
      type: 'text',
      maxLength: 5,
      placeholder: '5 digits',
    },
    {
      key: 'country',
      label: 'Country',
      required: true,
      type: 'text',
      placeholder: 'Enter country',
    },
  ];

  return (
    <div className='space-y-8'>
      <div className='text-center pt-8'>
        <h1 className='text-4xl font-serif font-black mb-2 text-primary tracking-tighter'>
          Shipping Address
        </h1>
        <p className='text-primary/40 font-bold italic text-sm'>Manage your delivery address</p>
      </div>

      <div className='max-w-3xl mx-auto'>
        <form onSubmit={handleSubmit} className='space-y-5'>
          <div className='grid grid-cols-1 md:grid-cols-2 gap-4'>
            {fields.map((field) => (
              <div key={field.key} className='space-y-2'>
                <label className='block text-xs font-black uppercase tracking-[0.2em] text-primary/60 pl-1'>
                  {field.label} {field.required && <span className='text-destructive'>*</span>}
                </label>

                {field.type === 'select' ? (
                  <select
                    value={form[field.key]}
                    onChange={(e) => handleChange(field.key, e.target.value)}
                    onBlur={() => handleBlur(field.key)}
                    className={inputClass(field.key)}>
                    <option value=''>Select a state</option>
                    {MALAYSIAN_STATES.map((state) => (
                      <option key={state} value={state}>
                        {state}
                      </option>
                    ))}
                  </select>
                ) : (
                  <div className='relative group'>
                    {field.icon && (
                      <div className='absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none'>
                        <field.icon className='w-5 h-5 text-primary/30 group-focus-within:text-primary transition-colors' />
                      </div>
                    )}
                    <input
                      type={field.type}
                      value={form[field.key]}
                      maxLength={field.maxLength}
                      placeholder={field.placeholder}
                      onChange={(e) => handleChange(field.key, e.target.value)}
                      onBlur={() => handleBlur(field.key)}
                      className={
                        field.icon ? `pl-12 pr-4 ${inputClass(field.key)}` : inputClass(field.key)
                      }
                    />
                  </div>
                )}

                {fieldErrors[field.key] && (
                  <p className='text-xs font-bold text-destructive pl-1'>
                    {fieldErrors[field.key]}
                  </p>
                )}
              </div>
            ))}
          </div>

          {/* Error Message */}
          {(error || Object.keys(fieldErrors).length > 0) && (
            <div className='flex items-start gap-3 p-4 duration-300 border bg-destructive/5 border-destructive/10 rounded-2xl animate-in slide-in-from-top-2'>
              <AlertCircle className='w-5 h-5 text-destructive shrink-0' />
              <p className='text-xs font-bold leading-relaxed text-destructive'>
                {error || 'Please fix the errors above'}
              </p>
            </div>
          )}

          {/* Submit Button */}
          <button
            type='submit'
            disabled={saving}
            className='w-full py-5 bg-primary text-secondary rounded-2xl font-sans font-bold uppercase tracking-[0.2em] shadow-2xl hover:scale-[1.02] active:scale-[0.98] transition-all flex items-center justify-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100'>
            {saving ? (
              <Loader2 className='w-5 h-5 animate-spin' />
            ) : (
              <>
                <MapPin className='w-5 h-5' />
                <span>Save Address</span>
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
