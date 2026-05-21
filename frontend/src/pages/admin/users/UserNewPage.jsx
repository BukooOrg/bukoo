import {
  UserPlus,
  Mail,
  Shield,
  Calendar,
  Loader2,
  AlertCircle,
  ArrowLeft,
  Eye,
  EyeOff,
} from 'lucide-react';
import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { toast } from 'sonner';

import { PasswordStrengthMeter } from '@/components/auth/password-strength-meter';
import { userApi } from '@/lib/apiClient';

export default function UserNewPage() {
  const navigate = useNavigate();

  // Form state
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [dateOfBirth, setDateOfBirth] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  // Submit state
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!email.trim()) {
      setError('Email is required');
      return;
    }
    if (!password) {
      setError('Password is required');
      return;
    }
    if (password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }
    if (!fullName.trim()) {
      setError('Full name is required');
      return;
    }

    setSubmitting(true);
    try {
      const res = await userApi.registerAdmin({
        registerAdminRequest: {
          email: email.trim(),
          password,
          fullName: fullName.trim(),
          dateOfBirth: dateOfBirth ? new Date(dateOfBirth + 'T00:00:00') : undefined,
        },
      });

      const user = res.data;
      toast.success(`"${user.fullName}" created!`);
      navigate(`/admin/users/${user.id}`);
    } catch (err) {
      let msg = 'Failed to create admin user';
      try {
        const res = err?.response;
        if (res) {
          const text = await res.clone().text();
          try {
            const body = JSON.parse(text);
            if (body?.error?.message) {
              msg = body.error.message;
            } else if (body?.detail) {
              msg = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail);
            }
          } catch {
            msg = text || err?.message || msg;
          }
        } else {
          msg = err?.message || msg;
        }
      } catch {
        msg = err?.message || msg;
      }
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const inputClass =
    'w-full pl-12 pr-4 py-4 bg-white/40 border border-primary/5 rounded-2xl focus:outline-none focus:ring-2 focus:ring-primary/10 focus:border-primary/20 transition-all font-sans font-bold text-sm';

  return (
    <div className='space-y-8 '>
      <Link
        to='/admin/users'
        className='inline-flex items-center gap-2 text-xs font-sans font-black uppercase tracking-widest text-primary/40 hover:text-primary transition-colors'>
        <ArrowLeft className='w-4 h-4' />
        Back to Users
      </Link>

      <div className='text-center pt-8'>
        <h1 className='text-4xl font-serif font-black mb-2 text-primary tracking-tighter'>
          New Admin
        </h1>
        <p className='text-primary/40 font-bold italic text-sm'>Register a new admin account</p>
      </div>

      <form onSubmit={handleSubmit} className='space-y-5'>
        {/* Email */}
        <div className='space-y-2'>
          <label className='block text-xs font-black uppercase tracking-[0.2em] text-primary/60 pl-1'>
            Email <span className='text-destructive'>*</span>
          </label>
          <div className='relative group'>
            <div className='absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none'>
              <Mail className='w-5 h-5 text-primary/30 group-focus-within:text-primary transition-colors' />
            </div>
            <input
              type='email'
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder='admin@example.com'
              className={inputClass}
            />
          </div>
        </div>

        {/* Password */}
        <div className='space-y-2'>
          <label className='block text-xs font-black uppercase tracking-[0.2em] text-primary/60 pl-1'>
            Password <span className='text-destructive'>*</span>
          </label>
          <div className='relative group'>
            <div className='absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none'>
              <Shield className='w-5 h-5 text-primary/30 group-focus-within:text-primary transition-colors' />
            </div>
            <input
              type={showPassword ? 'text' : 'password'}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder='Enter password'
              className={`${inputClass} pr-12`}
            />
            <button
              type='button'
              onClick={() => setShowPassword(!showPassword)}
              className='absolute inset-y-0 right-0 pr-4 flex items-center text-primary/30 hover:text-primary transition-colors'>
              {showPassword ? <EyeOff className='w-5 h-5' /> : <Eye className='w-5 h-5' />}
            </button>
          </div>
          <PasswordStrengthMeter password={password} />
        </div>

        {/* Full Name */}
        <div className='space-y-2'>
          <label className='block text-xs font-black uppercase tracking-[0.2em] text-primary/60 pl-1'>
            Full Name <span className='text-destructive'>*</span>
          </label>
          <div className='relative group'>
            <div className='absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none'>
              <UserPlus className='w-5 h-5 text-primary/30 group-focus-within:text-primary transition-colors' />
            </div>
            <input
              type='text'
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder='John Doe'
              className={inputClass}
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
              className={inputClass}
            />
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className='flex items-start gap-3 p-4 border bg-destructive/5 border-destructive/10 rounded-2xl animate-in slide-in-from-top-2'>
            <AlertCircle className='w-5 h-5 text-destructive shrink-0' />
            <p className='text-xs font-bold leading-relaxed text-destructive'>{error}</p>
          </div>
        )}

        {/* Submit */}
        <button
          type='submit'
          disabled={submitting}
          className='w-full py-5 bg-primary text-secondary rounded-2xl font-sans font-bold uppercase tracking-[0.2em] shadow-2xl hover:scale-[1.02] active:scale-[0.98] transition-all flex items-center justify-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100'>
          {submitting ? (
            <Loader2 className='w-5 h-5 animate-spin' />
          ) : (
            <>
              <UserPlus className='w-5 h-5' />
              <span>Create Admin</span>
            </>
          )}
        </button>
      </form>
    </div>
  );
}
