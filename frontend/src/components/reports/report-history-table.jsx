import { ReportJobStatus, ReportType } from '@bukoo/api-client';
import { Download, Link2Off } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { toast } from 'sonner';

import { ReportStatusBadge } from '@/components/reports/report-status-badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/data-display/table';
import { Spinner } from '@/components/ui/feedback/spinner';
import { Button } from '@/components/ui/forms/button';
import { getToken } from '@/lib/apiClient';
import { reportApi } from '@/lib/apiClient';

const PAGE_SIZE = 10;

const typeLabels = {
  [ReportType.SALES_SUMMARY]: 'Sales Summary',
  [ReportType.TOP_BOOKS]: 'Top Books',
  [ReportType.TOP_AUTHORS]: 'Top Authors',
  [ReportType.MONTHLY_VOLUME]: 'Monthly Volume',
};

const formatLabels = {
  pdf: 'PDF',
  csv: 'CSV',
};

function formatDate(dateStr) {
  if (!dateStr) return '—';
  return new Date(dateStr).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

function formatDateRange(dateFrom, dateTo) {
  const from = formatDate(dateFrom);
  const to = formatDate(dateTo);
  return `${from} → ${to}`;
}

async function handleDownload(job) {
  try {
    const token = getToken();
    const response = await fetch(`/api/app/v1/reports/jobs/${job.jobId}/download`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Download failed (${response.status}): ${errorText || response.statusText}`);
    }

    const blob = await response.blob();

    if (blob.size === 0) {
      throw new Error('Downloaded file is empty');
    }

    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;

    const dateFrom = job.dateFrom instanceof Date ? job.dateFrom : new Date(job.dateFrom);
    const dateTo = job.dateTo instanceof Date ? job.dateTo : new Date(job.dateTo);
    const typeStr = String(job.type || 'report')
      .replace('sales_summary', 'sales')
      .replace('top_books', 'top-books')
      .replace('top_authors', 'top-authors')
      .replace('monthly_volume', 'monthly-volume');
    const formatStr = String(job.format || 'pdf');

    a.download = `report_${typeStr}_${dateFrom.toISOString().split('T')[0]}_${dateTo.toISOString().split('T')[0]}.${formatStr}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);

    // Delay revoke to ensure browser has started the download
    setTimeout(() => URL.revokeObjectURL(url), 100);

    toast.success('Report downloaded');
  } catch (err) {
    toast.error(`Download failed: ${err.message}`);
  }
}

export function ReportHistoryTable() {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [statusFilter, setStatusFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const pollRef = useRef(null);

  const loadJobs = async () => {
    try {
      const response = await reportApi.findReportJobs({
        page,
        pageSize: PAGE_SIZE,
        ...(statusFilter && { status: statusFilter }),
        ...(typeFilter && { type: typeFilter }),
      });
      const data = response.data;
      setJobs(data.items || []);
      setTotalPages(data.meta?.totalPages || 1);
    } catch {
      setJobs([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setLoading(true);
    loadJobs();
  }, [page, statusFilter, typeFilter]);

  // Auto-refresh while any job is pending/processing
  useEffect(() => {
    const hasActiveJobs = jobs.some(
      (j) => j.status === ReportJobStatus.PENDING || j.status === ReportJobStatus.PROCESSING
    );

    if (hasActiveJobs) {
      pollRef.current = setInterval(() => {
        loadJobs();
      }, 5000);
    }

    return () => {
      if (pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }
    };
  }, [jobs]);

  if (loading) {
    return (
      <div className='flex items-center justify-center py-12'>
        <Spinner size='lg' />
      </div>
    );
  }

  if (jobs.length === 0) {
    return (
      <div className='flex flex-col items-center justify-center gap-4 py-16'>
        <Link2Off className='size-10 text-primary/20' />
        <p className='font-serif text-lg italic text-primary/30'>No report jobs yet</p>
        <p className='text-sm text-primary/40'>Generate your first report from the Generate tab</p>
      </div>
    );
  }

  return (
    <div className='space-y-4'>
      {/* Filters */}
      <div className='flex flex-wrap items-center gap-3'>
        <select
          value={statusFilter}
          onChange={(e) => {
            setStatusFilter(e.target.value);
            setPage(1);
          }}
          className='h-10 rounded-2xl border border-primary/10 px-3 pr-8 text-sm appearance-none bg-background transition-all focus:border-primary/30 focus:outline-none focus:ring-2 focus:ring-primary/10'>
          <option value=''>All Status</option>
          <option value={ReportJobStatus.PENDING}>Pending</option>
          <option value={ReportJobStatus.PROCESSING}>Processing</option>
          <option value={ReportJobStatus.COMPLETED}>Completed</option>
          <option value={ReportJobStatus.FAILED}>Failed</option>
        </select>

        <select
          value={typeFilter}
          onChange={(e) => {
            setTypeFilter(e.target.value);
            setPage(1);
          }}
          className='h-10 rounded-2xl border border-primary/10 px-3 pr-8 text-sm appearance-none bg-background transition-all focus:border-primary/30 focus:outline-none focus:ring-2 focus:ring-primary/10'>
          <option value=''>All Types</option>
          <option value={ReportType.SALES_SUMMARY}>Sales Summary</option>
          <option value={ReportType.TOP_BOOKS}>Top Books</option>
          <option value={ReportType.TOP_AUTHORS}>Top Authors</option>
          <option value={ReportType.MONTHLY_VOLUME}>Monthly Volume</option>
        </select>
      </div>

      {/* Table */}
      <div className='overflow-hidden rounded-2xl border border-primary/5 bg-white'>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Type</TableHead>
              <TableHead>Date Range</TableHead>
              <TableHead className='w-20'>Format</TableHead>
              <TableHead className='w-32'>Status</TableHead>
              <TableHead className='w-32'>Created</TableHead>
              <TableHead className='w-24 text-right'>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {jobs.map((job) => (
              <TableRow key={job.jobId}>
                <TableCell className='font-medium text-primary'>
                  {typeLabels[job.type] || job.type}
                </TableCell>
                <TableCell className='text-sm text-primary/50'>
                  {formatDateRange(job.dateFrom, job.dateTo)}
                </TableCell>
                <TableCell>
                  <span className='rounded bg-primary/5 px-2 py-0.5 text-xs font-medium text-primary/70'>
                    {formatLabels[job.format] || job.format}
                  </span>
                </TableCell>
                <TableCell>
                  <ReportStatusBadge status={job.status} />
                </TableCell>
                <TableCell className='text-sm text-primary/40'>
                  {formatDate(job.createdAt)}
                </TableCell>
                <TableCell className='text-right'>
                  {job.status === ReportJobStatus.COMPLETED ? (
                    <Button
                      onClick={() => handleDownload(job)}
                      variant='ghost'
                      size='icon-sm'
                      className='h-8 w-8 rounded-2xl text-primary/40 hover:text-primary hover:bg-primary/5'>
                      <Download className='size-4' />
                    </Button>
                  ) : (
                    <span className='text-xs text-primary/20'>—</span>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className='flex items-center justify-center gap-3 pt-2'>
          <Button
            variant='outline'
            disabled={page <= 1}
            onClick={() => setPage((p) => p - 1)}
            className='h-10'>
            Previous
          </Button>
          <span className='text-sm text-primary/40'>
            Page {page} of {totalPages}
          </span>
          <Button
            variant='outline'
            disabled={page >= totalPages}
            onClick={() => setPage((p) => p + 1)}
            className='h-10'>
            Next
          </Button>
        </div>
      )}
    </div>
  );
}
