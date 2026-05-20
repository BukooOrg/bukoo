import { Plus, AlertCircle, Loader2, FolderTree, Eye, Trash2 } from 'lucide-react';
import React, { useState, useCallback, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { toast } from 'sonner';

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/data-display/table';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/feedback/alert-dialog';
import { Button } from '@/components/ui/forms/button';
import { categoryApi, collectionApi } from '@/lib/apiClient';

export default function CategoriesPage() {
  const [categories, setCategories] = useState([]);
  const [collections, setCollections] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [collectionFilter, setCollectionFilter] = useState('all');
  const [deleteDialog, setDeleteDialog] = useState(false);
  const [deletingId, setDeletingId] = useState(null);
  const [targetCategory, setTargetCategory] = useState(null);

  const fetchData = useCallback(async (colId) => {
    setLoading(true);
    setError('');
    try {
      const [catRes, colRes] = await Promise.all([
        categoryApi.findCategories({
          collectionId: colId !== 'all' ? colId : undefined,
        }),
        collectionApi.findCollections(),
      ]);
      setCategories(catRes.data || []);
      setCollections(colRes.data?.items || []);
    } catch (err) {
      console.error('Failed to load categories:', err);
      setError('Failed to load categories');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData(collectionFilter);
  }, [collectionFilter, fetchData]);

  const handleCollectionChange = (val) => {
    setCollectionFilter(val);
  };

  const handleDeleteClick = (cat) => {
    setTargetCategory(cat);
    setDeleteDialog(true);
  };

  const handleDeleteConfirm = async () => {
    if (!targetCategory) return;
    setDeletingId(targetCategory.id);
    try {
      await categoryApi.softDeleteCategory({ categoryId: targetCategory.id });
      toast.success(`"${targetCategory.name}" deleted`);
      setDeleteDialog(false);
      setTargetCategory(null);
      fetchData(collectionFilter);
    } catch (err) {
      const msg = err?.response?.data?.error?.message || err?.message || 'Delete failed';
      toast.error(msg);
    } finally {
      setDeletingId(null);
    }
  };

  const getCollectionName = (collectionId) => {
    const col = collections.find((c) => c.id === collectionId);
    return col?.name || '—';
  };

  return (
    <div className='space-y-8'>
      {/* Header */}
      <div className='text-center pt-8'>
        <h1 className='text-4xl font-serif font-black mb-2 text-primary tracking-tighter'>
          Categories
        </h1>
        <p className='text-primary/40 font-bold italic text-sm'>
          {categories.length} categories total
        </p>
      </div>

      {/* Top bar — collection filter + create */}
      <div className='flex flex-wrap items-center justify-end gap-3'>
        <div className='flex p-1 bg-primary/5 rounded-xl'>
          <button
            onClick={() => handleCollectionChange('all')}
            className={`px-4 py-2 rounded-lg text-xs font-bold uppercase tracking-widest transition-all ${
              collectionFilter === 'all'
                ? 'bg-white shadow-sm text-primary'
                : 'text-primary/40 hover:text-primary/60'
            }`}>
            All Collections
          </button>
          {collections.map((col) => (
            <button
              key={col.id}
              onClick={() => handleCollectionChange(col.id)}
              className={`px-4 py-2 rounded-lg text-xs font-bold uppercase tracking-widest transition-all ${
                collectionFilter === col.id
                  ? 'bg-white shadow-sm text-primary'
                  : 'text-primary/40 hover:text-primary/60'
              }`}>
              {col.name}
            </button>
          ))}
        </div>
        <Link to='/admin/categories/new'>
          <Button className='gap-2 font-sans font-bold uppercase tracking-[0.1em] bg-primary text-secondary rounded-2xl hover:scale-[1.02] active:scale-[0.98] transition-all'>
            <Plus className='w-4 h-4' />
            New Category
          </Button>
        </Link>
      </div>

      {/* Error */}
      {error && (
        <div className='flex items-start gap-3 p-4 border bg-destructive/5 border-destructive/10 rounded-2xl animate-in slide-in-from-top-2'>
          <AlertCircle className='w-5 h-5 text-destructive shrink-0' />
          <p className='text-xs font-bold leading-relaxed text-destructive'>{error}</p>
        </div>
      )}

      {/* Table */}
      {loading ? (
        <div className='animate-pulse space-y-3'>
          {[...Array(6)].map((_, i) => (
            <div key={i} className='h-14 bg-primary/5 rounded-xl' />
          ))}
        </div>
      ) : (
        <>
          <div className='overflow-hidden bg-white border rounded-2xl border-primary/5'>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>URL Slug</TableHead>
                  <TableHead>Collection</TableHead>
                  <TableHead className='w-28 text-right'>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {categories.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={4} className='py-16 text-center'>
                      <FolderTree className='w-10 h-10 mx-auto mb-3 text-primary/20' />
                      <p className='font-serif text-lg italic text-primary/30'>
                        No categories found
                      </p>
                    </TableCell>
                  </TableRow>
                ) : (
                  categories.map((cat) => (
                    <TableRow key={cat.id}>
                      <TableCell>
                        <Link
                          to={`/admin/categories/${cat.id}`}
                          className='font-sans font-bold transition-colors text-primary hover:text-primary/70'>
                          {cat.name}
                        </Link>
                      </TableCell>
                      <TableCell className='text-primary/60 text-sm font-mono'>
                        {cat.urlSlug}
                      </TableCell>
                      <TableCell className='text-primary/60 text-sm'>
                        {getCollectionName(cat.collectionId)}
                      </TableCell>
                      <TableCell className='text-right'>
                        <div className='flex items-center justify-end gap-1'>
                          <Link to={`/admin/categories/${cat.id}`}>
                            <Button
                              variant='ghost'
                              size='icon'
                              className='w-8 h-8 rounded-lg text-primary/40 hover:text-primary hover:bg-primary/5'>
                              <Eye className='w-4 h-4' />
                            </Button>
                          </Link>
                          <Button
                            variant='ghost'
                            size='icon'
                            onClick={() => handleDeleteClick(cat)}
                            disabled={deletingId === cat.id}
                            className='w-8 h-8 rounded-lg text-primary/40 hover:text-destructive hover:bg-destructive/5'>
                            {deletingId === cat.id ? (
                              <Loader2 className='w-4 h-4 animate-spin' />
                            ) : (
                              <Trash2 className='w-4 h-4' />
                            )}
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </>
      )}

      {/* Delete Dialog */}
      <AlertDialog open={deleteDialog} onOpenChange={setDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className='text-destructive'>Delete Category?</AlertDialogTitle>
            <AlertDialogDescription>
              This will delete &quot;{targetCategory?.name}&quot;. Associated books will lose their
              category assignment. This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteConfirm}
              disabled={deletingId !== null}
              className='bg-destructive text-white'>
              {deletingId !== null ? (
                <Loader2 className='w-4 h-4 animate-spin' />
              ) : (
                'Delete Category'
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
