"use client";

import { useState, useRef, useEffect } from "react";
import { sendChatMessage, ChatResponse } from "@/lib/api";

type Message = {
  role: "user" | "assistant";
  content: string;
  research?: ChatResponse["research"];
  discussions?: ChatResponse["discussions"];
};

const SUGGESTIONS = [
  "I want to create a machine assistant that gives insights via sensor data",
  "What tools should I use for real-time video analysis?",
  "How to build a RAG system for document search?",
  "Latest techniques for edge AI deployment",
];

export default function Chatbot() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async (text?: string) => {
    const question = text || input.trim();
    if (!question) return;

    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: question }]);
    setLoading(true);

    try {
      const response = await sendChatMessage(question);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: response.answer,
          research: response.research,
          discussions: response.discussions,
        },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Sorry, something went wrong. Please try again." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {/* Floating Chat Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed bottom-6 right-6 z-50 flex h-14 w-14 items-center justify-center rounded-full bg-black text-white shadow-lg transition hover:bg-gray-800"
      >
        {isOpen ? (
          <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        ) : (
          <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
        )}
      </button>

      {/* Chat Window */}
      {isOpen && (
        <div className="fixed bottom-24 right-6 z-50 flex h-[500px] w-[380px] flex-col overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-2xl">
          {/* Header */}
          <div className="border-b border-gray-200 bg-black px-4 py-3">
            <h3 className="text-sm font-semibold text-white">Research Assistant</h3>
            <p className="text-xs text-gray-400">Ask about papers, tools, or techniques</p>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 && (
              <div className="space-y-3">
                <p className="text-sm text-gray-500">Try asking:</p>
                {SUGGESTIONS.map((s, i) => (
                  <button
                    key={i}
                    onClick={() => handleSend(s)}
                    className="w-full rounded-lg border border-gray-200 px-3 py-2 text-left text-sm text-gray-700 transition hover:bg-gray-50"
                  >
                    {s}
                  </button>
                ))}
              </div>
            )}

            {messages.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                <div
                  className={`max-w-[85%] rounded-2xl px-4 py-2 ${
                    msg.role === "user"
                      ? "bg-black text-white"
                      : "bg-gray-100 text-gray-900"
                  }`}
                >
                  <p className="text-sm whitespace-pre-wrap">{msg.content}</p>

                  {/* Research Results */}
                  {msg.research && msg.research.length > 0 && (
                    <div className="mt-3 space-y-2">
                      {msg.research.map((r, j) => (
                        <a
                          key={j}
                          href={r.url}
                          target="_blank"
                          rel="noreferrer"
                          className="block rounded-lg border border-gray-200 bg-white p-2 transition hover:bg-gray-50"
                        >
                          <p className="text-xs font-semibold text-black line-clamp-1">{r.title}</p>
                          <p className="text-xs text-gray-500 line-clamp-1">{r.why}</p>
                          <div className="mt-1 flex gap-1">
                            {r.topics.slice(0, 2).map((t) => (
                              <span key={t} className="rounded-full bg-gray-100 px-2 py-0.5 text-[10px] text-gray-600">
                                {t}
                              </span>
                            ))}
                          </div>
                        </a>
                      ))}
                    </div>
                  )}

                  {/* Discussion Results */}
                  {msg.discussions && msg.discussions.length > 0 && (
                    <div className="mt-2 space-y-1">
                      {msg.discussions.map((d, j) => (
                        <a
                          key={j}
                          href={d.url}
                          target="_blank"
                          rel="noreferrer"
                          className="block text-xs text-blue-600 hover:underline"
                        >
                          {d.title}
                        </a>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex justify-start">
                <div className="rounded-2xl bg-gray-100 px-4 py-2">
                  <div className="flex space-x-1">
                    <div className="h-2 w-2 animate-bounce rounded-full bg-gray-400" style={{ animationDelay: "0ms" }} />
                    <div className="h-2 w-2 animate-bounce rounded-full bg-gray-400" style={{ animationDelay: "150ms" }} />
                    <div className="h-2 w-2 animate-bounce rounded-full bg-gray-400" style={{ animationDelay: "300ms" }} />
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="border-t border-gray-200 p-3">
            <div className="flex gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSend()}
                placeholder="Ask about papers, tools, techniques..."
                className="flex-1 rounded-full border border-gray-300 px-4 py-2 text-sm focus:border-black focus:outline-none"
                disabled={loading}
              />
              <button
                onClick={() => handleSend()}
                disabled={loading || !input.trim()}
                className="rounded-full bg-black px-4 py-2 text-sm text-white transition hover:bg-gray-800 disabled:opacity-50"
              >
                Send
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
