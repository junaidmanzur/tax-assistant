import { FormEvent, useState, useRef } from 'react';
import MessageBubble, { Sender } from './MessageBubble';
import { ChatMessage, ChatRequest } from '@/types/tax';
import TaxResultCard from '@/components/common/TaxResultCard';

// Helper function to format tax calculation results
function formatTaxResponse(text: string): string {
  // Check if the response contains tax calculation results
  const hasBaseRate = /base.tax/i.test(text);
  const hasMedicareLevy = /medicare.levy/i.test(text);
  const hasTotalTax = /total.tax/i.test(text);
  
  if (hasBaseRate && hasMedicareLevy && hasTotalTax) {
    // Extract numbers for formatting
    const baseMatch = text.match(/base.tax[:\s]*\$?([0-9,]+(?:\.[0-9]{2})?)/i);
    const medicareMatch = text.match(/medicare.levy[:\s]*\$?([0-9,]+(?:\.[0-9]{2})?)/i);
    const mlsMatch = text.match(/(?:mls|medicare.levy.surcharge)[:\s]*\$?([0-9,]+(?:\.[0-9]{2})?)/i);
    const totalMatch = text.match(/total.tax[:\s]*\$?([0-9,]+(?:\.[0-9]{2})?)/i);
    const takeHomeMatch = text.match(/take.home[:\s]*\$?([0-9,]+(?:\.[0-9]{2})?)/i);
    
    if (baseMatch && medicareMatch && totalMatch) {
      const base = parseFloat(baseMatch[1].replace(/,/g, ''));
      const medicare = parseFloat(medicareMatch[1].replace(/,/g, ''));
      const mls = mlsMatch ? parseFloat(mlsMatch[1].replace(/,/g, '')) : 0;
      const total = parseFloat(totalMatch[1].replace(/,/g, ''));
      const takeHome = takeHomeMatch ? parseFloat(takeHomeMatch[1].replace(/,/g, '')) : null;
      
      // Format with elegant structure
      let formatted = `**🧮 Tax Calculation Results (2024-25)**\n\n`;
      formatted += `**💰 Your Tax Breakdown:**\n`;
      formatted += `• Base Income Tax: $${base.toLocaleString('en-AU', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}\n`;
      formatted += `• Medicare Levy: $${medicare.toLocaleString('en-AU', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}\n`;
      formatted += `• Medicare Levy Surcharge: $${mls.toLocaleString('en-AU', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}\n`;
      formatted += `• **Total Tax: $${total.toLocaleString('en-AU', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}**\n\n`;
      
      if (takeHome) {
        formatted += `**💵 Take-Home Pay: $${takeHome.toLocaleString('en-AU', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}**\n\n`;
      }
      
      // Extract any explanation about MLS
      const mlsExplanation = text.match(/(?:mls|medicare.levy.surcharge).*?(?:\n\n|$)/is);
      if (mlsExplanation) {
        formatted += `**📋 MLS Details:**\n${mlsExplanation[0].trim()}\n`;
      }
      
      return formatted;
    }
  }
  
  return text;
}

interface TaxResult {
  baseTax: number;
  medicareLevy: number;
  mls: number;
  totalTax: number;
  takeHome: number;
  income: number;
}

interface Msg { 
  sender: Sender; 
  text: string; 
  taxResult?: TaxResult;
}

// Helper function to extract tax results from response
function extractTaxResults(text: string): TaxResult | null {
  
  // Match the actual format: "**Base Tax**: $26,787.54"
  const baseMatch = text.match(/\*\*Base Tax\*\*:\s*\$([0-9,]+(?:\.[0-9]{2})?)/i);
  const medicareMatch = text.match(/\*\*Medicare Levy\*\*:\s*\$([0-9,]+(?:\.[0-9]{2})?)/i);
  const mlsMatch = text.match(/\*\*Medicare Levy Surcharge.*?\*\*:\s*\$([0-9,]+(?:\.[0-9]{2})?)/i);
  const totalMatch = text.match(/\*\*Total Tax Payable\*\*:\s*\$([0-9,]+(?:\.[0-9]{2})?)/i);
  const takeHomeMatch = text.match(/\*\*Take-Home Income\*\*:\s*\$([0-9,]+(?:\.[0-9]{2})?)/i);
  
  // Also try numbered format: "1. **Base Tax**: $26,787.54"
  const numberedBaseMatch = text.match(/\d+\.\s*\*\*Base Tax\*\*:\s*\$([0-9,]+(?:\.[0-9]{2})?)/i);
  const numberedMedicareMatch = text.match(/\d+\.\s*\*\*Medicare Levy\*\*:\s*\$([0-9,]+(?:\.[0-9]{2})?)/i);
  const numberedMlsMatch = text.match(/\d+\.\s*\*\*Medicare Levy Surcharge.*?\*\*:\s*\$([0-9,]+(?:\.[0-9]{2})?)/i);
  const numberedTotalMatch = text.match(/\d+\.\s*\*\*Total Tax Payable\*\*:\s*\$([0-9,]+(?:\.[0-9]{2})?)/i);
  const numberedTakeHomeMatch = text.match(/\d+\.\s*\*\*Take-Home Income\*\*:\s*\$([0-9,]+(?:\.[0-9]{2})?)/i);
  
  const finalBase = baseMatch || numberedBaseMatch;
  const finalMedicare = medicareMatch || numberedMedicareMatch;
  const finalMls = mlsMatch || numberedMlsMatch;
  const finalTotal = totalMatch || numberedTotalMatch;
  const finalTakeHome = takeHomeMatch || numberedTakeHomeMatch;
  
  if (finalBase && finalMedicare && finalTotal && finalTakeHome) {
    const result = {
      baseTax: parseFloat(finalBase[1].replace(/,/g, '')),
      medicareLevy: parseFloat(finalMedicare[1].replace(/,/g, '')),
      mls: finalMls ? parseFloat(finalMls[1].replace(/,/g, '')) : 0,
      totalTax: parseFloat(finalTotal[1].replace(/,/g, '')),
      takeHome: parseFloat(finalTakeHome[1].replace(/,/g, '')),
      income: 0 // Will calculate
    };
    
    // Calculate income
    result.income = result.takeHome + result.totalTax;
    
    return result;
  }
  
  return null;
}

export default function ChatPanel() {
  const [messages, setMessages] = useState<Msg[]>([
    { sender: 'ai', text: 'Hi! I\'ll help you calculate your Australian income tax. Do you have your income information ready for a tax calculation?' },
  ]);

  const [draft, setDraft] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const threadIdRef = useRef('default-thread');

  async function onSend(e: FormEvent) {
    e.preventDefault();
    const text = draft.trim();
    if (!text || isLoading) return;

    // Add user message
    setMessages((m) => [...m, { sender: 'me', text }]);
    setDraft('');
    setIsLoading(true);

    // Add loading indicator
    setMessages((m) => [...m, { sender: 'loading', text: '' }]);

    try {
      // Convert current conversation to ChatMessage format
      const chatMessages: ChatMessage[] = [
        { role: 'system', content: 'You are an Australian tax assistant. Always use the calculate_tax tool for tax calculations.' },
        ...messages.map(msg => ({
          role: msg.sender === 'me' ? 'user' as const : 'assistant' as const,
          content: msg.text
        })),
        { role: 'user', content: text }
      ];

      const requestBody: ChatRequest = {
        messages: chatMessages,
        thread_id: threadIdRef.current
      };

      const apiBase = import.meta.env.VITE_API_BASE || '';
      const response = await fetch(`${apiBase}/api/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No response body');
      }

      let aiResponse = '';
      const decoder = new TextDecoder();

      let buffer = '';
      
      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          
          // Keep the last incomplete line in buffer
          buffer = lines.pop() || '';

          let currentEvent = '';
          let currentData = '';

          for (const line of lines) {
            const trimmedLine = line.trim();
            
            if (trimmedLine.startsWith('event:')) {
              currentEvent = trimmedLine.slice(6).trim();
            } else if (trimmedLine.startsWith('data:')) {
              currentData = trimmedLine.slice(5).trim();
              
              // Process complete event when we have both event and data
              if (currentEvent && currentData) {
                try {
                  // Parse proper JSON from backend
                  const eventData = JSON.parse(currentData);
                  
                  if (currentEvent === 'step' && eventData.ai_content) {
                    aiResponse = eventData.ai_content;
                  } else if (currentEvent === 'done') {
                    setMessages((m) => {
                      const withoutLoading = m.filter(msg => msg.sender !== 'loading');
                      const response = aiResponse || 'I\'m ready to help with your tax calculation!';
                      let taxResult = extractTaxResults(response);
                      const formattedResponse = formatTaxResponse(response);
                      
                      
                      return [...withoutLoading, { 
                        sender: 'ai', 
                        text: formattedResponse,
                        taxResult: taxResult || undefined
                      }];
                    });
                    setIsLoading(false);
                    return;
                  } else if (currentEvent === 'error') {
                    setMessages((m) => {
                      const withoutLoading = m.filter(msg => msg.sender !== 'loading');
                      return [...withoutLoading, { sender: 'ai', text: 'Sorry, I encountered an error. Please try again.' }];
                    });
                    setIsLoading(false);
                    return;
                  }
                } catch (parseErr) {
                  console.error('Error parsing event data:', parseErr, currentData);
                }
                
                // Reset for next event
                currentEvent = '';
                currentData = '';
              }
            }
          }
        }
      } finally {
        reader.releaseLock();
      }

    } catch (error) {
      console.error('Chat error:', error);
      setMessages((m) => {
        const withoutLoading = m.filter(msg => msg.sender !== 'loading');
        return [...withoutLoading, { sender: 'ai', text: 'Sorry, something went wrong. Please try again.' }];
      });
      setIsLoading(false);
    }
  }

  return (
    <section className="panel grid grid-rows-chat h-[72vh] min-h-[560px]" aria-label="Conversation panel">
      <div className="overflow-auto p-4" id="chat">
        {messages.map((m, i) => (
          <div key={i}>
            {m.taxResult ? (
              // Show only the card when tax results are available
              <div className="flex gap-2.5 my-2">
                <div className="w-7 h-7 rounded-full bg-chip flex-none" aria-hidden="true" />
                <TaxResultCard
                  baseTax={m.taxResult.baseTax}
                  medicareLevy={m.taxResult.medicareLevy}
                  mls={m.taxResult.mls}
                  totalTax={m.taxResult.totalTax}
                  takeHome={m.taxResult.takeHome}
                  income={m.taxResult.income}
                />
              </div>
            ) : (
              // Show normal message bubble for non-tax messages
              <MessageBubble sender={m.sender}>
                {m.sender === 'ai' ? m.text : m.text.split('\n').map((line, idx) => <div key={idx}>{line}</div>)}
              </MessageBubble>
            )}
          </div>
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
        <button 
          type="submit" 
          disabled={isLoading}
          className="px-4 h-10 rounded-xl border border-border bg-accent text-[#05121f] font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? 'Sending...' : 'Send'}
        </button>
      </form>
    </section>
  );
}