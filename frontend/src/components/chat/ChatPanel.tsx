import { FormEvent, useState } from 'react';
import MessageBubble, { Sender } from './MessageBubble';

interface Msg { sender: Sender; text: string; }

export default function ChatPanel() {
  const [messages, setMessages] = useState<Msg[]>([
    { sender: 'ai', text: 'Hi, I’m your AI Tax Assistant. I can calculate your exact annual tax. Please tell me your taxable income for this year.' },
  ]);

  const [draft, setDraft] = useState('');

  async function onSend(e: FormEvent) {
    e.preventDefault();
    const text = draft.trim();
    if (!text) return;

    setMessages((m) => [...m, { sender: 'me', text }]);
    setDraft('');

    // Basic demo behavior: echo + hint. Real chat should call your chat backend here.
    setMessages((m) => [...m, { sender: 'ai', text: 'Thanks! Use the form on the right to run the exact calculation.' }]);
  }

  return (
    <section className="panel grid grid-rows-chat h-[72vh] min-h-[560px]" aria-label="Conversation panel">
      <div className="overflow-auto p-4" id="chat">
        {messages.map((m, i) => (
          <MessageBubble key={i} sender={m.sender}>{m.text.split('\n').map((line, idx) => <div key={idx}>{line}</div>)}</MessageBubble>
        ))}
      </div>
      <form onSubmit={onSend} className="flex gap-2.5 p-2.5 border-t border-border">
        <label htmlFor="chatInput" className="sr-only">Message</label>
        <input
          id="chatInput"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="Type a message (e.g., 85000)…"
          aria-label="Chat message"
          className="flex-1 px-3.5 py-3 rounded-xl border border-border bg-[#0f1117] text-text outline-none focus:ring-2 focus:ring-accent/40"
        />
        <button type="submit" className="px-4 h-10 rounded-xl border border-border bg-accent text-[#05121f] font-semibold">Send</button>
      </form>
    </section>
  );
}