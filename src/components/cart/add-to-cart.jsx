"use client";

import React, { useState, useMemo } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import { PlusCircleIcon } from "lucide-react";
import { useCart } from "./cart-context";
import { Button } from "../ui/forms/button";
import { Tooltip, TooltipTrigger, TooltipContent } from "../ui/overlays/tooltip";
import { useSelectedVariant } from "@/components/products/variant-selector";
import { addToCart as apiAddToCart } from "@/lib/sfcc";
import { motion, AnimatePresence } from "motion/react";
import { Loader } from "../ui/feedback/loader";

const getBaseProductVariant = (product) => {
  return {
    id: product.id,
    title: product.title,
    availableForSale: product.availableForSale,
    selectedOptions: [],
    price: product.priceRange.minVariantPrice
  };
};

export function AddToCart({
  product,
  className,
  iconOnly = false,
  icon = <PlusCircleIcon />,
  ...buttonProps
}) {
  const { variants, availableForSale } = product;
  const { addCartItem, mode } = useCart();
  const [isLoading, setIsLoading] = useState(false);
  const selectedVariant = useSelectedVariant(product);
  const params = useParams();
  const [searchParams] = useSearchParams();

  const hasNoVariants = variants.length === 0;
  const defaultVariantId = variants.length === 1 ? variants[0]?.id : undefined;
  const selectedVariantId = selectedVariant?.id || defaultVariantId;
  const isTargetingProduct =
    params.handle === product.id || searchParams.get("pid") === product.id;

  const resolvedVariant = useMemo(() => {
    if (hasNoVariants) return getBaseProductVariant(product);
    if (!isTargetingProduct && !defaultVariantId) return undefined;
    return variants.find((variant) => variant.id === selectedVariantId);
  }, [hasNoVariants, product, isTargetingProduct, defaultVariantId, variants, selectedVariantId]);

  const handleAddToCart = async (e) => {
    e.preventDefault();
    if (!resolvedVariant) return;

    setIsLoading(true);
    try {
      // Optimistic update
      addCartItem(resolvedVariant, product);
      
      // API call
      await apiAddToCart([
        {
          merchandiseId: resolvedVariant.id,
        }
      ]);
    } catch (error) {
      console.error("Failed to add to cart", error);
    } finally {
      setIsLoading(false);
    }
  };

  const getButtonText = () => {
    if (mode === "mock") return "Bag disabled";
    if (!availableForSale) return "Out Of Stock";
    if (!resolvedVariant) return "Select an option";
    return "Add To Bag";
  };

  const isDisabled =
    !availableForSale || !resolvedVariant || isLoading || mode === "mock";

  const getLoaderSize = () => {
    const buttonSize = buttonProps.size;
    if (buttonSize === "sm" || buttonSize === "icon-sm" || buttonSize === "icon") return "sm";
    if (buttonSize === "icon-lg") return "default";
    if (buttonSize === "lg") return "lg";
    return "default";
  };

  const buttonElement = (
    <Button
      type="button"
      onClick={handleAddToCart}
      aria-label={!resolvedVariant ? "Please select an option" : "Add to bag"}
      disabled={isDisabled}
      className={iconOnly ? undefined : "w-full relative flex items-center justify-between"}
      {...buttonProps}
    >
      <AnimatePresence initial={false} mode="wait">
        {iconOnly ? (
          <motion.div
            key={isLoading ? "loading" : "icon"}
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            transition={{ duration: 0.15 }}
            className="flex items-center justify-center"
          >
            {isLoading ? <Loader size={getLoaderSize()} /> : <span className="inline-block">{icon}</span>}
          </motion.div>
        ) : (
          <motion.div
            key={isLoading ? "loading" : getButtonText()}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="w-full flex items-center justify-center"
          >
            {isLoading ? (
              <Loader size={getLoaderSize()} />
            ) : (
              <div className="w-full flex items-center justify-between">
                <span className="font-sans font-bold uppercase tracking-tight">{getButtonText()}</span>
                <PlusCircleIcon />
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </Button>
  );

  return (
    <div className={className}>
      {mode === "mock" ? (
        <Tooltip>
          <TooltipTrigger asChild>
            <div className="w-full">{buttonElement}</div>
          </TooltipTrigger>
          <TooltipContent portal={false} className="pointer-events-none">
            <span className="relative z-10">You need to complete SFCC setup</span>
          </TooltipContent>
        </Tooltip>
      ) : (
        buttonElement
      )}
    </div>
  );
}