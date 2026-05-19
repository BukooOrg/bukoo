import React, { useMemo } from 'react';

import { cn } from '@/lib/utils';

const strengthLevels = [
  { level: 0, label: 'Weak', color: 'bg-destructive', textColor: 'text-destructive' },
  {
    level: 1,
    label: 'Medium',
    color: 'bg-amber-500',
    textColor: 'text-amber-700',
  },
  { level: 2, label: 'Strong', color: 'bg-green-600', textColor: 'text-green-600' },
];

function calculateStrength(password) {
  if (!password) return 0;

  let score = 0;
  if (password.length >= 8) score++;
  if (/[A-Z]/.test(password)) score++;
  if (/[a-z]/.test(password)) score++;
  if (/[0-9]/.test(password)) score++;
  if (/[^A-Za-z0-9]/.test(password)) score++;

  if (score <= 2) return 0;
  if (score <= 3) return 1;
  return 2;
}

export function PasswordStrengthMeter({ password }) {
  const strength = useMemo(() => calculateStrength(password), [password]);
  const level = strengthLevels[strength];

  if (!password) return null;

  return (
    <div className='mt-2 space-y-1'>
      <div className='flex gap-1'>
        {strengthLevels.map((_, index) => (
          <div
            key={index}
            className={cn(
              'h-1.5 flex-1 rounded-full transition-colors duration-300',
              index <= strength ? level.color : 'bg-primary/10'
            )}
          />
        ))}
      </div>
      <p className={cn('text-xs font-bold transition-colors', level.textColor)}>{level.label}</p>
    </div>
  );
}
