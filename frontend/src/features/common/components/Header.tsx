import React from 'react';
import { cn } from '../utils/helpers';

interface HeaderProps extends React.HTMLAttributes<HTMLHeadElement> {
  children: React.ReactNode;
}

const Header = React.forwardRef<HTMLHeadElement, HeaderProps>(
  ({ className, children, ...props }, ref) => {
    return (
      <header
        ref={ref}
        className={cn('bg-white shadow-sm border-b border-gray-200', className)}
        {...props}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">{children}</div>
      </header>
    );
  }
);

Header.displayName = 'Header';

export default Header;
