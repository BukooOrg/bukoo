import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';

import { StarRating } from '@/components/reviews/star-rating';

describe('StarRating', () => {
  it('renders 5 stars', () => {
    render(<StarRating value={0} />);
    const stars = screen.getAllByRole('button');
    expect(stars).toHaveLength(5);
  });

  it('fills correct number of stars', () => {
    render(<StarRating value={3} />);
    const stars = screen.getAllByRole('button');
    // Check that 3 stars are filled (amber color) and 2 are empty
    const filledStars = stars.filter((star) =>
      star.querySelector('svg')?.classList.contains('text-primary')
    );
    expect(filledStars).toHaveLength(3);
  });

  it('calls onChange when interactive star is clicked', () => {
    const onChange = vi.fn();
    render(<StarRating value={0} interactive onChange={onChange} />);
    const stars = screen.getAllByRole('radio');

    fireEvent.click(stars[3]); // Click 4th star
    expect(onChange).toHaveBeenCalledWith(4);
  });

  it('does not call onChange when not interactive', () => {
    const onChange = vi.fn();
    render(<StarRating value={3} interactive={false} onChange={onChange} />);
    const stars = screen.getAllByRole('button');

    fireEvent.click(stars[2]);
    expect(onChange).not.toHaveBeenCalled();
  });

  it('supports keyboard navigation when interactive', () => {
    const onChange = vi.fn();
    render(<StarRating value={0} interactive onChange={onChange} />);
    const stars = screen.getAllByRole('radio');

    fireEvent.keyDown(stars[1], { key: 'Enter' });
    expect(onChange).toHaveBeenCalledWith(2);
  });

  it('applies size classes correctly', () => {
    const { rerender } = render(<StarRating value={1} size='sm' />);
    let svg = screen.getAllByRole('button')[0].querySelector('svg');
    expect(svg).toHaveClass('w-3.5', 'h-3.5');

    rerender(<StarRating value={1} size='lg' />);
    svg = screen.getAllByRole('button')[0].querySelector('svg');
    expect(svg).toHaveClass('w-5', 'h-5');
  });

  it('applies custom className', () => {
    const { container } = render(<StarRating value={1} className='custom-class' />);
    expect(container.firstChild).toHaveClass('custom-class');
  });
});
