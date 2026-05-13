import ForgotPasswordPage from './ForgotPasswordPage';

export default {
  title: 'Auth/ForgotPasswordPage',
  component: ForgotPasswordPage,
  tags: ['autodocs'],
  parameters: {
    layout: 'fullscreen',
  },
};

export const Default = {
  args: {},
};

export const WithPrefilledEmail = {
  args: {
    email: 'user@example.com',
  },
};

export const Submitting = {
  args: {
    isSubmitting: true,
    email: 'user@example.com',
  },
};

export const Success = {
  args: {
    success: true,
    email: 'user@example.com',
  },
};

export const Error = {
  args: {
    error: 'No account found with this email address',
    email: 'nonexistent@example.com',
  },
};

export const ResendCooldown = {
  args: {
    success: true,
    email: 'user@example.com',
    cooldown: 25,
  },
};
