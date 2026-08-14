'use client';

const EXAMPLE_QUESTIONS = [
  'Students with attendance below 70%',
  'Students with attendance below 60%',
  'Top 15 students by attendance percentage',
  'Bottom 15 students by attendance percentage',
  'Students continuously absent in current week',
  'Last 7 days attendance percentage of all students',
  'Attendance below 70% in IOI Delhi center',
  'Show attendance percentage batch wise',
];

interface ExampleChipsProps {
  onSelect: (question: string) => void;
}

export function ExampleChips({ onSelect }: ExampleChipsProps) {
  return (
    <div className="flex flex-wrap justify-center gap-2 mt-4">
      {EXAMPLE_QUESTIONS.map((q) => (
        <button
          key={q}
          onClick={() => onSelect(q)}
          className="px-3 py-2 text-sm rounded-xl border border-border-light dark:border-border-dark hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors text-gray-600 dark:text-gray-300"
        >
          {q}
        </button>
      ))}
    </div>
  );
}
