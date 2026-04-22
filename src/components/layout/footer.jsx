import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { ShopLinks } from "./shop-links";
import { getCollections } from "@/lib/sfcc";

export function Footer() {
  const [collections, setCollections] = useState([]);

  useEffect(() => {
    async function loadCollections() {
      try {
        const data = await getCollections();
        setCollections(data);
      } catch (error) {
        console.error("Failed to load collections for footer", error);
      }
    }
    loadCollections();
  }, []);

  return (
    <footer className="w-full px-sides pb-0 pt-12">
      <div className="w-full px-10 py-8 md:px-14 md:py-10 text-primary bg-secondary/30 rounded-t-[32px] flex flex-col justify-between border border-border/20 border-b-0 backdrop-blur-xl">
        <div className="flex flex-col md:flex-row justify-between items-start gap-12">
          <div className="flex flex-col gap-4">
            <span className="text-4xl md:text-5xl font-serif font-black tracking-tighter text-primary">Bukoo.</span>
            <p className="max-w-md text-[10px] font-sans font-black uppercase tracking-widest opacity-40 leading-loose">
              Curated stories for the modern seeker. Bukoo is your gateway to worlds unknown, crafted with care and a love for the written word.
            </p>
          </div>
          <ShopLinks collections={collections} align="left" label="Explore Genres" />
        </div>
        <div className="flex flex-col md:flex-row justify-between items-center text-primary/40 border-t border-border/10 pt-6 mt-8 gap-4">
          <div className="flex gap-8 text-[10px] font-black uppercase tracking-[0.3em]">
            <Link to="#" className="hover:text-primary transition-colors">Privacy</Link>
            <Link to="#" className="hover:text-primary transition-colors">Terms</Link>
            <Link to="#" className="hover:text-primary transition-colors">Shipping</Link>
          </div>
          <p className="text-[10px] font-sans font-black uppercase tracking-[0.2em] opacity-40">
            {new Date().getFullYear()}© — Bukoo Online Bookstore.
          </p>
        </div>
      </div>
    </footer>
  );
}