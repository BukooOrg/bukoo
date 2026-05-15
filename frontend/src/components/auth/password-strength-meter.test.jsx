import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';

import { PasswordStrengthMeter } from './password-strength-meter';

describe('PasswordStrengthMeter', () => {
  it('returns null for empty password', () => {
    const { container } = render(<PasswordStrengthMeter password='' />);
    expect(container.firstChild).toBeNull();
  });

  it('shows weak for short password', () => {
    render(<PasswordStrengthMeter password='weak' />);
    expect(screen.getByText('Weak')).toBeInTheDocument();
  });

  it('shows medium for partial requirements', () => {
    render(<PasswordStrengthMeter password='Medium1' />);
    expect(screen.getByText('Medium')).toBeInTheDocument();
  });

  it('shows strong for full requirements', () => {
    render(<PasswordStrengthMeter password='Str0ng!Pass' />);
    expect(screen.getByText('Strong')).toBeInTheDocument();
  });
});
