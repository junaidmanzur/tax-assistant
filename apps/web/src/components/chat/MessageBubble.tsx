import { ReactNode } from 'react';

export type Sender = 'ai' | 'me' | 'sys' | 'loading';

// Helper function to render simple markdown formatting
function renderFormattedText(text: string): ReactNode {
  // Split by lines first
  const lines = text.split('\n');
  
  return lines.map((line, index) => {
    if (!line.trim()) {
      return <br key={index} />;
    }
    
    // Process inline formatting
    let processedLine = line
      // Bold text **text** 
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      // Bullet points
      .replace(/^• (.*)/, '&nbsp;&nbsp;• $1');
    
    return (
      <div key={index} dangerouslySetInnerHTML={{ __html: processedLine }} />
    );
  });
}

export default function MessageBubble({ sender, children }: { sender: Sender; children: ReactNode }) {
  const isMe = sender === 'me';
  const isSys = sender === 'sys';
  const isLoading = sender === 'loading';
  const isAi = sender === 'ai';
  
  return (
    <div className={`flex gap-2.5 my-2 ${isMe ? 'justify-start' : ''}`}>
      <div className="w-7 h-7 rounded-full bg-chip flex-none" aria-hidden="true" />
      <div className={`bubble ${isMe ? 'bubble-me' : ''} ${isSys ? 'text-muted text-sm' : ''}`}>
        {isLoading ? (
          <div className="flex items-center gap-1">
            <span className="animate-pulse">Thinking</span>
            <div className="flex gap-1">
              <div className="w-1 h-1 bg-current rounded-full animate-bounce" style={{animationDelay: '0ms'}}></div>
              <div className="w-1 h-1 bg-current rounded-full animate-bounce" style={{animationDelay: '150ms'}}></div>
              <div className="w-1 h-1 bg-current rounded-full animate-bounce" style={{animationDelay: '300ms'}}></div>
            </div>
          </div>
        ) : (
          isAi && typeof children === 'string' ? renderFormattedText(children) : children
        )}
      </div>
    </div>
  );
}