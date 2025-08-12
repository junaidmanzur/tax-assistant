import ChatPanel from '@components/chat/ChatPanel';
import FormPanel from '@components/form/FormPanel';

export default function App() {
  return (
    <div className="min-h-screen">
      <header className="panel border-b border-border px-5 py-6">
        <h1 className="text-[22px] font-bold tracking-[0.2px]">AI Tax Assistant</h1>
        <p className="text-muted mt-1">Get your exact tax calculation in minutes.</p>
      </header>

      <main className="max-w-[1200px] mx-auto grid gap-4 p-4 grid-cols-[1.4fr_1fr] grid-cols-1 md:grid-cols-[1.4fr_1fr]">
        <ChatPanel />
        <FormPanel />
      </main>

      <footer className="text-muted text-xs p-4 border-t border-border">© 2025 — AI Tax Assistant (MVP). No personal data is stored in this demo.</footer>
    </div>
  );
}