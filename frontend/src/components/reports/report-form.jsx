import { ReportFormat, ReportType } from '@bukoo/api-client';
import { zodResolver } from '@hookform/resolvers/zod';
import { CalendarDays } from 'lucide-react';
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { toast } from 'sonner';
import { z } from 'zod';

import { reportApi } from '@/lib/apiClient';
import { cn } from '@/lib/utils';

const reportSchema = z
  .object({
    type: z.nativeEnum(ReportType),
    dateFrom: z.string().min(1, 'Start date is required'),
    dateTo: z.string().min(1, 'End date is required'),
    format: z.nativeEnum(ReportFormat),
    limit: z.coerce.number().int().min(1).max(1000).optional().nullable(),
  })
  .superRefine((data, ctx) => {
    if (data.dateFrom && data.dateTo && data.dateFrom > data.dateTo) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Start date must be before or equal to end date',
        path: ['dateFrom'],
      });
    }
  });

const REPORT_TYPE_OPTIONS = [
  {
    value: ReportType.SALES_SUMMARY,
    label: 'Sales Summary',
    description: 'Revenue and order totals',
  },
  { value: ReportType.TOP_BOOKS, label: 'Top Books', description: 'Best-selling titles by period' },
  {
    value: ReportType.TOP_AUTHORS,
    label: 'Top Authors',
    description: 'Authors ranked by sales volume',
  },
  {
    value: ReportType.MONTHLY_VOLUME,
    label: 'Monthly Volume',
    description: 'Monthly order and revenue trends',
  },
];

const showsLimitField = (type) => type === ReportType.TOP_BOOKS || type === ReportType.TOP_AUTHORS;

export function ReportForm({ onSuccess }) {
  const [isSubmitting, setIsSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(reportSchema),
    defaultValues: {
      type: ReportType.SALES_SUMMARY,
      dateFrom: '',
      dateTo: '',
      format: ReportFormat.PDF,
      limit: null,
    },
  });

  const selectedType = watch('type');
  const selectedFormat = watch('format');

  const onSubmit = async (data) => {
    setIsSubmitting(true);
    try {
      await reportApi.createReportJob({
        createReportJobRequest: {
          type: data.type,
          dateFrom: new Date(data.dateFrom),
          dateTo: new Date(data.dateTo),
          format: data.format,
          limit: showsLimitField(data.type) ? data.limit : undefined,
        },
      });
      toast.success('Report queued for generation');
      onSuccess?.();
    } catch {
      toast.error('Failed to create report job');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className='space-y-8'>
      {/* Report Type */}
      <div>
        <label className='mb-3 block text-sm font-semibold text-primary/70'>Report Type</label>
        <div className='grid grid-cols-1 gap-3 sm:grid-cols-2'>
          {REPORT_TYPE_OPTIONS.map((option) => {
            const isSelected = selectedType === option.value;
            return (
              <button
                key={option.value}
                type='button'
                onClick={() => setValue('type', option.value, { shouldValidate: true })}
                className={cn(
                  'rounded-xl border-2 p-4 text-left transition-all',
                  isSelected
                    ? 'border-primary bg-primary/5 shadow-sm'
                    : 'border-primary/10 hover:border-primary/30 hover:bg-primary/[0.02]'
                )}>
                <div className='text-sm font-semibold text-primary'>{option.label}</div>
                <div className='mt-0.5 text-xs text-primary/40'>{option.description}</div>
              </button>
            );
          })}
        </div>
        {errors.type && <p className='mt-2 text-sm text-destructive'>{errors.type.message}</p>}
      </div>

      {/* Date Range */}
      <div className='grid grid-cols-1 gap-4 sm:grid-cols-2'>
        <div>
          <label htmlFor='dateFrom' className='mb-2 block text-sm font-semibold text-primary/70'>
            Start Date
          </label>
          <div className='relative'>
            <input
              id='dateFrom'
              type='date'
              {...register('dateFrom')}
              className={cn(
                'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
                errors.dateFrom && 'border-destructive'
              )}
            />
            <CalendarDays className='pointer-events-none absolute right-3 top-2.5 size-4 text-muted-foreground' />
          </div>
          {errors.dateFrom && (
            <p className='mt-1.5 text-sm text-destructive'>{errors.dateFrom.message}</p>
          )}
        </div>

        <div>
          <label htmlFor='dateTo' className='mb-2 block text-sm font-semibold text-primary/70'>
            End Date
          </label>
          <div className='relative'>
            <input
              id='dateTo'
              type='date'
              {...register('dateTo')}
              className={cn(
                'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
                errors.dateTo && 'border-destructive'
              )}
            />
            <CalendarDays className='pointer-events-none absolute right-3 top-2.5 size-4 text-muted-foreground' />
          </div>
          {errors.dateTo && (
            <p className='mt-1.5 text-sm text-destructive'>{errors.dateTo.message}</p>
          )}
        </div>
      </div>

      {/* Format Toggle */}
      <div>
        <label className='mb-3 block text-sm font-semibold text-primary/70'>Output Format</label>
        <div className='inline-flex rounded-lg border-2 border-primary/20 p-1'>
          {[
            { value: ReportFormat.PDF, label: 'PDF' },
            { value: ReportFormat.CSV, label: 'CSV' },
          ].map((option) => {
            const isSelected = selectedFormat === option.value;
            return (
              <button
                key={option.value}
                type='button'
                onClick={() => setValue('format', option.value, { shouldValidate: true })}
                className={cn(
                  'rounded-md px-5 py-2 text-sm font-semibold transition-all',
                  isSelected
                    ? 'border border-primary/30 bg-primary/10 text-primary shadow-sm'
                    : 'border border-transparent text-primary/50 hover:text-primary hover:bg-primary/5'
                )}>
                {option.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Limit (conditional) */}
      {showsLimitField(selectedType) && (
        <div className='max-w-xs'>
          <label htmlFor='limit' className='mb-2 block text-sm font-semibold text-primary/70'>
            Limit (max results)
          </label>
          <input
            id='limit'
            type='number'
            min={1}
            max={1000}
            placeholder='e.g. 50'
            {...register('limit')}
            className={cn(
              'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
              errors.limit && 'border-destructive'
            )}
          />
          {errors.limit && (
            <p className='mt-1.5 text-sm text-destructive'>{errors.limit.message}</p>
          )}
        </div>
      )}

      {/* Submit */}
      <div className='flex justify-end pt-4'>
        <button
          type='submit'
          disabled={isSubmitting}
          className={cn(
            'inline-flex h-11 items-center justify-center gap-2 rounded-lg border-2 border-primary bg-transparent px-8 text-base font-semibold text-primary shadow-sm transition-all hover:bg-primary hover:text-primary-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50'
          )}>
          {isSubmitting ? (
            <>
              <span className='size-4 animate-spin rounded-full border-2 border-primary border-t-transparent' />
              Queuing…
            </>
          ) : (
            'Generate Report'
          )}
        </button>
      </div>
    </form>
  );
}
