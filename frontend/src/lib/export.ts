import { Message } from '@/types';

export async function exportMessageAsPDF(message: Message) {
  // Dynamic import to avoid SSR issues
  const { jsPDF } = await import('jspdf');

  const doc = new jsPDF();
  const margin = 20;
  let y = margin;

  // Title
  doc.setFontSize(14);
  doc.setFont('helvetica', 'bold');
  doc.text('College Chatbot - Response Export', margin, y);
  y += 10;

  // Timestamp
  doc.setFontSize(8);
  doc.setFont('helvetica', 'normal');
  doc.text(`Exported: ${new Date().toLocaleString()}`, margin, y);
  y += 10;

  // Domain badge
  if (message.domain) {
    doc.setFontSize(9);
    doc.text(`Domain: ${message.domain}`, margin, y);
    y += 8;
  }

  // Answer content
  doc.setFontSize(10);
  doc.setFont('helvetica', 'normal');
  const lines = doc.splitTextToSize(message.content, 170);
  for (const line of lines) {
    if (y > 270) {
      doc.addPage();
      y = margin;
    }
    doc.text(line, margin, y);
    y += 5;
  }

  // SQL
  if (message.sql) {
    y += 5;
    doc.setFont('courier', 'normal');
    doc.setFontSize(8);
    doc.text('SQL Query:', margin, y);
    y += 5;
    const sqlLines = doc.splitTextToSize(message.sql, 170);
    for (const line of sqlLines) {
      if (y > 270) {
        doc.addPage();
        y = margin;
      }
      doc.text(line, margin, y);
      y += 4;
    }
  }

  // Raw data as table
  if (message.rawData && message.rawData.length > 0) {
    y += 8;
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(9);
    doc.text('Data:', margin, y);
    y += 5;
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(7);

    const keys = Object.keys(message.rawData[0]);
    const header = keys.join(' | ');
    doc.text(header, margin, y);
    y += 4;

    for (const row of message.rawData) {
      if (y > 270) {
        doc.addPage();
        y = margin;
      }
      const rowText = keys.map((k) => String(row[k] ?? '')).join(' | ');
      doc.text(rowText, margin, y);
      y += 4;
    }
  }

  doc.save(`chatbot-response-${Date.now()}.pdf`);
}

export function exportMessageAsCSV(message: Message) {
  if (!message.rawData || message.rawData.length === 0) return;

  const keys = Object.keys(message.rawData[0]);
  const header = keys.join(',');
  const rows = message.rawData.map((row) =>
    keys.map((k) => {
      const val = String(row[k] ?? '');
      // Escape commas and quotes
      if (val.includes(',') || val.includes('"') || val.includes('\n')) {
        return `"${val.replace(/"/g, '""')}"`;
      }
      return val;
    }).join(',')
  );

  const csv = [header, ...rows].join('\n');
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `chatbot-data-${Date.now()}.csv`;
  link.click();
  URL.revokeObjectURL(url);
}

export async function exportMessageAsXLSX(message: Message) {
  if (!message.rawData || message.rawData.length === 0) return;

  const XLSX = await import('xlsx');
  const worksheet = XLSX.utils.json_to_sheet(message.rawData);
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, 'Data');

  // Auto-size columns based on content
  const keys = Object.keys(message.rawData[0]);
  worksheet['!cols'] = keys.map((key) => {
    const maxLen = Math.max(
      key.length,
      ...message.rawData!.map((row) => String(row[key] ?? '').length)
    );
    return { wch: Math.min(maxLen + 2, 50) };
  });

  XLSX.writeFile(workbook, `chatbot-data-${Date.now()}.xlsx`);
}

export async function exportConversationAsPDF(messages: Message[], title: string) {
  const { jsPDF } = await import('jspdf');

  const doc = new jsPDF();
  const margin = 20;
  let y = margin;

  doc.setFontSize(14);
  doc.setFont('helvetica', 'bold');
  doc.text(title || 'Conversation Export', margin, y);
  y += 8;

  doc.setFontSize(8);
  doc.setFont('helvetica', 'normal');
  doc.text(`Exported: ${new Date().toLocaleString()}`, margin, y);
  y += 10;

  for (const msg of messages) {
    if (y > 250) {
      doc.addPage();
      y = margin;
    }

    doc.setFontSize(9);
    doc.setFont('helvetica', 'bold');
    doc.text(msg.role === 'user' ? 'You:' : 'Assistant:', margin, y);
    y += 5;

    doc.setFont('helvetica', 'normal');
    doc.setFontSize(9);
    const lines = doc.splitTextToSize(msg.content, 170);
    for (const line of lines) {
      if (y > 270) {
        doc.addPage();
        y = margin;
      }
      doc.text(line, margin, y);
      y += 4.5;
    }
    y += 5;
  }

  doc.save(`conversation-${Date.now()}.pdf`);
}
