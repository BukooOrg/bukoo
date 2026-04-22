import React, { useState, useEffect } from "react";
import { Link, useLocation } from "react-router-dom";
import { cn } from "@/lib/utils";
import CartModal from "@/components/cart/modal";
import Search from "./search";
import MobileMenu from "./mobile-menu";
import { UserIcon } from "lucide-react";
import { getCollections } from "@/lib/sfcc";

export function Header() {
  const { pathname } = useLocation();
  const [collections, setCollections] = useState([]);

  useEffect(() => {
    async function loadCollections() {
      const data = await getCollections();
      setCollections(data);
    }
    loadCollections();
  }, []);

  return (
    <header className="fixed top-0 left-0 w-full z-50 transition-all duration-300">
      {/* Primary Header Row */}
      <div className="p-sides bg-background/80 backdrop-blur-2xl border-b border-secondary/20 h-24 md:h-32 flex items-center gap-sides">
        <div className="flex-none md:hidden mr-4">
          <MobileMenu collections={collections} />
        </div>

        {/* Large Logo */}
        <Link to="/" className="flex-none">
          <span className="text-5xl md:text-7xl font-serif font-black tracking-tighter text-primary">Bukoo</span>
        </Link>

        {/* Wide Search Bar (Centered/Expanded) */}
        <div className="flex-1 md:px-12 flex justify-center max-md:hidden">
          <div className="w-full max-w-3xl px-6 py-2 bg-secondary/80 rounded-full border border-secondary/30 backdrop-blur-md">
            <Search />
          </div>
        </div>

        {/* Action Buttons (Right) */}
        <nav className="flex items-center gap-4 md:gap-8 ml-auto">
          <CartModal />

          <Link
            to="/login"
            className="flex items-center gap-2 px-8 py-4 bg-primary text-background rounded-full font-sans font-bold text-[10px] uppercase tracking-[0.2em] hover:scale-[1.02] active:scale-[0.98] transition-all shadow-xl"
          >
            <UserIcon className="size-4" />
            <span className="hidden lg:inline">Login / Sign Up</span>
          </Link>
        </nav>
      </div>

      {/* Genre Header Row */}
      <div className="bg-background/60 backdrop-blur-xl border-b border-secondary/15 h-12 md:h-16 flex items-center justify-center">
        <ul className="flex gap-10 md:gap-16 items-center overflow-x-auto no-scrollbar px-sides">
          {collections.filter(c => c.handle !== "joyco-root").map((item) => (
            <li key={item.handle}>
              <Link
                to={`/shop/${item.handle}`}
                className={cn(
                  "text-[11px] md:text-sm font-sans font-black uppercase tracking-[0.25em] transition-all hover:opacity-100",
                  pathname.includes(item.handle) ? "opacity-100 text-primary scale-110" : "opacity-40"
                )}
              >
                {item.title}
              </Link>
            </li>
          ))}
        </ul>
      </div>
    </header>
  );
}