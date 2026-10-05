import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Loader2, X, MessageSquare } from 'lucide-react';
import { ChatMessage } from '../types/report';
import { streamChat } from '../lib/api';

interface ChatPanelProps {
  owner: string;
  repo: string;
  sha: string;
  isOpen: boolean;
  onClose: () => void;
}

export const ChatPanel: React.FC<ChatPanelProps> = ({
  owner,
  repo,
  sha,
  isOpen,
  onClose,
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: `Hello! I've indexed the code for **${owner}/${repo}**. Ask me anything about how the system works, entry points, authentication, or specific endpoints.`,
    },
  ]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    const q = input.trim();
    if (!q || isStreaming) return;

    setInput('');
    const userMsg: ChatMessage = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: q,
    };

    const assistantId = `assistant-${Date.now()}`;
    const initialAssistantMsg: ChatMessage = {
      id: assistantId,
      role: 'assistant',
      content: '',
      citations: [],
    };

    setMessages((prev) => [...prev, userMsg, initialAssistantMsg]);
    setIsStreaming(true);

    try {
      const history = messages
        .filter((m) => m.id !== 'welcome')
        .map((m) => ({ role: m.role, content: m.content }));

      await streamChat(
        owner,
        repo,
        sha,
        q,
        history,
        (token) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId ? { ...m, content: m.content + token } : m
            )
          );
        },
        (citations) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId ? { ...m, citations } : m
            )
          );
        }
      );
    } catch (err: any) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantId
            ? { ...m, content: `Error: ${err.message || 'Failed to retrieve answer.'}` }
            : m
        )
      );
    } finally {
      setIsStreaming(false);
    }
  };

  const sampleQuestions = [
    'How does request handling work?',
    'What databases or schemas are used?',
    'Explain the entry point and startup flow',
  ];

  if (!isOpen) return null;

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-full sm:w-[480px] bg-surface border-l border-border shadow-2xl flex flex-col transition-all duration-200">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-border bg-surface-2/40">
        <div className="flex items-center gap-2">
          <MessageSquare className="w-4 h-4 text-primary" />
          <h3 className="text-sm font-semibold text-text">Repo Chat (RAG)</h3>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="p-1.5 rounded-lg text-text-muted hover:text-text hover:bg-surface-2 transition-colors cursor-pointer"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((m) => (
          <div
            key={m.id}
            className={`flex gap-3 ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            {m.role === 'assistant' && (
              <div className="w-7 h-7 rounded-full bg-primary/20 text-primary flex items-center justify-center shrink-0 mt-0.5">
                <Bot className="w-4 h-4" />
              </div>
            )}

            <div
              className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-xs sm:text-sm leading-relaxed ${
                m.role === 'user'
                  ? 'bg-primary text-white rounded-br-none'
                  : 'bg-surface-2 text-text border border-border rounded-bl-none'
              }`}
            >
              <div className="whitespace-pre-wrap">{m.content}</div>

              {/* Citations */}
              {m.citations && m.citations.length > 0 && (
                <div className="mt-3 pt-2 border-t border-border/40 space-y-1">
                  <div className="text-[10px] font-semibold text-text-muted uppercase tracking-wider">
                    Cited Sources:
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {m.citations.map((c, i) => (
                      <span
                        key={i}
                        className="px-2 py-0.5 rounded bg-surface border border-border font-mono text-[10px] text-accent"
                      >
                        {c.file_path}:{c.start_line}-{c.end_line}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {m.role === 'user' && (
              <div className="w-7 h-7 rounded-full bg-surface-2 text-text-muted flex items-center justify-center shrink-0 mt-0.5 border border-border">
                <User className="w-4 h-4" />
              </div>
            )}
          </div>
        ))}
        {isStreaming && (
          <div className="flex items-center gap-2 text-xs text-text-muted pl-10">
            <Loader2 className="w-3.5 h-3.5 animate-spin text-primary" />
            <span>Analyzing repository chunks...</span>
          </div>
        )}
        <div ref={scrollRef} />
      </div>

      {/* Suggested Questions */}
      {messages.length === 1 && (
        <div className="px-4 pb-2">
          <div className="text-[11px] text-text-muted mb-1.5">Suggested queries:</div>
          <div className="flex flex-col gap-1.5">
            {sampleQuestions.map((q) => (
              <button
                key={q}
                type="button"
                onClick={() => {
                  setInput(q);
                }}
                className="text-left text-xs p-2 rounded-lg bg-surface-2 hover:bg-border/60 text-text transition-colors border border-border/50 cursor-pointer"
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input Box */}
      <form onSubmit={handleSend} className="p-4 border-t border-border bg-surface-2/20 flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question about the repo..."
          disabled={isStreaming}
          className="flex-1 px-3.5 py-2.5 rounded-xl bg-surface border border-border text-xs sm:text-sm text-text placeholder:text-text-muted focus:outline-none focus:border-primary font-sans"
        />
        <button
          type="submit"
          disabled={!input.trim() || isStreaming}
          className="px-4 py-2.5 rounded-xl bg-primary hover:bg-primary-hover disabled:opacity-50 text-white transition-colors flex items-center justify-center cursor-pointer"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
};
