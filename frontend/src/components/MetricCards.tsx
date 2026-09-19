import React from 'react';
import { Target, TrendingDown, CheckCircle, ShieldAlert, Percent, Database } from 'lucide-react';
import type { EvaluationMetrics, ModelStatus } from '../services/api';

interface MetricCardsProps {
  metrics: EvaluationMetrics | null;
  status: ModelStatus | null;
}

export const MetricCards: React.FC<MetricCardsProps> = ({ metrics, status }) => {
  return (
    <div className="grid-metrics">
      {/* MAE Card */}
      <div className="metric-box cyan">
        <div className="metric-title">
          <span>Mean Absolute Error</span>
          <Target size={18} color="#06B6D4" />
        </div>
        <div className="metric-value">
          {metrics ? `${metrics.mae}` : '--'}
          <span style={{ fontSize: '15px', fontWeight: 500, color: 'var(--text-secondary)', marginLeft: '6px' }}>students</span>
        </div>
        <div className="metric-subtext">Avg deviation from actual attendance</div>
      </div>

      {/* RMSE Card */}
      <div className="metric-box violet">
        <div className="metric-title">
          <span>RMSE</span>
          <TrendingDown size={18} color="#8B5CF6" />
        </div>
        <div className="metric-value">
          {metrics ? `${metrics.rmse}` : '--'}
          <span style={{ fontSize: '15px', fontWeight: 500, color: 'var(--text-secondary)', marginLeft: '6px' }}>students</span>
        </div>
        <div className="metric-subtext">Penalizes large swings and surges</div>
      </div>

      {/* R² Card */}
      <div className="metric-box emerald">
        <div className="metric-title">
          <span>R² Score (Goodness)</span>
          <CheckCircle size={18} color="#10B981" />
        </div>
        <div className="metric-value">
          {metrics ? `${metrics.r2}` : '--'}
        </div>
        <div className="metric-subtext">Proportion of variance explained</div>
      </div>

      {/* MAPE / Error Rate */}
      <div className="metric-box">
        <div className="metric-title">
          <span>Prediction Error</span>
          <Percent size={18} color="#3B82F6" />
        </div>
        <div className="metric-value">
          {metrics ? `${metrics.mape}%` : '--'}
        </div>
        <div className="metric-subtext">Mean Absolute Percentage Error</div>
      </div>

      {/* Potential Waste Rate */}
      <div className="metric-box amber">
        <div className="metric-title">
          <span>Potential Waste</span>
          <ShieldAlert size={18} color="#F59E0B" />
        </div>
        <div className="metric-value">
          {metrics ? `${metrics.waste_rate_pct}%` : '--'}
        </div>
        <div className="metric-subtext">
          {metrics ? `${metrics.total_waste} student meals overproduced` : 'Overprediction buffer'}
        </div>
      </div>

      {/* Unmet Demand Rate */}
      <div className="metric-box rose">
        <div className="metric-title">
          <span>Unmet Demand</span>
          <ShieldAlert size={18} color="#F43F5E" />
        </div>
        <div className="metric-value">
          {metrics ? `${metrics.unmet_rate_pct}%` : '--'}
        </div>
        <div className="metric-subtext">
          {metrics ? `${metrics.total_unmet_demand} student meals short` : 'Underprediction shortages'}
        </div>
      </div>

      {/* Dataset / Model Version */}
      <div className="metric-box">
        <div className="metric-title">
          <span>Training Records</span>
          <Database size={18} color="#94A3B8" />
        </div>
        <div className="metric-value">
          {status ? status.training_records_count.toLocaleString() : '--'}
        </div>
        <div className="metric-subtext">
          Model: <strong>{status?.active_version || 'RF-v1.0'}</strong> ({status?.hyperparameters?.n_estimators || 150} trees)
        </div>
      </div>
    </div>
  );
};
