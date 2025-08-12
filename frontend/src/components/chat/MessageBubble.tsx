import { ReactNode } from 'react';

export type Sender = 'ai' | 'me' | 'sys';

export default function MessageBubble({ sender, children }: { sender: Sender; children: ReactNode }) {
  const isMe = sender === 'me';
  const isSys = sender === 'sys';
  return (
    <div className={`flex gap-2.5 my-2 ${isMe ? 'justify-start' : ''}`}>
      <div className="w-7 h-7 rounded-full bg-chip flex-none" aria-hidden="true" />
      <div className={`bubble ${isMe ? 'bubble-me' : ''} ${isSys ? 'text-muted text-sm' : ''}`}>{children}</div>
    </div>
  );
}