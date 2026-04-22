import React, { useState, useEffect, Suspense } from "react";
import { useParams, Link } from "react-router-dom";
import { getCollection, getProduct } from "@/lib/sfcc";
import { HIDDEN_PRODUCT_TAG } from "@/lib/constants";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbSeparator,
  BreadcrumbPage
} from "@/components/ui/navigation/breadcrumb";
import { AddToCart } from "@/components/cart/add-to-cart";
import { storeCatalog } from "@/lib/sfcc/constants";
import Prose from "@/components/prose";
import { formatPrice } from "@/lib/sfcc/utils";
import { cn } from "@/lib/utils";
import { PageLayout } from "@/components/layout/page-layout";
import { VariantSelectorSlots } from "./Product/variant-selector-slots";
import { MobileGallerySlider } from "./Product/mobile-gallery-slider";
import { DesktopGallery } from "./Product/desktop-gallery";
import { BookViewer3D } from "@/components/3d-book/BookViewer3D";
import { Box, Image as ImageIcon } from "lucide-react";

export default function ProductDetail() {
  const { handle } = useParams();
  const [product, setProduct] = useState(null);
  const [collection, setCollection] = useState(null);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState("3d"); // default to 3d for the wow effect

  useEffect(() => {
    async function loadData() {
      try {
        const prod = await getProduct(handle);
        if (prod) {
          setProduct(prod);
          if (prod.categoryId) {
            const coll = await getCollection(prod.categoryId);
            setCollection(coll);
          }
        }
      } catch (error) {
        console.error("Failed to load product", error);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [handle]);

  if (loading) {
    return <PageLayout className="bg-muted"><div className="pt-48 text-center font-serif italic opacity-50">Opening the pages...</div></PageLayout>;
  }

  if (!product) {
    return <PageLayout className="bg-muted"><div className="pt-48 text-center font-serif text-2xl">Book not found.</div></PageLayout>;
  }

  const rootParentCategory = collection?.parentCategoryTree?.find(
    (c) => c.id !== storeCatalog.rootCategoryId
  );

  const hasVariants = product.variants?.length > 1;

  return (
    <PageLayout className="bg-muted min-h-screen">
      <div className="flex flex-col md:grid md:grid-cols-12 md:gap-sides">
        {/* Mobile Gallery Slider */}
        <div className="md:hidden col-span-full h-[60vh] min-h-[400px] relative">
          <div className="absolute top-4 right-4 z-10 flex gap-2">
            <button 
              onClick={() => setViewMode(viewMode === "2d" ? "3d" : "2d")}
              className="bg-white/80 backdrop-blur-md p-3 rounded-full shadow-lg border border-white/40 hover:scale-110 transition-transform active:scale-95"
            >
              {viewMode === "2d" ? <Box className="w-5 h-5" /> : <ImageIcon className="w-5 h-5" />}
            </button>
          </div>
          <Suspense fallback={null}>
            {viewMode === "2d" ? (
              <MobileGallerySlider product={product} />
            ) : (
              <div className="w-full h-full bg-white/40 backdrop-blur-sm">
                <BookViewer3D 
                  frontCoverUrl={product.images?.[0]?.url} 
                  backCoverUrl={product.images?.[1]?.url} 
                />
              </div>
            )}
          </Suspense>
        </div>

        <div className="col-span-5 flex flex-col 2xl:col-span-4 max-md:col-span-full md:h-screen max-md:p-sides md:pl-sides md:pt-32 sticky max-md:static top-0">
          <div className="col-span-full">
            <Breadcrumb className="col-span-full mb-3 md:mb-8">
              <BreadcrumbList>
                <BreadcrumbItem>
                  <BreadcrumbLink asChild>
                    <Link to="/shop">Shop</Link>
                  </BreadcrumbLink>
                </BreadcrumbItem>
                {rootParentCategory && (
                  <>
                    <BreadcrumbSeparator />
                    <BreadcrumbItem>
                      <BreadcrumbLink asChild>
                        <Link to={`/shop/${rootParentCategory.id}`}>
                          {rootParentCategory.name}
                        </Link>
                      </BreadcrumbLink>
                    </BreadcrumbItem>
                  </>
                )}
                <BreadcrumbSeparator />
                <BreadcrumbItem>
                  <BreadcrumbPage>{product.title}</BreadcrumbPage>
                </BreadcrumbItem>
              </BreadcrumbList>
            </Breadcrumb>

            <div className="flex flex-col gap-4 col-span-full mb-10 max-md:order-2">
              <div className="rounded-3xl bg-white/80 backdrop-blur-3xl py-8 px-10 flex flex-col border border-white/40 shadow-2xl">
                <div className="mb-6">
                   <h1 className="text-4xl lg:text-5xl font-serif font-black text-primary tracking-tighter mb-2">
                    {product.title}
                  </h1>
                  <p className="text-primary/40 font-bold italic text-sm">{product.vendor || "Bukoo Editions"}</p>
                </div>
                
                <p className="text-sm font-medium text-primary/70 leading-relaxed mb-10">
                  {product.description}
                </p>

                <div className="mt-auto pt-6 border-t border-primary/5 flex items-center justify-between">
                  <p className="text-3xl font-serif font-black text-primary">
                    {formatPrice(
                      product.priceRange?.minVariantPrice?.amount || "0",
                      product.priceRange?.minVariantPrice?.currencyCode || "GBP"
                    )}
                  </p>
                  <div className="flex items-center gap-3">
                    <div className="px-4 py-1 bg-primary/5 rounded-full text-[10px] font-black uppercase tracking-widest text-primary/40">
                      Hardcover
                    </div>
                  </div>
                </div>

                {/* View Mode Toggle */}
                <div className="mt-6 pt-6 border-t border-primary/5 flex flex-col gap-3">
                  <p className="text-[10px] font-black uppercase tracking-widest text-primary/30">Display Mode</p>
                  <div className="flex bg-primary/5 p-1 rounded-xl">
                    <button 
                      onClick={() => setViewMode("2d")}
                      className={cn("flex-1 py-2 px-4 rounded-lg text-xs font-bold uppercase tracking-widest transition-all flex items-center justify-center gap-2", {
                        "bg-white shadow-sm text-primary": viewMode === "2d",
                        "text-primary/40 hover:text-primary/60": viewMode !== "2d"
                      })}
                    >
                      <ImageIcon className="w-3.5 h-3.5" /> 2D Gallery
                    </button>
                    <button 
                      onClick={() => setViewMode("3d")}
                      className={cn("flex-1 py-2 px-4 rounded-lg text-xs font-bold uppercase tracking-widest transition-all flex items-center justify-center gap-2", {
                        "bg-white shadow-sm text-primary": viewMode === "3d",
                        "text-primary/40 hover:text-primary/60": viewMode !== "3d"
                      })}
                    >
                      <Box className="w-3.5 h-3.5" /> 3D Viewer
                    </button>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 gap-4">
                <Suspense fallback={null}>
                  <VariantSelectorSlots product={product} />
                </Suspense>

                <Suspense fallback={null}>
                  <AddToCart
                    product={product}
                    size="lg"
                    className={cn("w-full py-6 rounded-2xl bg-primary text-secondary font-sans font-bold uppercase tracking-[0.2em] shadow-2xl hover:scale-[1.02] active:scale-[0.98] transition-all", {
                      "col-span-full": !hasVariants
                    })}
                  />
                </Suspense>
              </div>
            </div>
          </div>

          <Prose
            className="col-span-full opacity-70 mb-auto max-md:order-3 max-md:mt-6 prose-sm"
            html={product.descriptionHtml}
          />
        </div>

        {/* Desktop Gallery */}
        <div className="hidden md:block col-start-6 col-span-7 w-full h-screen overflow-y-auto relative bg-white/20">
          <div className="w-full h-full">
            <Suspense fallback={null}>
              {viewMode === "2d" ? (
                <DesktopGallery product={product} />
              ) : (
                <div className="w-full h-full animate-in fade-in duration-700">
                  <BookViewer3D 
                    frontCoverUrl={product.images?.[0]?.url} 
                    backCoverUrl={product.images?.[1]?.url} 
                  />
                </div>
              )}
            </Suspense>
          </div>
        </div>
      </div>
    </PageLayout>
  );
}
