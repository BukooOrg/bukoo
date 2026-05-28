import { AlertCircle, AlertTriangle, Package } from 'lucide-react';
import React, { useState, useEffect, useMemo, useCallback } from 'react';

import { InventoryTable } from '@/components/inventory/inventory-table';
import { MetricCard } from '@/components/inventory/metric-card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/navigation/tabs';
import { inventoryApi } from '@/lib/apiClient';
import { cn } from '@/lib/utils';

const LOW_STOCK_RANGES = [
  { label: '< 5', min: 0, max: 4 },
  { label: '5–10', min: 5, max: 10 },
  { label: '10–20', min: 10, max: 20 },
  { label: '20–50', min: 20, max: 50 },
  { label: '50+', min: 50, max: null },
];

function OverviewTab() {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    async function loadMetrics() {
      setLoading(true);
      setError('');
      try {
        const res = await inventoryApi.getInventoryMetrics();
        setMetrics(res.data);
      } catch {
        setError('Failed to load inventory metrics');
      } finally {
        setLoading(false);
      }
    }
    loadMetrics();
  }, []);

  const handleRetry = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await inventoryApi.getInventoryMetrics();
      setMetrics(res.data);
    } catch {
      setError('Failed to load inventory metrics');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className='grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3'>
        {[...Array(3)].map((_, i) => (
          <div key={i} className='rounded-xl border p-5 animate-pulse bg-primary/5 h-24' />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className='flex flex-col items-center justify-center gap-4 py-12'>
        <AlertCircle className='w-8 h-8 text-destructive' />
        <p className='text-sm font-bold text-destructive'>{error}</p>
        <button
          onClick={handleRetry}
          className='px-4 py-2 text-sm font-bold border rounded-lg border-primary/10 text-primary hover:bg-primary/5 transition-colors'>
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className='grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3'>
      <MetricCard
        icon={Package}
        label='Total SKUs'
        value={metrics?.totalSkuCount ?? 0}
        accent='default'
      />
      <MetricCard
        icon={AlertCircle}
        label='Out of Stock'
        value={metrics?.outOfStockCount ?? 0}
        accent='red'
      />
      <MetricCard
        icon={AlertTriangle}
        label='Low Stock'
        value={metrics?.lowStockCount ?? 0}
        accent='amber'
      />
    </div>
  );
}

export default function InventoryPage() {
  const [activeTab, setActiveTab] = useState('overview');

  const lowStockRangeSelector = useMemo(
    () => ({ default: 0, options: LOW_STOCK_RANGES }),
    []
  );

  const fetchLowStock = useCallback(
    (params) => inventoryApi.findLowStockItems(params),
    []
  );

  const fetchOutOfStock = useCallback(
    (params) => inventoryApi.findOutOfStockItems(params),
    []
  );

  return (
    <div className='py-16 px-sides'>
      <div className='mx-auto max-w-7xl space-y-8'>
        {/* Page Header */}
        <div className='pt-8 text-center'>
          <h1 className='mb-2 font-serif text-4xl font-black tracking-tighter text-primary'>
            Inventory
          </h1>
          <p className='text-sm italic font-bold text-primary/40'>
            Monitor stock levels and inventory health
          </p>
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className='w-full'>
          <TabsList
            className={cn(
              'w-full max-w-md mx-auto h-auto p-1 rounded-xl bg-primary/5',
              'flex gap-1'
            )}
            role='tablist'
            aria-label='Inventory sections'>
            <TabsTrigger
              value='overview'
              role='tab'
              aria-selected={activeTab === 'overview'}
              className={cn(
                'flex-1 rounded-lg py-2.5 text-xs font-bold uppercase tracking-widest transition-all',
                'data-[state=active]:bg-white data-[state=active]:shadow-sm data-[state=active]:text-primary',
                'data-[state=inactive]:text-primary/40 data-[state=inactive]:hover:text-primary/60'
              )}>
              Overview
            </TabsTrigger>
            <TabsTrigger
              value='low-stock'
              role='tab'
              aria-selected={activeTab === 'low-stock'}
              className={cn(
                'flex-1 rounded-lg py-2.5 text-xs font-bold uppercase tracking-widest transition-all',
                'data-[state=active]:bg-white data-[state=active]:shadow-sm data-[state=active]:text-primary',
                'data-[state=inactive]:text-primary/40 data-[state=inactive]:hover:text-primary/60'
              )}>
              Low Stock
            </TabsTrigger>
            <TabsTrigger
              value='out-of-stock'
              role='tab'
              aria-selected={activeTab === 'out-of-stock'}
              className={cn(
                'flex-1 rounded-lg py-2.5 text-xs font-bold uppercase tracking-widest transition-all',
                'data-[state=active]:bg-white data-[state=active]:shadow-sm data-[state=active]:text-primary',
                'data-[state=inactive]:text-primary/40 data-[state=inactive]:hover:text-primary/60'
              )}>
              Out of Stock
            </TabsTrigger>
          </TabsList>

          <TabsContent value='overview' role='tabpanel' className='mt-6 focus-visible:outline-none'>
            <OverviewTab />
          </TabsContent>

          <TabsContent
            value='low-stock'
            role='tabpanel'
            className='mt-6 focus-visible:outline-none'>
            <InventoryTable
              title='Low Stock Items'
              description='Books below the selected stock threshold'
              fetchItems={fetchLowStock}
              emptyMessage='All books are well-stocked'
              rangeSelector={lowStockRangeSelector}
            />
          </TabsContent>

          <TabsContent
            value='out-of-stock'
            role='tabpanel'
            className='mt-6 focus-visible:outline-none'>
            <InventoryTable
              title='Out of Stock'
              description='Books with zero inventory'
              fetchItems={fetchOutOfStock}
              emptyMessage='All books in stock'
            />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
