import { CONTACT_LINKS } from "@/lib/constants";
import { cn } from "@/lib/utils";
import { cva } from "class-variance-authority";
import { Link } from "react-router-dom";

const linkVariants = cva(
  "leading-tight transition-colors hover:underline ease-out duration-200 whitespace-nowrap",
  {
    variants: {
      invert: {
        true: "text-background/50 hover:text-background",
        false: "text-muted-foreground hover:text-foreground"
      },
      size: {
        sm: "text-xs 2xl:text-sm",
        base: "text-sm 2xl:text-base"
      }
    },
    defaultVariants: {
      invert: false,
      size: "sm"
    }
  }
);







export function SidebarLinks({ className, invert, size }) {
  return (
    <ul className={cn("flex flex-row gap-2 justify-between", className)}>
      {CONTACT_LINKS.map((link) =>
      <li key={link.href}>
          <Link
          to={link.href}
          target="_blank"
          className={linkVariants({ invert, size })}>
          
            {link.label}
          </Link>
        </li>
      )}
    </ul>);

}