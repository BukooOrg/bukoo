import { Circle } from 'lucide-react';
import React from 'react';

import { cn } from '@/lib/utils';

export function ActivityTimeline({ events, className, ...props }) {
  if (!events || events.length === 0) {
    return (
      <div className={cn('text-center py-8 text-muted-foreground', className)} {...props}>
        <p>No activity yet</p>
      </div>
    );
  }

  return (
    <div className={cn('relative space-y-4', className)} {...props}>
      {events.map((event, index) => (
        <TimelineItem
          key={event.id || index}
          icon={event.icon}
          title={event.title}
          description={event.description}
          timestamp={event.timestamp}
          isLast={index === events.length - 1}
        />
      ))}
    </div>
  );
}

function TimelineItem({ icon: Icon, title, description, timestamp, isLast }) {
  return (
    <div className='flex gap-4'>
      <div className='flex flex-col items-center'>
        <div className='w-8 h-8 rounded-full bg-muted flex items-center justify-center shrink-0'>
          {Icon ? (
            <Icon className='w-4 h-4 text-muted-foreground' />
          ) : (
            <Circle className='w-3 h-3 fill-muted-foreground' />
          )}
        </div>

        {!isLast && <div className='w-px flex-1 bg-border mt-2' />}
      </div>

      <div className='flex-1 min-w-0 pb-4'>
        <div className='flex items-start justify-between gap-2'>
          <div className='min-w-0'>
            <p className='text-sm font-medium text-foreground'>{title}</p>
            {description && <p className='text-sm text-muted-foreground mt-0.5'>{description}</p>}
          </div>

          {timestamp && (
            <time className='text-xs text-muted-foreground shrink-0 tabular-nums'>
              {formatTimestamp(timestamp)}
            </time>
          )}
        </div>
      </div>
    </div>
  );
}

function formatTimestamp(timestamp) {
  if (timestamp instanceof Date) {
    return timestamp.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }

  if (typeof timestamp === 'string') {
    const date = new Date(timestamp);
    if (!isNaN(date.getTime())) {
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    }
  }

  return String(timestamp);
}
