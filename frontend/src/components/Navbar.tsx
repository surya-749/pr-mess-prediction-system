import React from 'react';
import { ChefHat, Database, RefreshCw, Cpu, Activity, AlertTriangle } from 'lucide-react';
import type { ModelStatus, DriftReport } from '../services/api';

interface NavbarProps {
  modelStatus: ModelStatus | null;
  driftReport: DriftReport | null;
  onSeedData: () => void;
  onRetrain: () => void;
  onRefresh: () => void;
  loadingAction: string | null;
}

export const Navbar: React.FC<NavbarProps> = ({
  modelStatus,
  driftReport,
  onSeedData,
  onRetrain,
  onRefresh,
  loadingAction
}) => {
  const isDriftAlert = driftReport?.drift_detected;

  return (
    <header className="glass-panel" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        <div style={{ width: '48px', height: '48px', borderRadius: '12px', background: 'linear-gradient(135deg, #3B82F6 0%, #06B6D4 100%)', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 4px 12px rgba(6, 182, 212, 0.3)' }}>
          <ChefHat size={26} color="#FFFFFF" />
        </div>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <h1 style={{ fontSize: '20px', margin: 0, fontWeight: 800 }}>AI Food Demand Forecasting Engine</h1>
            <span className="badge badge-blue">College Mess IDP</span>
          </div>
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '2px' }}>
            Random Forest Regression Attendance Forecasting & Kitchen Preparation Optimizer
          </p>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
        {/* Model Version Pill */}
        <div className="badge badge-purple" style={{ padding: '6px 12px', fontSize: '13px' }}>
          <Cpu size={15} />
          <span>Model: <strong>{modelStatus?.active_version || 'Loading...'}</strong></span>
        </div>

        {/* Drift Status Indicator */}
        <div
          className={`badge ${isDriftAlert ? 'badge-rose' : 'badge-emerald'}`}
          style={{ padding: '6px 12px', fontSize: '13px' }}
        >
          {isDriftAlert ? <AlertTriangle size={15} /> : <Activity size={15} />}
          <span>{isDriftAlert ? 'Drift Alert' : 'Model Stable'}</span>
        </div>

        {/* Action Buttons */}
        <button
          className="btn btn-secondary"
          onClick={onSeedData}
          disabled={loadingAction !== null}
          title="Populates 300+ days multi-semester academic data and trains baseline model"
        >
          <Database size={15} />
          <span>{loadingAction === 'seed' ? 'Generating 300d Data...' : 'Seed Data'}</span>
        </button>

        <button
          className="btn btn-primary"
          onClick={onRetrain}
          disabled={loadingAction !== null}
          title="Retrain Random Forest with accumulated feedback records"
        >
          <RefreshCw size={15} className={loadingAction === 'retrain' ? 'animate-spin' : ''} />
          <span>{loadingAction === 'retrain' ? 'Retraining RF...' : 'Retrain Model'}</span>
        </button>

        <button
          className="btn btn-secondary"
          onClick={onRefresh}
          disabled={loadingAction !== null}
          title="Refresh dashboard metrics"
        >
          <RefreshCw size={15} />
        </button>
      </div>
    </header>
  );
};
