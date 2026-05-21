import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

import { CartProvider } from './components/cart/CartContext';
// ─── Guards ─────────────────────────────────────────────────────────────────
import { AdminRoute } from './components/guards/AdminRoute';
// ─── Legacy router (kept for reference) ──────────────────────────────────────
// import { Toaster } from 'sonner';
// import { Footer } from './components/layout/footer';
// import { Header } from './components/layout/header';
// import Home from './pages/Home';
// import Login from './pages/Login';
// import OAuthCallback from './pages/OAuthCallback';
// import ProductDetail from './pages/ProductDetail';
// import Register from './pages/Register';
// import Shop from './pages/Shop';
//
// function AppLegacy() {
//   return (
//     <AuthProvider>
//       <CartProvider>
//         <Router>
//           <div className='flex flex-col min-h-screen font-sans antialiased bg-background text-foreground'>
//             <Header />
//             <main className='flex-1'>
//               <Routes>
//                 <Route path='/' element={<Home />} />
//                 <Route path='/shop' element={<Shop />} />
//                 <Route path='/shop/:collection' element={<Shop />} />
//                 <Route path='/search' element={<Shop />} />
//                 <Route path='/product/:handle' element={<ProductDetail />} />
//                 <Route path='/login' element={<Login />} />
//                 <Route path='/register' element={<Register />} />
//                 <Route path='/oauth/callback' element={<OAuthCallback />} />
//                 <Route
//                   path='*'
//                   element={
//                     <div className='pt-48 font-serif text-2xl text-center opacity-40'>
//                       404 - Chapter Not Found
//                     </div>
//                   }
//                 />
//               </Routes>
//             </main>
//             <Footer />
//             <Toaster closeButton position='bottom-right' />
//           </div>
//         </Router>
//       </CartProvider>
//     </AuthProvider>
//   );
// }
import { ProtectedRoute } from './components/guards/ProtectedRoute';
// ─── Layouts ────────────────────────────────────────────────────────────────
import { AccountLayout } from './components/layout/AccountLayout';
import { AdminLayout } from './components/layout/AdminLayout';
import { AuthLayout } from './components/layout/AuthLayout';
import { StorefrontLayout } from './components/layout/StorefrontLayout';
import { WishlistProvider } from './components/wishlist/WishlistContext';
import { AuthProvider } from './context/AuthContext';
// ─── Account pages ───────────────────────────────────────────────────────────
import AccountPage from './pages/account/AccountPage';
import AddressPage from './pages/account/AddressPage';
import DeleteAccountPage from './pages/account/DeleteAccountPage';
import AccountNotificationsPage from './pages/account/NotificationsPage';
import AccountOrderDetailPage from './pages/account/OrderDetailPage';
import AccountOrdersPage from './pages/account/OrdersPage';
import PasswordPage from './pages/account/PasswordPage';
import ProfilePage from './pages/account/ProfilePage';
import AccountReviewsPage from './pages/account/ReviewsPage';
import AuthorDetailPage from './pages/admin/catalog/AuthorDetailPage';
import AuthorNewPage from './pages/admin/catalog/AuthorNewPage';
import AuthorsPage from './pages/admin/catalog/AuthorsPage';
import BookDetailPage from './pages/admin/catalog/BookDetailPage';
import BookNewPage from './pages/admin/catalog/BookNewPage';
// ─── Admin — Catalog ─────────────────────────────────────────────────────────
import BooksPage from './pages/admin/catalog/BooksPage';
import CategoriesPage from './pages/admin/catalog/CategoriesPage';
import CategoryDetailPage from './pages/admin/catalog/CategoryDetailPage';
import CategoryNewPage from './pages/admin/catalog/CategoryNewPage';
import CollectionDetailPage from './pages/admin/catalog/CollectionDetailPage';
import CollectionNewPage from './pages/admin/catalog/CollectionNewPage';
import CollectionsPage from './pages/admin/catalog/CollectionsPage';
import PublisherDetailPage from './pages/admin/catalog/PublisherDetailPage';
import PublisherNewPage from './pages/admin/catalog/PublisherNewPage';
import PublishersPage from './pages/admin/catalog/PublishersPage';
// ─── Admin — Dashboard ───────────────────────────────────────────────────────
import AdminDashboardPage from './pages/admin/DashboardPage';
// ─── Admin — Inventory & Reports ─────────────────────────────────────────────
import InventoryPage from './pages/admin/inventory/InventoryPage';
import ReportsPage from './pages/admin/inventory/ReportsPage';
import AdminNotificationsPage from './pages/admin/NotificationsPage';
import AdminOrderDetailPage from './pages/admin/orders/OrderDetailPage';
// ─── Admin — Orders ──────────────────────────────────────────────────────────
import AdminOrdersPage from './pages/admin/orders/OrdersPage';
// ─── Admin — Reviews ─────────────────────────────────────────────────────────
import AdminReviewsPage from './pages/admin/reviews/ReviewsPage';
import UserDetailPage from './pages/admin/users/UserDetailPage';
import UserNewPage from './pages/admin/users/UserNewPage';
// ─── Admin — Users ───────────────────────────────────────────────────────────
import UsersPage from './pages/admin/users/UsersPage';
import ForgotPasswordPage from './pages/auth/ForgotPasswordPage';
// ─── Auth pages ─────────────────────────────────────────────────────────────
import LoginPage from './pages/auth/LoginPage';
import OAuthCallbackPage from './pages/auth/OAuthCallbackPage';
import RegisterPage from './pages/auth/RegisterPage';
import ResetPasswordPage from './pages/auth/ResetPasswordPage';
import VerifyEmailPage from './pages/auth/VerifyEmailPage';
import VerifyPasswordResetOtpPage from './pages/auth/VerifyPasswordResetOtpPage';
// ─── Shopping pages ──────────────────────────────────────────────────────────
import CartPage from './pages/shopping/CartPage';
import CheckoutConfirmationPage from './pages/shopping/CheckoutConfirmationPage';
import CheckoutPage from './pages/shopping/CheckoutPage';
import CheckoutPaymentPage from './pages/shopping/CheckoutPaymentPage';
import WishlistPage from './pages/shopping/WishlistPage';
// ─── Storefront pages ────────────────────────────────────────────────────────
import HomePage from './pages/storefront/HomePage';
import NotFoundPage from './pages/storefront/NotFoundPage';
import ProductDetailPage from './pages/storefront/ProductDetailPage';
import ShopPage from './pages/storefront/ShopPage';

function App() {
  return (
    <AuthProvider>
      <CartProvider>
        <WishlistProvider>
          <Router>
            <Routes>
              {/* ── AUTH LAYOUT — no Header/Footer ───────────────────────── */}
              <Route element={<AuthLayout />}>
                <Route path='/login' element={<LoginPage />} />
                <Route path='/register' element={<RegisterPage />} />
                <Route path='/oauth/callback' element={<OAuthCallbackPage />} />
                <Route path='/verify-email' element={<VerifyEmailPage />} />
                <Route path='/forgot-password' element={<ForgotPasswordPage />} />
                <Route path='/verify-password-reset-otp' element={<VerifyPasswordResetOtpPage />} />
                <Route path='/reset-password' element={<ResetPasswordPage />} />
              </Route>

              {/* ── STOREFRONT LAYOUT — Header + Footer ──────────────────── */}
              <Route element={<StorefrontLayout />}>
                {/* 🌐 Public */}
                <Route path='/' element={<HomePage />} />
                <Route path='/shop' element={<ShopPage />} />
                <Route path='/shop/:collection' element={<ShopPage />} />
                <Route path='/search' element={<ShopPage />} />
                <Route path='/product/:handle' element={<ProductDetailPage />} />

                {/* 👤 Account pages — with header/footer */}
                <Route element={<ProtectedRoute />}>
                  <Route element={<AccountLayout />}>
                    <Route path='/account' element={<AccountPage />} />
                    <Route path='/account/profile' element={<ProfilePage />} />
                    <Route path='/account/password' element={<PasswordPage />} />
                    <Route path='/account/address' element={<AddressPage />} />
                    <Route path='/account/wishlist' element={<WishlistPage />} />
                    <Route path='/account/delete' element={<DeleteAccountPage />} />
                    <Route path='/account/orders' element={<AccountOrdersPage />} />
                    <Route path='/account/orders/:orderId' element={<AccountOrderDetailPage />} />
                    <Route path='/account/reviews' element={<AccountReviewsPage />} />
                    <Route path='/account/notifications' element={<AccountNotificationsPage />} />
                    <Route path='/account/cart' element={<CartPage />} />
                  </Route>
                  <Route path='/checkout' element={<CheckoutPage />} />
                  <Route path='/checkout/payment' element={<CheckoutPaymentPage />} />
                  <Route path='/checkout/confirmation' element={<CheckoutConfirmationPage />} />
                </Route>
              </Route>

              {/* ── ADMIN LAYOUT — sidebar shell ─────────────────────────── */}
              <Route element={<AdminRoute />}>
                <Route element={<AdminLayout />}>
                  {/* Dashboard */}
                  <Route path='/admin' element={<AdminDashboardPage />} />
                  <Route path='/admin/notifications' element={<AdminNotificationsPage />} />

                  {/* Catalog */}
                  <Route path='/admin/books' element={<BooksPage />} />
                  <Route path='/admin/books/new' element={<BookNewPage />} />
                  <Route path='/admin/books/:bookId' element={<BookDetailPage />} />
                  <Route path='/admin/collections' element={<CollectionsPage />} />
                  <Route path='/admin/collections/new' element={<CollectionNewPage />} />
                  <Route
                    path='/admin/collections/:collectionId'
                    element={<CollectionDetailPage />}
                  />
                  <Route path='/admin/categories' element={<CategoriesPage />} />
                  <Route path='/admin/categories/new' element={<CategoryNewPage />} />
                  <Route path='/admin/categories/:categoryId' element={<CategoryDetailPage />} />
                  <Route path='/admin/authors' element={<AuthorsPage />} />
                  <Route path='/admin/authors/new' element={<AuthorNewPage />} />
                  <Route path='/admin/authors/:authorId' element={<AuthorDetailPage />} />
                  <Route path='/admin/publishers' element={<PublishersPage />} />
                  <Route path='/admin/publishers/new' element={<PublisherNewPage />} />
                  <Route path='/admin/publishers/:publisherId' element={<PublisherDetailPage />} />

                  {/* Users */}
                  <Route path='/admin/users' element={<UsersPage />} />
                  <Route path='/admin/users/new' element={<UserNewPage />} />
                  <Route path='/admin/users/:userId' element={<UserDetailPage />} />

                  {/* Orders */}
                  <Route path='/admin/orders' element={<AdminOrdersPage />} />
                  <Route path='/admin/orders/:orderId' element={<AdminOrderDetailPage />} />

                  {/* Reviews */}
                  <Route path='/admin/reviews' element={<AdminReviewsPage />} />

                  {/* Inventory & Reports */}
                  <Route path='/admin/inventory' element={<InventoryPage />} />
                  <Route path='/admin/reports' element={<ReportsPage />} />
                </Route>
              </Route>

              {/* 404 */}
              <Route path='*' element={<NotFoundPage />} />
            </Routes>
          </Router>
        </WishlistProvider>
      </CartProvider>
    </AuthProvider>
  );
}

export default App;
