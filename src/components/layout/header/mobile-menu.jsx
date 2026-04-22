import React, { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { motion, AnimatePresence } from "motion/react";
import { Button } from "@/components/ui/forms/button";
import { ShopLinks } from "../shop-links";
import { User } from "lucide-react";

export default function MobileMenu({ collections }) {
  const [isOpen, setIsOpen] = useState(false);
  const { pathname } = useLocation();
  const openMobileMenu = () => setIsOpen(true);
  const closeMobileMenu = () => setIsOpen(false);

  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth > 768) {
        setIsOpen(false);
      }
    };
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  // Close menu when route changes
  useEffect(() => {
    closeMobileMenu();
  }, [pathname]);

  return (
    <>
      <Button
        onClick={openMobileMenu}
        aria-label="Open mobile menu"
        variant="secondary"
        size="sm"
        className="md:hidden uppercase">
        Menu
      </Button>

      <AnimatePresence>
        {isOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.3, ease: "easeInOut" }}
              className="fixed inset-0 bg-foreground/30 z-50"
              onClick={closeMobileMenu}
              aria-hidden="true"
            />

            {/* Panel */}
            <motion.div
              initial={{ x: "-100%" }}
              animate={{ x: 0 }}
              exit={{ x: "-100%" }}
              transition={{ duration: 0.3, ease: "easeInOut" }}
              className="fixed top-0 bottom-0 left-0 flex w-full md:w-[400px] p-modal-sides z-50"
            >
              <div className="flex flex-col bg-muted p-3 md:p-4 rounded w-full">
                <div className="pl-2 flex items-baseline justify-between mb-10">
                  <p className="text-2xl font-semibold">Menu</p>
                  <Button
                    size="sm"
                    variant="ghost"
                    aria-label="Close menu"
                    onClick={closeMobileMenu}
                  >
                    Close
                  </Button>
                </div>

                <nav className="grid grid-cols-1 gap-4 mb-10">
                  <Link 
                    to="/login" 
                    className="flex items-center gap-4 p-4 bg-primary text-secondary rounded-2xl font-sans font-bold uppercase tracking-widest text-xs"
                    onClick={closeMobileMenu}
                  >
                    <User className="size-5" />
                    Login / Sign Up
                  </Link>
                </nav>

                <ShopLinks label="Genres" collections={collections} />

                <div className="mt-auto mb-6">
                  <p className="font-serif font-black tracking-tighter text-3xl text-primary">
                    Every great story begins with a single page.
                  </p>
                  <div className="mt-5 text-sm font-sans font-bold italic opacity-40 leading-tight">
                    <p>Curated collections for the modern reader.</p>
                    <p>Bukoo — where stories live.</p>
                  </div>
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}