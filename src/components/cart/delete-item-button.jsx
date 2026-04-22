"use client";

import React from "react";
import { removeFromCart } from "@/lib/sfcc";
import { Button } from "../ui/forms/button";

export function DeleteItemButton({
  item,
  optimisticUpdate
}) {
  const merchandiseId = item.merchandise.id;

  const handleRemove = async (e) => {
    e.preventDefault();
    optimisticUpdate(merchandiseId, "delete");
    try {
      if (item.id) {
        await removeFromCart([item.id]);
      }
    } catch (error) {
      console.error("Failed to remove item", error);
    }
  };

  return (
    <div className="-mr-1 -mb-1 opacity-70">
      <Button
        onClick={handleRemove}
        type="button"
        size="sm"
        variant="ghost"
        aria-label="Remove item"
        className="px-2 text-sm">
        Remove
      </Button>
    </div>
  );
}