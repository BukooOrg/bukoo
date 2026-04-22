"use client";

import * as CollapsiblePrimitive from "@radix-ui/react-collapsible";

function Collapsible({
  ...props
}) {
  return <CollapsiblePrimitive.Root data-slot="collapsible" {...props} />;
}

function CollapsibleTrigger({
  ...props
}) {
  return (
    <CollapsiblePrimitive.CollapsibleTrigger
      data-slot="collapsible-trigger"
      {...props} />);


}

function CollapsibleContent({
  className,
  ...props
}) {
  return (
    <CollapsiblePrimitive.CollapsibleContent
      data-slot="collapsible-content"
      className={`overflow-hidden data-[state=closed]:animate-collapsible-up data-[state=open]:animate-collapsible-down ${
      className || ""}`
      }
      {...props} />);


}

export { Collapsible, CollapsibleTrigger, CollapsibleContent };