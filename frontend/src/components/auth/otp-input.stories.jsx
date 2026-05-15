import { OtpInput } from './otp-input';

export default {
  title: 'Auth/OtpInput',
  component: OtpInput,
  tags: ['autodocs'],
  argTypes: {
    value: { control: 'text' },
    onChange: { action: 'changed' },
    disabled: { control: 'boolean' },
    error: { control: 'boolean' },
  },
};

export const Default = {
  args: {
    value: '',
    disabled: false,
    error: false,
  },
};

export const Filled = {
  args: {
    value: '123456',
    disabled: false,
    error: false,
  },
};

export const PartiallyFilled = {
  args: {
    value: '123',
    disabled: false,
    error: false,
  },
};

export const Error = {
  args: {
    value: '123456',
    disabled: false,
    error: true,
  },
};

export const Disabled = {
  args: {
    value: '123456',
    disabled: true,
    error: false,
  },
};

export const Focused = {
  render: (args) => {
    return (
      <div className='p-4'>
        <p className='text-sm text-gray-500 mb-4'>Click on any box to see the focused state</p>
        <OtpInput {...args} />
      </div>
    );
  },
  args: {
    value: '',
    disabled: false,
    error: false,
  },
};
