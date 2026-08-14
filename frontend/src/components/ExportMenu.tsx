'use client';

import { useState, useRef, useEffect } from 'react';
import { Download } from 'lucide-react';
import { Message } from '@/types';
import { exportMessageAsPDF, exportMessageAsCSV, exportMessageAsXLSX } from '@/lib/export';

interface ExportMenuProps {
  message: Message;
}

export function ExportMenu({ message }: ExportMenuProps) {
  const [open, setOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className="relative" ref={menuRef}>
      <button
        onClick={() => setOpen(!open)}
        className="p-1 rounded text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
        aria-label="Export message"
        aria-expanded={open}
      >
        <Download className="w-3.5 h-3.5" />
      </button>

      {open && (
        <div className="absolute bottom-full right-0 mb-1 bg-white dark:bg-gray-800 border border-border-light dark:border-border-dark rounded-lg shadow-lg py-1 min-w-[140px] z-10">
          <button
            onClick={() => { exportMessageAsPDF(message); setOpen(false); }}
            className="w-full text-left px-3 py-1.5 text-xs hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          >
            Export as PDF
          </button>
          {message.rawData && (
            <>
              <button
                onClick={() => { exportMessageAsCSV(message); setOpen(false); }}
                className="w-full text-left px-3 py-1.5 text-xs hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              >
                Export as CSV
              </button>
              <button
                onClick={() => { exportMessageAsXLSX(message); setOpen(false); }}
                className="w-full text-left px-3 py-1.5 text-xs hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              >
                Export as XLSX
              </button>
            </>
          )}
        </div>
      )}
    </div>
  );
}
