"use client";

import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useState, useRef } from "react";
import { AlertTriangle, X, Check } from "lucide-react";
import { checkEnvironmentVariables } from "./actions";
import { cn } from "@/lib/utils";







export const SetupToolbar = () => {
  const [open, setOpen] = useState(false);
  const [formState, setFormState] = useState("idle");
  const [envs, setEnvs] = useState([]);
  const [allValid, setAllValid] = useState(false);
  const ref = useRef(null);

  function submit() {
    setFormState("loading");
    setTimeout(() => {
      setFormState("success");
    }, 1500);

    setTimeout(() => {
      setOpen(false);
    }, 3300);
  }

  useEffect(() => {
    const handleKeyDown = (event) => {
      if (event.key === "Escape") {
        setOpen(false);
      }

      if (
      (event.ctrlKey || event.metaKey) &&
      event.key === "Enter" &&
      open &&
      formState === "idle")
      {
        submit();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [open, formState]);

  useEffect(() => {
    const loadEnvs = async () => {
      const result = await checkEnvironmentVariables();
      setEnvs(result.envs);
      setAllValid(result.allValid);
    };
    loadEnvs();
  }, []);

  // Only show if in development and not all valid
  if (process.env.NODE_ENV === "production" || allValid) {
    return null;
  }

  const validCount = envs.filter((env) => env.isValid).length;

  return (
    <div
      aria-hidden="true"
      className={cn(
        "fixed inset-0 transition-colors flex items-end justify-center z-[9999] p-4 pointer-events-none"
      )}>
      
      <div
        onClick={() => setOpen(false)}
        className={cn(
          "absolute inset-0 transition-colors",
          open ? "pointer-events-auto bg-black/30" : "pointer-events-none"
        )} />
      
      <motion.button
        layoutId="wrapper"
        onClick={() => {
          setOpen(true);
          setFormState("idle");
        }}
        key="button"
        className="relative flex items-center gap-2 px-3 font-medium transition-colors border rounded-lg shadow-sm outline-none pointer-events-auto h-9 border-amber-200 bg-amber-50 hover:bg-amber-100"
        style={{ borderRadius: 8 }}>
        
        <motion.div layoutId="icon">
          <AlertTriangle className="w-4 h-4 text-amber-600" />
        </motion.div>
        <motion.span layoutId="title" className="block text-sm text-amber-800">
          Setup your store
        </motion.span>
      </motion.button>

      <AnimatePresence>
        {open ?
        <motion.div
          layoutId="wrapper"
          className="pointer-events-auto absolute bottom-6 w-[500px] overflow-hidden bg-neutral-100 p-1 outline-none flex flex-col"
          ref={ref}
          style={{
            borderRadius: 12,
            boxShadow:
            "0 0 0 1px rgba(0, 0, 0, 0.08), 0px 2px 2px rgba(0, 0, 0, 0.04), 0px 0px 0px 1px rgba(0, 0, 0, 0.08)",
            height: "400px"
          }}>
          
            {/* Header with animated title and close button */}
            <div className="flex items-center justify-between flex-shrink-0 px-4 py-3 border-b border-dashed rounded-t-lg bg-neutral-50 border-neutral-200">
              <div className="flex items-center gap-2">
                <motion.div layoutId="icon">
                  <AlertTriangle className="size-4 text-amber-600" />
                </motion.div>
                <motion.span
                layoutId="title"
                className="text-sm font-semibold text-amber-800">
                
                  Setup your store
                </motion.span>
              </div>
              <button
              onClick={() => setOpen(false)}
              className="p-1 transition-colors rounded text-neutral-300 hover:text-neutral-600 hover:bg-neutral-100">
              
                <X className="size-4" />
              </button>
            </div>

            <div className="flex flex-col flex-1 min-h-0">
              <motion.div
              exit={{ y: 8, opacity: 0 }}
              transition={{ type: "spring", duration: 0.25, bounce: 0 }}
              key="content"
              className="flex flex-col flex-1 min-h-0 rounded-b-lg">
              
                {/* Description */}
                <div className="flex items-center justify-between flex-shrink-0 gap-4 px-3 py-1.5 border-b bg-neutral-100 border-neutral-200">
                  <p className="text-xs text-balance text-neutral-600">
                    Configure the following environment variables to set up your
                    Salesforce Commerce Cloud integration.
                  </p>
                  <div className="flex items-center justify-center shrink-0">
                    <div className="relative size-10">
                      {/* Background circle */}
                      <svg
                      className="transform -rotate-90 size-10"
                      viewBox="0 0 32 32">
                      
                        <circle
                        cx="16"
                        cy="16"
                        r="12"
                        stroke="currentColor"
                        strokeWidth="2"
                        fill="transparent"
                        className="text-neutral-300" />
                      
                        {/* Progress circle */}
                        <circle
                        cx="16"
                        cy="16"
                        r="12"
                        stroke="currentColor"
                        strokeWidth="2"
                        fill="transparent"
                        strokeDasharray={`${2 * Math.PI * 12}`}
                        strokeDashoffset={`${
                        2 * Math.PI * 12 * (1 - validCount / envs.length)}`
                        }
                        className={
                        validCount === envs.length ?
                        "text-green-500" :
                        "text-amber-500"
                        }
                        style={{
                          transition: "stroke-dashoffset 0.3s ease-in-out"
                        }} />
                      
                      </svg>
                      {/* Center text */}
                      <div className="absolute inset-0 flex items-center justify-center">
                        <span className="text-[10px] font-semibold text-neutral-700 leading-none tabular-nums">
                          {validCount}/{envs.length}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Environment variables list */}
                <div className="flex-1 overflow-y-auto bg-white">
                  <div className="p-4 pb-6 space-y-3">
                    {envs.map((env) =>
                  <div
                    key={env.name}
                    className="flex items-center gap-3 p-3 border rounded-lg bg-neutral-50 border-neutral-200">
                    
                        <div
                      className={`flex-shrink-0 size-8 rounded-sm flex items-center justify-center ${
                      env.isValid ?
                      "bg-green-100 text-green-600" :
                      "bg-amber-100 text-amber-600"}`
                      }>
                      
                          {env.isValid ?
                      <Check className="size-4" /> :

                      <AlertTriangle className="size-4" />
                      }
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="text-sm font-medium text-neutral-900">
                            {env.label}
                          </div>
                          <div className="font-mono text-xs truncate text-neutral-500">
                            {env.name}
                          </div>
                        </div>
                        <div
                      className={`text-xs font-medium ${
                      env.isValid ? "text-green-600" : "text-amber-600"}`
                      }>
                      
                          {env.isValid ? "Set" : "Missing"}
                        </div>
                      </div>
                  )}
                  </div>
                </div>
              </motion.div>
            </div>
          </motion.div> :
        null}
      </AnimatePresence>
    </div>);

};

export default SetupToolbar;