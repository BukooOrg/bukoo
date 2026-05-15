import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';

import { OtpInput } from './otp-input';

describe('OtpInput', () => {
  it('renders 6 input boxes', () => {
    render(<OtpInput value='' onChange={vi.fn()} />);
    const inputs = screen.getAllByRole('textbox');
    expect(inputs).toHaveLength(6);
  });

  it('calls onChange when digit entered', () => {
    const onChange = vi.fn();
    render(<OtpInput value='' onChange={onChange} />);

    const inputs = screen.getAllByRole('textbox');
    fireEvent.change(inputs[0], { target: { value: '1' } });
    expect(onChange).toHaveBeenCalledWith('1');
  });

  it('does not call onChange for non-digit input', () => {
    const onChange = vi.fn();
    render(<OtpInput value='' onChange={onChange} />);

    const inputs = screen.getAllByRole('textbox');
    fireEvent.change(inputs[0], { target: { value: 'a' } });
    expect(onChange).not.toHaveBeenCalled();
  });

  it('handles backspace on empty box by moving focus back', () => {
    const onChange = vi.fn();
    render(<OtpInput value='12' onChange={onChange} />);

    const inputs = screen.getAllByRole('textbox');
    fireEvent.keyDown(inputs[2], { key: 'Backspace' });

    // Should clear previous digit and focus previous box
    expect(onChange).toHaveBeenCalledWith('1');
  });

  it('handles left arrow navigation', () => {
    render(<OtpInput value='123' onChange={vi.fn()} />);

    const inputs = screen.getAllByRole('textbox');
    inputs[1].focus();
    fireEvent.keyDown(inputs[1], { key: 'ArrowLeft' });

    expect(inputs[0]).toHaveFocus();
  });

  it('handles right arrow navigation', () => {
    render(<OtpInput value='123' onChange={vi.fn()} />);

    const inputs = screen.getAllByRole('textbox');
    inputs[1].focus();
    fireEvent.keyDown(inputs[1], { key: 'ArrowRight' });

    expect(inputs[2]).toHaveFocus();
  });

  it('disables all inputs when disabled prop is true', () => {
    render(<OtpInput value='' onChange={vi.fn()} disabled />);
    const inputs = screen.getAllByRole('textbox');
    inputs.forEach((input) => {
      expect(input).toBeDisabled();
    });
  });

  it('shows error state on all inputs when error is true', () => {
    render(<OtpInput value='' onChange={vi.fn()} error />);
    const inputs = screen.getAllByRole('textbox');
    inputs.forEach((input) => {
      expect(input).toHaveClass('border-destructive');
    });
  });
});
