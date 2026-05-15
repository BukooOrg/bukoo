import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';

import { OtpInputBox } from './otp-input-box';

describe('OtpInputBox', () => {
  it('renders input element', () => {
    render(<OtpInputBox index={0} onChange={vi.fn()} onKeyDown={vi.fn()} onFocus={vi.fn()} />);
    expect(screen.getByRole('textbox')).toBeInTheDocument();
  });

  it('displays value prop', () => {
    render(
      <OtpInputBox index={0} value='5' onChange={vi.fn()} onKeyDown={vi.fn()} onFocus={vi.fn()} />
    );
    expect(screen.getByRole('textbox')).toHaveValue('5');
  });

  it('calls onChange with index and new value', () => {
    const onChange = vi.fn();
    render(<OtpInputBox index={2} onChange={onChange} onKeyDown={vi.fn()} onFocus={vi.fn()} />);

    fireEvent.change(screen.getByRole('textbox'), { target: { value: '7' } });
    expect(onChange).toHaveBeenCalledWith(2, '7');
  });

  it('calls onKeyDown on key press', () => {
    const onKeyDown = vi.fn();
    render(<OtpInputBox index={0} onChange={vi.fn()} onKeyDown={onKeyDown} onFocus={vi.fn()} />);

    fireEvent.keyDown(screen.getByRole('textbox'), { key: 'Backspace' });
    expect(onKeyDown).toHaveBeenCalledWith(0, expect.any(Object));
  });

  it('calls onFocus on focus', () => {
    const onFocus = vi.fn();
    render(<OtpInputBox index={0} onChange={vi.fn()} onKeyDown={vi.fn()} onFocus={onFocus} />);

    fireEvent.focus(screen.getByRole('textbox'));
    expect(onFocus).toHaveBeenCalledWith(0);
  });

  it('applies error styling when error is true', () => {
    render(
      <OtpInputBox index={0} error onChange={vi.fn()} onKeyDown={vi.fn()} onFocus={vi.fn()} />
    );
    const input = screen.getByRole('textbox');
    expect(input).toHaveClass('border-destructive');
  });

  it('disables input when disabled is true', () => {
    render(
      <OtpInputBox index={0} disabled onChange={vi.fn()} onKeyDown={vi.fn()} onFocus={vi.fn()} />
    );
    expect(screen.getByRole('textbox')).toBeDisabled();
  });

  it('has correct aria-label', () => {
    render(<OtpInputBox index={3} onChange={vi.fn()} onKeyDown={vi.fn()} onFocus={vi.fn()} />);
    expect(screen.getByLabelText('Digit 4 of 6')).toBeInTheDocument();
  });
});
