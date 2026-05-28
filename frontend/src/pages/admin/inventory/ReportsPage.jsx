import { useState } from 'react';

import { ReportForm, ReportHistoryTable } from '@/components/reports';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/navigation/tabs';
import { cn } from '@/lib/utils';

export default function ReportsPage() {
  const [activeTab, setActiveTab] = useState('generate');

  return (
    <div className='py-16 px-sides'>
      <div className='mx-auto max-w-7xl space-y-8'>
        {/* Page Header */}
        <div className='pt-8 text-center'>
          <h1 className='mb-2 font-serif text-4xl font-black tracking-tighter text-primary'>
            Reports & Analytics
          </h1>
          <p className='text-sm italic font-bold text-primary/40'>
            Generate reports and view job history
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
            aria-label='Reports sections'>
            <TabsTrigger
              value='generate'
              role='tab'
              aria-selected={activeTab === 'generate'}
              className={cn(
                'flex-1 rounded-lg py-2.5 text-xs font-bold uppercase tracking-widest transition-all',
                'data-[state=active]:bg-white data-[state=active]:shadow-sm data-[state=active]:text-primary',
                'data-[state=inactive]:text-primary/40 data-[state=inactive]:hover:text-primary/60'
              )}>
              Generate Report
            </TabsTrigger>
            <TabsTrigger
              value='history'
              role='tab'
              aria-selected={activeTab === 'history'}
              className={cn(
                'flex-1 rounded-lg py-2.5 text-xs font-bold uppercase tracking-widest transition-all',
                'data-[state=active]:bg-white data-[state=active]:shadow-sm data-[state=active]:text-primary',
                'data-[state=inactive]:text-primary/40 data-[state=inactive]:hover:text-primary/60'
              )}>
              Job History
            </TabsTrigger>
          </TabsList>

          <TabsContent value='generate' role='tabpanel' className='mt-6 focus-visible:outline-none'>
            <div className='mx-auto max-w-2xl rounded-2xl border border-primary/5 bg-white p-6 sm:p-8'>
              <ReportForm onSuccess={() => setActiveTab('history')} />
            </div>
          </TabsContent>

          <TabsContent value='history' role='tabpanel' className='mt-6 focus-visible:outline-none'>
            <ReportHistoryTable />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
