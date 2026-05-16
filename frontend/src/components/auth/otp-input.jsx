import React, { useRef, useCallback } from 'react';

import { OtpInputBox } from './otp-input-box';

/**
 * OTP Input Component
 * Renders 6 individual input boxes for entering a verification code
 *
 * @param {Object} props
 * @param {string} props.value - Current OTP value (0-6 digits)
 * @param {(value: string) => void} props.onChange - Callback when OTP changes
 * @param {boolean} props.disabled - Disable input
 * @param {boolean} props.error - Show error state
 */
export function OtpInput({ value = '', onChange, disabled = false, error = false }) {
  const inputRefs = useRef([]);

  // Initialize refs array
  if (inputRefs.current.length !== 6) {
    inputRefs.current = Array(6).fill(null);
  }

  const handleDigitChange = useCallback(
    (index, digit) => {
      // Only allow single digit (0-9)
      if (digit && !/^\d$/.test(digit)) return;

      const newValue = value.split('');
      newValue[index] = digit || '';
      const newValueStr = newValue.join('').slice(0, 6);

      onChange(newValueStr);

      // Auto-advance to next box if digit entered
      if (digit && index < 5) {
        inputRefs.current[index + 1]?.focus();
      }
    },
    [value, onChange]
  );

  const handleKeyDown = useCallback(
    (index, e) => {
      // Handle backspace
      if (e.key === 'Backspace' && !value[index] && index > 0) {
        e.preventDefault();
        inputRefs.current[index - 1]?.focus();

        // Clear previous digit
        const newValue = value.split('');
        newValue[index - 1] = '';
        onChange(newValue.join('').slice(0, 6));
      }

      // Handle left arrow
      if (e.key === 'ArrowLeft' && index > 0) {
        e.preventDefault();
        inputRefs.current[index - 1]?.focus();
      }

      // Handle right arrow
      if (e.key === 'ArrowRight' && index < 5) {
        e.preventDefault();
        inputRefs.current[index + 1]?.focus();
      }
    },
    [value, onChange]
  );

  const handlePaste = useCallback(
    (e) => {
      e.preventDefault();

      const pastedData = e.clipboardData.getData('text');
      const digits = pastedData.replace(/\D/g, '').slice(0, 6);

      if (digits.length > 0) {
        onChange(digits);

        // Focus on the next empty box or last box
        const focusIndex = Math.min(digits.length, 5);
        inputRefs.current[focusIndex]?.focus();
      }
    },
    [onChange]
  );

  const handleFocus = useCallback((index) => {
    // Select all text in the focused box
    const input = inputRefs.current[index];
    if (input) {
      input.select();
    }
  }, []);

  return (
    <div className='flex justify-center gap-2 md:gap-3'>
      {Array(6)
        .fill(null)
        .map((_, index) => (
          <OtpInputBox
            key={index}
            index={index}
            value={value[index] || ''}
            onChange={handleDigitChange}
            onKeyDown={handleKeyDown}
            onPaste={index === 0 ? handlePaste : null}
            onFocus={handleFocus}
            disabled={disabled}
            error={error}
            inputRef={(el) => (inputRefs.current[index] = el)}
          />
        ))}
    </div>
  );
}
