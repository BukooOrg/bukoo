import React, { useEffect, useRef } from 'react';

import { cn } from '@/lib/utils';

/**
 * Individual OTP Input Box
 * Renders a single digit input box for the OTP component
 *
 * @param {Object} props
 * @param {number} props.index - Index of this box (0-5)
 * @param {string} props.value - Current digit value
 * @param {(index: number, value: string) => void} props.onChange - Callback when digit changes
 * @param {(index: number, e: KeyboardEvent) => void} props.onKeyDown - Key down handler
 * @param {(e: ClipboardEvent) => void} props.onPaste - Paste handler (only on first box)
 * @param {(index: number) => void} props.onFocus - Focus handler
 * @param {boolean} props.disabled - Disable input
 * @param {boolean} props.error - Show error state
 * @param {React.RefObject<HTMLInputElement>} props.inputRef - Ref for the input element
 */
export function OtpInputBox({
  index,
  value = '',
  onChange,
  onKeyDown,
  onPaste,
  onFocus,
  disabled = false,
  error = false,
  inputRef,
}) {
  const localRef = useRef(null);
  const ref = inputRef || localRef;

  useEffect(() => {
    // Auto-focus on mount if this is the first box and has no value
    if (index === 0 && !value && ref.current) {
      ref.current.focus();
    }
  }, [index, value, ref]);

  const handleChange = (e) => {
    const newValue = e.target.value.slice(-1);
    onChange(index, newValue);
  };

  const handleFocus = (e) => {
    e.target.select();
    onFocus(index);
  };

  const handleKeyDown = (e) => {
    onKeyDown(index, e);
  };

  return (
    <input
      ref={ref}
      type='text'
      inputMode='numeric'
      autoComplete='one-time-code'
      maxLength={1}
      value={value}
      onChange={handleChange}
      onKeyDown={handleKeyDown}
      onPaste={index === 0 ? onPaste : undefined}
      onFocus={handleFocus}
      disabled={disabled}
      aria-label={`Digit ${index + 1} of 6`}
      className={cn(
        'w-12 h-14 md:w-14 md:h-16',
        'text-center text-2xl md:text-3xl font-bold',
        'transition-all duration-200',
        'border-2 rounded-xl',
        'bg-white/40 backdrop-blur-sm',
        'focus:outline-none focus:ring-2 focus:ring-primary/10',
        disabled && 'opacity-50 cursor-not-allowed',
        error
          ? 'border-destructive text-destructive focus:border-destructive focus:ring-destructive/10'
          : value
            ? 'border-primary text-primary focus:border-primary focus:ring-primary/10'
            : 'border-primary/20 text-primary focus:border-primary focus:ring-primary/10',
        'hover:border-primary/40'
      )}
    />
  );
}
