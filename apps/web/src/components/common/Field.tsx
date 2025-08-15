import { ReactNode } from 'react';

interface Props {
  label: string;
  htmlFor?: string;
  hint?: string;
  error?: string | null;
  children: ReactNode;
}

export default function Field({ label, htmlFor, hint, error, children }: Props) {
  return (
    <div className="grid gap-1.5">
      <label htmlFor={htmlFor} className="font-semibold text-sm text-[#cfd3da]">{label}</label>
      {children}
      {hint && <p className="text-muted text-xs">{hint}</p>}
      {error && <p className="text-[#ff7a7a] text-sm" role="alert">{error}</p>}
    </div>
  );
}