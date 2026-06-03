import { motion } from 'motion/react';
import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';

import { useAuth } from '@/context/AuthContext';

export function CustomerRoute() {
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
  if (user?.role === 'admin') {
    return <Navigate to='/admin' replace />;
  }

  return (
    <motion.div
      initial={{ y: 6 }}
      animate={{ y: 0 }}
      exit={{ opacity: 0, y: -6 }}
      transition={{ duration: 0.1, ease: 'easeOut' }}>
      <Outlet />
    </motion.div>
  );
}
