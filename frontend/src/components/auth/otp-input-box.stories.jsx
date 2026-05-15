import { OtpInputBox } from './otp-input-box';

export default {
  title: 'Auth/OtpInputBox',
  component: OtpInputBox,
  tags: ['autodocs'],
  argTypes: {
    value: { control: 'text' },
    disabled: { control: 'boolean' },
    error: { control: 'boolean' },
  },
};

export const Empty = {
  args: {
    index: 0,
    value: '',
    onChange: () => {},
    onKeyDown: () => {},
    onFocus: () => {},
    disabled: false,
    error: false,
  },
};

export const Filled = {
  args: {
    index: 0,
    value: '5',
    onChange: () => {},
    onKeyDown: () => {},
    onFocus: () => {},
    disabled: false,
    error: false,
  },
};

export const Focused = {
  render: (args) => {
    return (
      <div className='p-4'>
        <p className='text-sm text-gray-500 mb-4'>
          This box is auto-focused on mount when it's the first box and empty
        </p>
        <OtpInputBox {...args} />
      </div>
    );
  },
  args: {
    index: 0,
    value: '',
    onChange: () => {},
    onKeyDown: () => {},
    onFocus: () => {},
    disabled: false,
    error: false,
  },
};

export const Error = {
  args: {
    index: 0,
    value: 'X',
    onChange: () => {},
    onKeyDown: () => {},
    onFocus: () => {},
    disabled: false,
    error: true,
  },
};

export const Disabled = {
  args: {
    index: 0,
    value: '5',
    onChange: () => {},
    onKeyDown: () => {},
    onFocus: () => {},
    disabled: true,
    error: false,
  },
};
