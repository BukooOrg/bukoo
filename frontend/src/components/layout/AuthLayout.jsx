import React from 'react';
import { Outlet } from 'react-router-dom';
import { Toaster } from 'sonner';

export function AuthLayout() {
  return (
    <>
      <Outlet />
      <Toaster closeButton position='bottom-right' />
    </>
  );
}
