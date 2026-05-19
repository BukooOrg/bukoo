'use client';

import * as TooltipPrimitive from '@radix-ui/react-tooltip';
import * as React from 'react';

import { cn } from '@/lib/utils';

function TooltipProvider({ delayDuration = 0, ...props }) {
  return (
    <TooltipPrimitive.Provider
      data-slot='tooltip-provider'
      delayDuration={delayDuration}
      {...props}
    />
  );
}

function Tooltip({ delayDuration = 0, ...props }) {
  return <TooltipPrimitive.Root delayDuration={delayDuration} data-slot='tooltip' {...props} />;
}

function TooltipTrigger({ ...props }) {
  return <TooltipPrimitive.Trigger data-slot='tooltip-trigger' {...props} />;
}

function TooltipContent({
  className,
  sideOffset = 4,
  side = 'right',
  portal = true,
  children,
  ...props
}) {
  const content = (
    <TooltipPrimitive.Content
      data-slot='tooltip-content'
      sideOffset={sideOffset}
      side={side}
      className={cn(
        'bg-zinc-900 text-white animate-in fade-in-0 zoom-in-95 data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2 z-[100] w-fit rounded-md px-3 py-1.5 text-xs text-balance shadow-md',
        className
      )}
      {...props}>
      {children}
    </TooltipPrimitive.Content>
  );

  if (!portal) {
    return content;
  }

  return <TooltipPrimitive.Portal>{content}</TooltipPrimitive.Portal>;
}

export { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider };
