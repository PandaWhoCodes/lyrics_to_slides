import { cn } from '../../lib/utils';

export function Input({ className = '', ...props }) {
  return (
    <input
      className={cn(
        'w-full px-4 py-3 text-base border-2 border-gray-300 rounded-xl outline-none transition-all duration-200',
        'focus:border-blue-500 focus:ring-4 focus:ring-blue-100',
        'placeholder:text-gray-400',
        'disabled:opacity-50 disabled:cursor-not-allowed',
        className
      )}
      {...props}
    />
  );
}

export function Textarea({ className = '', ...props }) {
  return (
    <textarea
      className={cn(
        'w-full px-4 py-3 text-base border-2 border-gray-300 rounded-xl outline-none transition-all duration-200 resize-vertical',
        'focus:border-blue-500 focus:ring-4 focus:ring-blue-100',
        'placeholder:text-gray-400',
        'disabled:opacity-50 disabled:cursor-not-allowed',
        className
      )}
      {...props}
    />
  );
}
