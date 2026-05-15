import { PasswordStrengthMeter } from './password-strength-meter';

export default {
  title: 'Auth/PasswordStrengthMeter',
  component: PasswordStrengthMeter,
  tags: ['autodocs'],
};

export const Weak = {
  args: {
    password: 'weak',
  },
};

export const Medium = {
  args: {
    password: 'Medium1',
  },
};

export const Strong = {
  args: {
    password: 'Str0ng!Pass',
  },
};

export const Empty = {
  args: {
    password: '',
  },
};
