'use client';

export function TypingIndicator() {
  return (
    <div className="flex justify-start animate-fade-in-up">
      <div className="bg-assistant-bubble dark:bg-assistant-bubble-dark rounded-2xl px-4 py-3">
        <div className="flex items-center gap-1">
          <span className="typing-dot w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full" />
          <span className="typing-dot w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full" />
          <span className="typing-dot w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full" />
        </div>
      </div>
    </div>
  );
}
