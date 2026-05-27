import { EyeOff, Loader2, Trash2 } from 'lucide-react';
import React, { useState, useEffect } from 'react';
import { toast } from 'sonner';

import { StarRating } from '@/components/reviews';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/data-display/table';
import { ConfirmDialog } from '@/components/ui/feedback/confirm-dialog';
import { Spinner } from '@/components/ui/feedback/spinner';
import { Button } from '@/components/ui/forms/button';
import { reviewApi } from '@/lib/apiClient';

function formatDate(date) {
  return new Date(date).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

export default function AdminReviewsPage() {
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [searchQuery, setSearchQuery] = useState('');
  const [hiddenFilter, setHiddenFilter] = useState('');
  const [actingId, setActingId] = useState(null);

  // Delete confirmation
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(null);

  useEffect(() => {
    async function loadReviews() {
      setLoading(true);
      try {
        const params = { page, pageSize: 20 };
        if (searchQuery) params.search = searchQuery;
        if (hiddenFilter === 'hidden') params.isHidden = true;
        if (hiddenFilter === 'visible') params.isHidden = false;

        const response = await reviewApi.findReviewsByAdmin(params);
        const data = response.data;
        setReviews(data.items || []);
        setTotalPages(data.meta?.totalPages || 1);
      } catch {
        setReviews([]);
      } finally {
        setLoading(false);
      }
    }
    loadReviews();
  }, [page, searchQuery, hiddenFilter]);

  const handleHideRestore = async (reviewId, isHidden) => {
    setActingId(reviewId);
    try {
      await reviewApi.hideOrRestoreReview({
        reviewId,
        hideOrRestoreReviewRequest: { isHidden: isHidden },
      });
      toast.success(isHidden ? 'Review hidden' : 'Review restored');
      // Refresh
      const params = { page, pageSize: 20 };
      if (searchQuery) params.search = searchQuery;
      if (hiddenFilter === 'hidden') params.isHidden = true;
      if (hiddenFilter === 'visible') params.isHidden = false;
      const response = await reviewApi.findReviewsByAdmin(params);
      setReviews(response.data.items || []);
    } catch (error) {
      toast.error(`Failed: ${error.message || 'Unknown error'}`);
    } finally {
      setActingId(null);
    }
  };

  const handleDeleteClick = (review) => {
    setDeleteTarget(review);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!deleteTarget) return;
    setActingId(deleteTarget.id);
    try {
      await reviewApi.softDeleteReview({ reviewId: deleteTarget.id });
      toast.success('Review deleted');
      setDeleteDialogOpen(false);
      setDeleteTarget(null);
      // Refresh
      const params = { page, pageSize: 20 };
      if (searchQuery) params.search = searchQuery;
      if (hiddenFilter === 'hidden') params.isHidden = true;
      if (hiddenFilter === 'visible') params.isHidden = false;
      const response = await reviewApi.findReviewsByAdmin(params);
      setReviews(response.data.items || []);
    } catch (error) {
      toast.error(`Failed: ${error.message || 'Unknown error'}`);
    } finally {
      setActingId(null);
    }
  };

  if (loading) {
    return (
      <div className='flex items-center justify-center min-h-[60vh]'>
        <Spinner size='lg' />
      </div>
    );
  }

  return (
    <div className='px-sides py-16'>
      <div className='max-w-7xl mx-auto'>
        {/* Header */}
        <div className='text-center pt-8'>
          <h1 className='text-4xl font-serif font-black mb-2 text-primary tracking-tighter'>
            Reviews
          </h1>
          <p className='text-primary/40 font-bold italic text-sm'>
            Moderate customer reviews and ratings
          </p>
        </div>

        {/* Filters */}
        <div className='flex flex-wrap items-center justify-end gap-3 mt-6'>
          <input
            type='text'
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              setPage(1);
            }}
            placeholder='Search reviews...'
            className='h-10 px-3 border rounded-lg text-sm w-64 border-primary/10 focus:border-primary/30 focus:outline-none focus:ring-2 focus:ring-primary/10 transition-all'
          />
          <select
            value={hiddenFilter}
            onChange={(e) => {
              setHiddenFilter(e.target.value);
              setPage(1);
            }}
            className='h-10 px-3 border rounded-lg text-sm border-primary/10 focus:border-primary/30 focus:outline-none focus:ring-2 focus:ring-primary/10 transition-all'>
            <option value=''>All Reviews</option>
            <option value='visible'>Visible Only</option>
            <option value='hidden'>Hidden Only</option>
          </select>
        </div>

        {/* Table */}
        <div className='overflow-hidden bg-white border rounded-2xl border-primary/5 mt-6'>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className='w-16'>Rating</TableHead>
                <TableHead>Book</TableHead>
                <TableHead className='w-48'>Comment</TableHead>
                <TableHead className='w-28'>Date</TableHead>
                <TableHead className='w-24'>Status</TableHead>
                <TableHead className='w-24 text-right'>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {reviews.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className='py-16 text-center'>
                    <p className='font-serif text-lg italic text-primary/30'>
                      No reviews{searchQuery ? ` matching "${searchQuery}"` : ''}
                      {hiddenFilter === 'hidden' ? ' (hidden)' : ''}
                      {hiddenFilter === 'visible' ? ' (visible)' : ''} found
                    </p>
                  </TableCell>
                </TableRow>
              ) : (
                reviews.map((review) => {
                  const isActing = actingId === review.id;
                  return (
                    <TableRow key={review.id}>
                      <TableCell>
                        <StarRating value={review.rating} size='sm' />
                      </TableCell>
                      <TableCell>
                        <div>
                          <a
                            href={`/admin/books/${review.book?.id}`}
                            className='font-medium transition-colors text-primary hover:text-primary/70'>
                            {review.book?.title || 'Unknown'}
                          </a>
                        </div>
                      </TableCell>
                      <TableCell className='max-w-48'>
                        <p className='text-sm truncate text-primary/60'>{review.comment || '—'}</p>
                      </TableCell>
                      <TableCell className='text-sm text-primary/40'>
                        {formatDate(review.createdAt)}
                      </TableCell>
                      <TableCell>
                        {review.isHidden ? (
                          <span className='flex items-center gap-1 px-2 py-1 text-xs rounded-full bg-red-50 text-red-600 w-fit'>
                            <EyeOff className='w-3 h-3' />
                            Hidden
                          </span>
                        ) : (
                          <span className='px-2 py-1 text-xs rounded-full bg-green-50 text-green-600 w-fit'>
                            Visible
                          </span>
                        )}
                      </TableCell>
                      <TableCell>
                        <div className='flex items-center justify-end gap-1'>
                          <Button
                            onClick={() => handleHideRestore(review.id, !review.isHidden)}
                            disabled={isActing}
                            variant='ghost'
                            size='icon'
                            className='w-8 h-8 rounded-lg text-primary/40 hover:text-primary hover:bg-primary/5'
                            aria-label={review.isHidden ? 'Restore review' : 'Hide review'}>
                            {isActing ? (
                              <Loader2 className='w-4 h-4 animate-spin' />
                            ) : (
                              <EyeOff className='w-4 h-4' />
                            )}
                          </Button>
                          <Button
                            onClick={() => handleDeleteClick(review)}
                            disabled={isActing}
                            variant='ghost'
                            size='icon'
                            className='w-8 h-8 rounded-lg text-red-400 hover:text-red-600 hover:bg-red-50'
                            aria-label='Delete review'>
                            {isActing ? (
                              <Loader2 className='w-4 h-4 animate-spin' />
                            ) : (
                              <Trash2 className='w-4 h-4' />
                            )}
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className='flex items-center justify-center gap-3 mt-8'>
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

      {/* Delete confirmation */}
      <ConfirmDialog
        open={deleteDialogOpen}
        onOpenChange={setDeleteDialogOpen}
        title='Delete Review'
        description={`Are you sure you want to delete the review for "${deleteTarget?.book?.title}"? This action cannot be undone.`}
        confirmText='Delete'
        variant='destructive'
        onConfirm={handleDeleteConfirm}
      />
    </div>
  );
}
