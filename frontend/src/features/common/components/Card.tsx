import React from 'react';
import { cn } from '../utils/helpers';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
}

const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, children, ...props }, ref) => {
    return (
      <div ref={ref} className={cn('bg-white rounded-lg shadow-md p-6', className)} {...props}>
        {children}
      </div>
    );
  }
);

Card.displayName = 'Card';

export default Card;
