import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Toaster } from 'sonner';

import { CartProvider } from './components/cart/cart-context';
import { Footer } from './components/layout/footer';
import { Header } from './components/layout/header';
import { AuthProvider } from './context/AuthContext';
// Pages
import Home from './pages/Home';
import Login from './pages/Login';
import OAuthCallback from './pages/OAuthCallback';
import ProductDetail from './pages/ProductDetail';
import Register from './pages/Register';
import Shop from './pages/Shop';

function App() {
  return (
    <AuthProvider>
      <CartProvider>
        <Router>
          <div className='min-h-screen bg-background text-foreground antialiased font-sans flex flex-col'>
            <Header />
            <main className='flex-1'>
              <Routes>
                <Route path='/' element={<Home />} />
                <Route path='/shop' element={<Shop />} />
                <Route path='/shop/:collection' element={<Shop />} />
                <Route path='/search' element={<Shop />} />
                <Route path='/product/:handle' element={<ProductDetail />} />
                <Route path='/login' element={<Login />} />
                <Route path='/register' element={<Register />} />
                <Route path='/oauth/callback' element={<OAuthCallback />} />
                <Route
                  path='*'
                  element={
                    <div className='pt-48 text-center font-serif text-2xl opacity-40'>
                      404 - Chapter Not Found
                    </div>
                  }
                />
              </Routes>
            </main>
            <Footer />
            <Toaster closeButton position='bottom-right' />
          </div>
        </Router>
      </CartProvider>
    </AuthProvider>
  );
}

export default App;
