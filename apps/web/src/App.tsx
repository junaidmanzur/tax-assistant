import { useState } from 'react';
import ChatPanel from '@/components/chat/ChatPanel';
import FormPanel from '@/components/form/FormPanel';

interface TaxCalculation {
  income: number;
  baseTax: number;
  medicareLevy: number;
  mls: number;
  totalTax: number;
  takeHome: number;
  filingStatus: 'single' | 'family';
  combinedFamilyIncome?: number;
  numChildren?: number;
  hasPrivateHealth: boolean;
}

export default function App() {
  const [activePanel, setActivePanel] = useState<'chat' | 'form'>('chat');
  const [lastTaxCalculation, setLastTaxCalculation] = useState<TaxCalculation | null>(null);

  return (
    <div className="min-h-screen">
      <header className="panel border-b border-border px-5 py-6">
        <div className="max-w-[1200px] mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-[22px] font-bold tracking-[0.2px]">AI Tax Assistant</h1>
            <p className="text-muted mt-1">Get your exact tax calculation in minutes.</p>
          </div>
          
          {/* Mobile toggle - only visible on smaller screens */}
          <div className="md:hidden">
            <div className="flex rounded-xl border border-border bg-[#0f1117] p-1">
              <button
                onClick={() => setActivePanel('chat')}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  activePanel === 'chat'
                    ? 'bg-accent text-[#05121f]'
                    : 'text-muted hover:text-text'
                }`}
              >
                Chat
              </button>
              <button
                onClick={() => setActivePanel('form')}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  activePanel === 'form'
                    ? 'bg-accent text-[#05121f]'
                    : 'text-muted hover:text-text'
                }`}
              >
                Form
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-[1200px] mx-auto p-4">
        {/* Desktop: Side-by-side layout */}
        <div className="hidden md:grid md:grid-cols-[1.4fr_1fr] gap-4">
          <ChatPanel onTaxCalculation={setLastTaxCalculation} />
          <FormPanel syncedCalculation={lastTaxCalculation} />
        </div>

        {/* Mobile: Toggled single panel */}
        <div className="md:hidden">
          {activePanel === 'chat' ? (
            <ChatPanel onTaxCalculation={setLastTaxCalculation} />
          ) : (
            <FormPanel syncedCalculation={lastTaxCalculation} />
          )}
        </div>
      </main>

      <footer className="text-muted text-xs p-4 border-t border-border text-center">
        © 2025 — AI Tax Assistant (MVP). No personal data is stored in this demo.
      </footer>
    </div>
  );
}