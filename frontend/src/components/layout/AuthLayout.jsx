import { motion } from 'motion/react';
import React from 'react';
import { Outlet } from 'react-router-dom';
import { Toaster } from 'sonner';

export function AuthLayout() {
  return (
    <>
      <motion.div
        initial={{ y: 6 }}
        animate={{ y: 0 }}
        exit={{ opacity: 0, y: -6 }}
        transition={{ duration: 0.1, ease: 'easeOut' }}>
        <Outlet />
      </motion.div>
      <Toaster closeButton position='bottom-right' />
    </>
  );
}
