import { FormEvent, useState, useRef } from 'react';
import MessageBubble, { Sender } from './MessageBubble';
import { ChatMessage, ChatRequest } from '@types/tax';

interface Msg { sender: Sender; text: string; }

export default function ChatPanel() {
  const [messages, setMessages] = useState<Msg[]>([
    { sender: 'ai', text: 'Hi, I\'m your AI Tax Assistant. I can calculate your exact annual tax. Please tell me your taxable income for this year.' },
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
                      return [...withoutLoading, { sender: 'ai', text: aiResponse || 'I\'m ready to help with your tax calculation!' }];
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