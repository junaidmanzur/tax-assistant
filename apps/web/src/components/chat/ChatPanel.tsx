import { FormEvent, useState, useRef } from 'react';
import MessageBubble, { Sender } from './MessageBubble';
import { ChatMessage, ChatRequest, TaxCalculation } from '@/types/tax';
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
  lito: number;
  totalTax: number;
  takeHome: number;
  income: number;
}

interface Msg { 
  sender: Sender; 
  text: string; 
  taxResult?: TaxResult;
}

// Helper function to filter out tax calculation lines from text
function filterTaxCalculationLines(text: string): string {
  // Remove lines that contain tax calculation results
  const lines = text.split('\n');
  const filteredLines = lines.filter(line => {
    // Keep lines that don't match tax calculation patterns
    return !(
      /\*\*Base Tax\*\*:\s*\$/.test(line) ||
      /\*\*Medicare Levy\*\*:\s*\$/.test(line) ||
      /\*\*Medicare Levy Surcharge.*?\*\*:\s*\$/.test(line) ||
      /\*\*Total Tax Payable\*\*:\s*\$/.test(line) ||
      /\*\*Take-Home Income\*\*:\s*\$/.test(line) ||
      /\d+\.\s*\*\*Base Tax\*\*:\s*\$/.test(line) ||
      /\d+\.\s*\*\*Medicare Levy\*\*:\s*\$/.test(line) ||
      /\d+\.\s*\*\*Medicare Levy Surcharge.*?\*\*:\s*\$/.test(line) ||
      /\d+\.\s*\*\*Total Tax Payable\*\*:\s*\$/.test(line) ||
      /\d+\.\s*\*\*Take-Home Income\*\*:\s*\$/.test(line)
    );
  });
  
  return filteredLines.join('\n').trim();
}

// Helper function to extract tax results from response
function extractTaxResults(text: string): TaxResult | null {
  
  // Match the actual format: "**Base Tax**: $26,787.54"
  const baseMatch = text.match(/\*\*Base Tax\*\*:\s*\$([0-9,]+(?:\.[0-9]{2})?)/i);
  const medicareMatch = text.match(/\*\*Medicare Levy\*\*:\s*\$([0-9,]+(?:\.[0-9]{2})?)/i);
  const mlsMatch = text.match(/\*\*Medicare Levy Surcharge.*?\*\*:\s*\$([0-9,]+(?:\.[0-9]{2})?)/i);
  const litoMatch = text.match(/\*\*Low Income Tax Offset\*\*:\s*-?\$([0-9,]+(?:\.[0-9]{2})?)/i);
  const totalMatch = text.match(/\*\*Total Tax Payable\*\*:\s*\$([0-9,]+(?:\.[0-9]{2})?)/i);
  const takeHomeMatch = text.match(/\*\*Take-Home Income\*\*:\s*\$([0-9,]+(?:\.[0-9]{2})?)/i);
  
  // Also try numbered format: "1. **Base Tax**: $26,787.54"
  const numberedBaseMatch = text.match(/\d+\.\s*\*\*Base Tax\*\*:\s*\$([0-9,]+(?:\.[0-9]{2})?)/i);
  const numberedMedicareMatch = text.match(/\d+\.\s*\*\*Medicare Levy\*\*:\s*\$([0-9,]+(?:\.[0-9]{2})?)/i);
  const numberedMlsMatch = text.match(/\d+\.\s*\*\*Medicare Levy Surcharge.*?\*\*:\s*\$([0-9,]+(?:\.[0-9]{2})?)/i);
  const numberedLitoMatch = text.match(/\d+\.\s*\*\*Low Income Tax Offset\*\*:\s*-?\$([0-9,]+(?:\.[0-9]{2})?)/i);
  const numberedTotalMatch = text.match(/\d+\.\s*\*\*Total Tax Payable\*\*:\s*\$([0-9,]+(?:\.[0-9]{2})?)/i);
  const numberedTakeHomeMatch = text.match(/\d+\.\s*\*\*Take-Home Income\*\*:\s*\$([0-9,]+(?:\.[0-9]{2})?)/i);
  
  const finalBase = baseMatch || numberedBaseMatch;
  const finalMedicare = medicareMatch || numberedMedicareMatch;
  const finalMls = mlsMatch || numberedMlsMatch;
  const finalLito = litoMatch || numberedLitoMatch;
  const finalTotal = totalMatch || numberedTotalMatch;
  const finalTakeHome = takeHomeMatch || numberedTakeHomeMatch;
  
  if (finalBase && finalMedicare && finalTotal && finalTakeHome) {
    const result = {
      baseTax: parseFloat(finalBase[1].replace(/,/g, '')),
      medicareLevy: parseFloat(finalMedicare[1].replace(/,/g, '')),
      mls: finalMls ? parseFloat(finalMls[1].replace(/,/g, '')) : 0,
      lito: finalLito ? parseFloat(finalLito[1].replace(/,/g, '')) : 0,
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

interface ChatPanelProps {
  onTaxCalculation?: (calculation: TaxCalculation) => void;
}

export default function ChatPanel({ onTaxCalculation }: ChatPanelProps) {
  const [messages, setMessages] = useState<Msg[]>([
    { sender: 'ai', text: '👋 **Quick Tax Calculator**\n\nJust tell me your income and I\'ll calculate your 2024-25 Australian tax!\n\n**Examples:**\n• "85,000 salary"\n• "120k, married, 2 kids, family income 200k"\n• "95000, single, no private health"\n\n**What\'s your situation?**' },
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
                      
                      // Remove JSON block from display (it's only for data extraction)
                      const cleanedResponse = response
                        .replace(/```json\s*\{[\s\S]*?\}\s*```/g, '')  // Standard JSON blocks
                        .replace(/```\s*\{\s*[\s\S]*?\}\s*```/g, '')   // JSON blocks without 'json' label
                        .replace(/\{\s*"taxCalculation"[\s\S]*?\}\s*$/g, '') // Bare JSON at end
                        .trim();
                      const formattedResponse = formatTaxResponse(cleanedResponse);
                      
                      // First try to extract JSON data from the response
                      let jsonTaxData = null;
                      try {
                        // Try multiple JSON patterns
                        const patterns = [
                          /```json\s*(\{[\s\S]*?\})\s*```/,     // Standard JSON blocks
                          /```\s*(\{[\s\S]*?\})\s*```/,        // JSON blocks without 'json' label
                          /(\{\s*"taxCalculation"[\s\S]*?\})/   // Bare JSON
                        ];
                        
                        let jsonMatch = null;
                        for (const pattern of patterns) {
                          jsonMatch = response.match(pattern);
                          if (jsonMatch) break;
                        }
                        
                        if (jsonMatch) {
                          const jsonData = JSON.parse(jsonMatch[1]);
                          if (jsonData.taxCalculation) {
                            jsonTaxData = jsonData.taxCalculation;
                          }
                        }
                      } catch (error) {
                        console.log('Could not parse JSON tax data, falling back to text parsing');
                      }

                      // If tax results are extracted, notify parent component for FormPanel sync
                      if ((taxResult || jsonTaxData) && onTaxCalculation) {
                        // Get the most recent user message that triggered this calculation
                        const allMessages = [...withoutLoading];
                        const recentUserMessages = allMessages.filter(msg => msg.sender === 'me').slice(-3); // Last 3 user messages
                        const userInputText = recentUserMessages.map(msg => msg.text).join(' ');
                        
                        // Extract filing status from user input patterns
                        const hasMarriedKeywords = /\b(?:married|spouse|partner|wife|husband)\b/i.test(userInputText);
                        const hasKidsNumbers = /\b(?:\d+)\s*(?:kids?|children|child)\b/i.test(userInputText);
                        const hasSingleKeyword = /\bsingle\b/i.test(userInputText);
                        const hasNoKidsKeyword = /\b(?:no|0)\s*(?:kids?|children)\b/i.test(userInputText);
                        
                        const filingStatus = (hasMarriedKeywords || (hasKidsNumbers && !hasNoKidsKeyword)) && !hasSingleKeyword ? 'family' : 'single';
                        
                        // Extract private health from user input patterns
                        const hasPrivateHealthYes = /\b(?:have|has|with|yes).*private.*health\b/i.test(userInputText) ||
                                                   /\bprivate.*health\b/i.test(userInputText) && !/\bno\b/i.test(userInputText);
                        const hasPrivateHealthNo = /\b(?:no|without|don't\s+have).*private.*health\b/i.test(userInputText) ||
                                                  /\bno.*private.*health\b/i.test(userInputText);
                        const hasPrivateHealth = hasPrivateHealthYes && !hasPrivateHealthNo;
                        
                        // Extract combined family income and children from user input
                        const conversationText = userInputText;
                        
                        let combinedFamilyIncome: number | undefined;
                        if (filingStatus === 'family') {
                          const familyIncomeMatch = conversationText.match(/(?:family.*income|combined.*income|total.*income)[:\s]*(?:\$)?([0-9,]+(?:k|000)?)/i);
                          
                          if (familyIncomeMatch) {
                            const incomeStr = familyIncomeMatch[1].replace(/,/g, '');
                            combinedFamilyIncome = incomeStr.includes('k') ? 
                              parseFloat(incomeStr.replace('k', '')) * 1000 : 
                              parseFloat(incomeStr);
                          }
                        }
                        
                        // Extract number of children from conversation
                        let numChildren = 0;
                        const childrenMatch = conversationText.match(/(\d+)\s*(?:kids?|children|child)/i);
                        if (childrenMatch && !/no.*(?:kids?|children)|0\s+(?:kids?|children)/i.test(conversationText)) {
                          numChildren = parseInt(childrenMatch[1]);
                        }
                        
                        // Use JSON data if available, otherwise fall back to parsed text
                        if (jsonTaxData) {
                          onTaxCalculation({
                            income: jsonTaxData.income,
                            baseTax: jsonTaxData.baseTax,
                            medicareLevy: jsonTaxData.medicareLevy,
                            mls: jsonTaxData.mls,
                            lito: jsonTaxData.lito,
                            totalTax: jsonTaxData.totalTax,
                            takeHome: jsonTaxData.takeHome,
                            filingStatus: jsonTaxData.filingStatus,
                            combinedFamilyIncome: jsonTaxData.combinedFamilyIncome,
                            numChildren: jsonTaxData.numChildren,
                            hasPrivateHealth: jsonTaxData.hasPrivateHealth,
                          });
                        } else if (taxResult) {
                          onTaxCalculation({
                            income: taxResult.income,
                            baseTax: taxResult.baseTax,
                            medicareLevy: taxResult.medicareLevy,
                            mls: taxResult.mls,
                            lito: taxResult.lito,
                            totalTax: taxResult.totalTax,
                            takeHome: taxResult.takeHome,
                            filingStatus,
                            combinedFamilyIncome,
                            numChildren,
                            hasPrivateHealth,
                          });
                        }
                      }
                      
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
              // Show both card and explanation text when tax results are available
              <>
                <div className="flex gap-2.5 my-2">
                  <div className="w-7 h-7 rounded-full bg-chip flex-none" aria-hidden="true" />
                  <TaxResultCard
                    baseTax={m.taxResult.baseTax}
                    medicareLevy={m.taxResult.medicareLevy}
                    mls={m.taxResult.mls}
                    lito={m.taxResult.lito}
                    totalTax={m.taxResult.totalTax}
                    takeHome={m.taxResult.takeHome}
                    income={m.taxResult.income}
                  />
                </div>
                {/* Show explanation text below the card (filtered to remove duplicate tax numbers) */}
                <MessageBubble sender={m.sender}>
                  {m.sender === 'ai' 
                    ? filterTaxCalculationLines(m.text).split('\n').map((line, idx) => <div key={idx}>{line}</div>)
                    : m.text.split('\n').map((line, idx) => <div key={idx}>{line}</div>)
                  }
                </MessageBubble>
              </>
            ) : (
              // Show normal message bubble for non-tax messages
              <MessageBubble sender={m.sender}>
                {m.sender === 'ai' ? m.text : m.text.split('\n').map((line, idx) => <div key={idx}>{line}</div>)}
              </MessageBubble>
            )}
          </div>
        ))}
      </div>
      <div className="border-t border-border p-2.5">
        {/* Quick Action Buttons */}
        <div className="flex gap-2 mb-3 flex-wrap">
          <button 
            onClick={() => setDraft("85000, single")}
            className="px-3 py-1.5 text-sm rounded-lg border border-border bg-[#0f1117] text-muted hover:text-text hover:border-accent/40 transition-colors"
          >
            💼 $85k Single
          </button>
          <button 
            onClick={() => setDraft("120k, married, 2 kids")}
            className="px-3 py-1.5 text-sm rounded-lg border border-border bg-[#0f1117] text-muted hover:text-text hover:border-accent/40 transition-colors"
          >
            👨‍👩‍👧‍👦 $120k Family
          </button>
          <button 
            onClick={() => setDraft("95000, no private health")}
            className="px-3 py-1.5 text-sm rounded-lg border border-border bg-[#0f1117] text-muted hover:text-text hover:border-accent/40 transition-colors"
          >
            💰 $95k No Insurance
          </button>
        </div>

        <form onSubmit={onSend} className="flex gap-2.5">
          <label htmlFor="chatInput" className="sr-only">Message</label>
          <input
            id="chatInput"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder="e.g., '85000, single' or '120k, married, 2 kids, family income 200k'..."
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
      </div>
    </section>
  );
}