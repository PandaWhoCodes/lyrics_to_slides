import { motion } from 'framer-motion';
import { cn } from '../../lib/utils';

export function Card({ children, className = '', hover = true, ...props }) {
  return (
    <motion.div
      className={cn(
        'bg-white rounded-xl border-2 border-gray-200 p-6 transition-all duration-200',
        hover && 'cursor-pointer hover:border-blue-400 hover:shadow-lg',
        className
      )}
      whileHover={hover ? { y: -4, transition: { duration: 0.2 } } : {}}
      {...props}
    >
      {children}
    </motion.div>
  );
}

export function CardHeader({ children, className = '' }) {
  return (
    <div className={cn('mb-3', className)}>
      {children}
    </div>
  );
}

export function CardTitle({ children, className = '' }) {
  return (
    <h3 className={cn('text-lg font-semibold text-gray-900', className)}>
      {children}
    </h3>
  );
}

export function CardContent({ children, className = '' }) {
  return (
    <div className={cn('text-sm text-gray-600', className)}>
      {children}
    </div>
  );
}
