import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';

import { useAuth } from '@/context/AuthContext';

export function AdminRoute() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className='flex items-center justify-center min-h-screen'>
        <div className='w-8 h-8 border-4 rounded-full border-primary/20 border-t-primary animate-spin' />
      </div>
    );
  }

  if (!user) {
    return <Navigate to='/login' replace />;
  }

  if (user?.role !== 'admin') {
    return <Navigate to='/' replace />;
  }

  return <Outlet />;
}
