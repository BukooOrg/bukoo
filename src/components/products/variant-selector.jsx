"use client";

import React, { startTransition, useEffect, useMemo } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import { cva } from "class-variance-authority";
import { ColorSwatch } from "@/components/ui/forms/color-picker";
import { Button } from "@/components/ui/forms/button";
import { getColorHex } from "@/lib/utils";

const variantOptionSelectorVariants = cva("flex items-center gap-4", {
  variants: {
    variant: {
      card: "rounded-lg bg-card py-2 px-3 justify-between",
      condensed: "justify-start"
    }
  },
  defaultVariants: {
    variant: "card"
  }
});

export function VariantOptionSelector({
  option,
  variant,
  product
}) {
  const { variants, options } = product;
  const [searchParams, setSearchParams] = useSearchParams();
  const params = useParams();
  const optionNameLowerCase = option.name.toLowerCase();

  const selectedValue = searchParams.get(optionNameLowerCase) || "";
  const activeProductId = searchParams.get("pid") || "";

  // Auto-select single color option
  useEffect(() => {
    if (
      optionNameLowerCase === "color" &&
      option.values.length === 1 &&
      option.values[0] &&
      !selectedValue
    ) {
      const colorValue = option.values[0].name;
      if (colorValue) {
        const newParams = new URLSearchParams(searchParams);
        newParams.set(optionNameLowerCase, colorValue);
        setSearchParams(newParams);
      }
    }
  }, [option, optionNameLowerCase, selectedValue, setSearchParams, searchParams]);

  const combinations = variants.map((variant) => ({
    id: variant.id,
    availableForSale: variant.availableForSale,
    ...variant.selectedOptions.reduce(
      (accumulator, option) => ({
        ...accumulator,
        [option.name.toLowerCase()]: option.value
      }),
      {}
    )
  }));

  const isColorOption = optionNameLowerCase === "color";
  const isProductPage = params.handle === product.id;
  const isTargetingProduct = isProductPage || activeProductId === product.id;

  return (
    <dl className={variantOptionSelectorVariants({ variant })}>
      <dt className="text-base font-semibold">{option.name}</dt>
      <dd className="flex flex-wrap gap-2">
        {option.values.map((value) => {
          const currentState = Object.fromEntries(searchParams.entries());
          const optionParams = {
            ...currentState,
            [optionNameLowerCase]: value.id
          };

          const filtered = Object.entries(optionParams).filter(([key, val]) =>
            options.find(
              (option) =>
                option.name.toLowerCase() === key &&
                option.values.some((v) => v.name === val)
            )
          );
          
          const isAvailableForSale = combinations.find((combination) =>
            filtered.every(
              ([key, val]) =>
                combination[key] === val && combination.availableForSale
            )
          );

          const isActive = isTargetingProduct && selectedValue === value.id;

          if (isColorOption) {
            const color = getColorHex(value.id);

            return (
              <ColorSwatch
                key={value.id}
                color={
                  Array.isArray(color) ?
                    [
                      { name: value.name, value: color[0] },
                      { name: value.name, value: color[1] }
                    ] :
                    { name: value.name, value: color }
                }
                isSelected={isActive}
                onColorChange={() => {
                  const newParams = new URLSearchParams(searchParams);
                  newParams.set(optionNameLowerCase, value.id);
                  if (!isProductPage) {
                    newParams.set("pid", product.id);
                  }
                  setSearchParams(newParams);
                }}
                size={variant === "condensed" ? "sm" : "md"}
                atLeastOneColorSelected={!!selectedValue}
              />
            );
          }

          return (
            <Button
              onClick={() => {
                const newParams = new URLSearchParams(searchParams);
                newParams.set(optionNameLowerCase, value.id);
                setSearchParams(newParams);
              }}
              key={value.id}
              variant={isActive ? "default" : "outline"}
              size="sm"
              disabled={!isAvailableForSale}
              title={`${option.name} ${value.name}${!isAvailableForSale ? " (Out of Stock)" : ""}`}
              className="min-w-[48px]"
            >
              {value.name}
            </Button>
          );
        })}
      </dd>
    </dl>
  );
}

export const useSelectedVariant = (product) => {
  const { variants, options } = product;
  const [searchParams] = useSearchParams();

  const selectedOptions = useMemo(() => {
    const state = {};
    options.forEach((option) => {
      const key = option.name.toLowerCase();
      const value = searchParams.get(key);
      if (value) {
        state[key] = value;
      }
    });
    return state;
  }, [options, searchParams]);

  const selectedVariant = useMemo(() => {
    return variants.find((variant) =>
      variant.selectedOptions.every(
        (option) =>
          option.value.toLowerCase() ===
          selectedOptions[option.name.toLowerCase()]?.toLowerCase()
      )
    );
  }, [variants, selectedOptions]);

  return selectedVariant;
};

export const useProductImages = (product, selectedOptions) => {
  const optionsObject = useMemo(() => {
    return selectedOptions?.reduce((acc, option) => {
      acc[option.name.toLowerCase()] = option.value.toLowerCase();
      return acc;
    }, {});
  }, [selectedOptions]);

  const variantImages = useMemo(() => {
    if (!optionsObject) return [];

    return (product.images || []).filter((image) => {
      return Object.entries(optionsObject || {}).every(([key, value]) =>
        image.selectedOptions?.some(
          (option) => option.name === key && option.value === value
        )
      );
    });
  }, [optionsObject, product.images]);

  const defaultImages = (product.images || []).filter(
    (image) => !image.selectedOptions
  );

  const featuredImage = product.featuredImage;

  if (variantImages.length > 0) return variantImages;
  if (defaultImages.length > 0) return defaultImages;
  if (featuredImage) return [featuredImage];
  return [];
};