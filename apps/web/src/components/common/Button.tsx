import { ButtonHTMLAttributes } from 'react';

type Props = ButtonHTMLAttributes<HTMLButtonElement> & { loading?: boolean };

export default function Button({ className = '', loading, children, ...rest }: Props) {
  return (
    <button
      className={`px-4 h-10 rounded-xl border border-border bg-accent text-[#05121f] font-semibold disabled:opacity-60 ${className}`}
      {...rest}
      disabled={loading || rest.disabled}
    >
      {loading ? '…' : children}
    </button>
  );
}