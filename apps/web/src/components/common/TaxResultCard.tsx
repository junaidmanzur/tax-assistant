import { useState } from 'react';

interface TaxResultCardProps {
  baseTax: number;
  medicareLevy: number;
  mls: number;
  lito: number;
  totalTax: number;
  takeHome: number;
  income: number;
}

export default function TaxResultCard({
  baseTax,
  medicareLevy,
  mls,
  lito,
  totalTax,
  takeHome,
  income
}: TaxResultCardProps) {
  const [showMonthly, setShowMonthly] = useState(false);

  const formatCurrency = (amount: number) =>
    new Intl.NumberFormat('en-AU', {
      style: 'currency',
      currency: 'AUD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount).replace('A$', '$');

  const monthlyTakeHome = takeHome / 12;

  return (
    <div className="rounded-xl border-2 border-accent/40 bg-[#0f1117] p-6 my-4 max-w-md">
      {/* Header */}
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-text mb-1">Your Tax Calculation</h3>
        <div className="text-3xl font-bold text-accent mb-2">
          {formatCurrency(totalTax)} total tax
        </div>
        <div className="text-muted">
          <span>Take-home: {formatCurrency(showMonthly ? monthlyTakeHome : takeHome)} </span>
          <button
            onClick={() => setShowMonthly(!showMonthly)}
            className={`transition-colors cursor-pointer px-2 py-0.5 rounded ${
              showMonthly
                ? 'text-accent bg-accent/10 hover:bg-accent/15'
                : 'text-accent bg-accent/10 hover:bg-accent/15'
            }`}
          >
            {showMonthly ? 'monthly' : 'annually'}
          </button>
        </div>
      </div>

      {/* Breakdown */}
      <div className="space-y-3 border-t border-border pt-4">
        <div className="flex justify-between items-center">
          <span className="text-text">Income Tax</span>
          <span className="font-semibold text-text">{formatCurrency(baseTax)}</span>
        </div>
        
        <div className="flex justify-between items-center">
          <span className="text-text">Medicare Levy (2%)</span>
          <span className="font-semibold text-text">{formatCurrency(medicareLevy)}</span>
        </div>
        
        <div className="flex justify-between items-center">
          <span className="text-text">Medicare Levy Surcharge</span>
          <span className="font-semibold text-text">{formatCurrency(mls)}</span>
        </div>
        
        {lito > 0 && (
          <div className="flex justify-between items-center">
            <span className="text-text">Low Income Tax Offset</span>
            <span className="font-semibold text-accent">-{formatCurrency(lito)}</span>
          </div>
        )}
        
        <div className="flex justify-between items-center border-t border-border pt-3 mt-3">
          <span className="font-bold text-text text-lg">Total Tax</span>
          <span className="font-bold text-text text-lg">{formatCurrency(totalTax)}</span>
        </div>
      </div>
    </div>
  );
}