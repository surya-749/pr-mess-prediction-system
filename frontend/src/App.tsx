import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { MetricCards } from './components/MetricCards';
import { ActualVsPredictedChart } from './components/ActualVsPredictedChart';
import { FeatureImportanceChart } from './components/FeatureImportanceChart';
import { PredictionAndKitchenPlanner } from './components/PredictionAndKitchenPlanner';
import { FeedbackAndDriftModal } from './components/FeedbackAndDriftModal';
import {
  fetchModelStatus,
  fetchEvaluation,
  fetchFeatureImportance,
  fetchActualVsPredicted,
  fetchDriftReport,
  triggerRetrain,
  triggerSeedData
} from './services/api';
import type {
  ModelStatus,
  EvaluationMetrics,
  FeatureImportance,
  ActualVsPredictedPoint,
  DriftReport
} from './services/api';
import { Sparkles, LineChart, BarChart2, MessageSquare, CheckCircle, AlertCircle } from 'lucide-react';

export const App: React.FC = () => {
  // Navigation
  const [activeTab, setActiveTab] = useState<'planner' | 'analytics' | 'features' | 'feedback'>('planner');

  // App Data
  const [modelStatus, setModelStatus] = useState<ModelStatus | null>(null);
  const [metrics, setMetrics] = useState<EvaluationMetrics | null>(null);
  const [features, setFeatures] = useState<FeatureImportance[]>([]);
  const [chartData, setChartData] = useState<ActualVsPredictedPoint[]>([]);
  const [selectedMeal, setSelectedMeal] = useState<string>('all');
  const [driftReport, setDriftReport] = useState<DriftReport | null>(null);

  // Status banners & action loaders
  const [loadingAction, setLoadingAction] = useState<string | null>(null);
  const [banner, setBanner] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  const loadAllData = async () => {
    try {
      const statusRes = await fetchModelStatus();
      setModelStatus(statusRes);

      if (statusRes.is_loaded) {
        const [evalRes, featRes, chartRes, driftRes] = await Promise.all([
          fetchEvaluation().catch(() => null),
          fetchFeatureImportance().catch(() => []),
          fetchActualVsPredicted(80).catch(() => []),
          fetchDriftReport().catch(() => null)
        ]);

        if (evalRes) setMetrics(evalRes);
        if (featRes) setFeatures(featRes);
        if (chartRes) setChartData(chartRes);
        if (driftRes) setDriftReport(driftRes);
      }
    } catch (err: any) {
      console.error('Failed to load dashboard data:', err);
    }
  };

  useEffect(() => {
    loadAllData();
  }, []);

  // Seed Data Trigger
  const handleSeedData = async () => {
    setLoadingAction('seed');
    setBanner(null);
    try {
      const res = await triggerSeedData(300);
      setBanner({
        type: 'success',
        message: `Dataset seeded with ${res.records_count} historical meals! Baseline model ${res.version_tag} trained.`
      });
      await loadAllData();
    } catch (err: any) {
      setBanner({ type: 'error', message: err.message || 'Failed to seed data' });
    } finally {
      setLoadingAction(null);
    }
  };

  // Retrain Trigger
  const handleRetrain = async () => {
    setLoadingAction('retrain');
    setBanner(null);
    try {
      const res = await triggerRetrain();
      const msg = res.promoted_to_active
        ? `Model retrained successfully! Promoted new active model: ${res.version_tag} (MAE: ${res.candidate_metrics.mae}).`
        : `Candidate model ${res.version_tag} evaluated. ${res.promotion_reason}`;
      setBanner({ type: 'success', message: msg });
      await loadAllData();
    } catch (err: any) {
      setBanner({ type: 'error', message: err.message || 'Retraining failed' });
    } finally {
      setLoadingAction(null);
    }
  };

  return (
    <>
      <Navbar
        modelStatus={modelStatus}
        driftReport={driftReport}
        onSeedData={handleSeedData}
        onRetrain={handleRetrain}
        onRefresh={loadAllData}
        loadingAction={loadingAction}
      />

      {/* Action Notification Banner */}
      {banner && (
        <div
          style={{
            padding: '12px 18px',
            borderRadius: '10px',
            background: banner.type === 'success' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(244, 63, 94, 0.15)',
            border: `1px solid ${banner.type === 'success' ? '#10B981' : '#F43F5E'}`,
            color: banner.type === 'success' ? '#34D399' : '#FB7185',
            fontSize: '14px',
            display: 'flex',
            alignItems: 'center',
            gap: '10px'
          }}
        >
          {banner.type === 'success' ? <CheckCircle size={18} /> : <AlertCircle size={18} />}
          <span>{banner.message}</span>
        </div>
      )}

      {/* Model Performance Overview (PRD Section 13) */}
      <MetricCards metrics={metrics} status={modelStatus} />

      {/* Tabs Navigation */}
      <div className="tabs-container">
        <button
          className={`tab-btn ${activeTab === 'planner' ? 'active' : ''}`}
          onClick={() => setActiveTab('planner')}
        >
          <Sparkles size={16} />
          Demand Forecaster & Kitchen Planner
        </button>

        <button
          className={`tab-btn ${activeTab === 'analytics' ? 'active' : ''}`}
          onClick={() => setActiveTab('analytics')}
        >
          <LineChart size={16} />
          Actual vs Predicted Analytics
        </button>

        <button
          className={`tab-btn ${activeTab === 'features' ? 'active' : ''}`}
          onClick={() => setActiveTab('features')}
        >
          <BarChart2 size={16} />
          Feature Importance
        </button>

        <button
          className={`tab-btn ${activeTab === 'feedback' ? 'active' : ''}`}
          onClick={() => setActiveTab('feedback')}
        >
          <MessageSquare size={16} />
          Post-Meal Feedback & Model Drift
        </button>
      </div>

      {/* Tab Panels */}
      {activeTab === 'planner' && (
        <PredictionAndKitchenPlanner />
      )}

      {activeTab === 'analytics' && (
        <ActualVsPredictedChart
          data={chartData}
          selectedMeal={selectedMeal}
          onMealChange={setSelectedMeal}
        />
      )}

      {activeTab === 'features' && (
        <FeatureImportanceChart features={features} />
      )}

      {activeTab === 'feedback' && (
        <FeedbackAndDriftModal
          driftReport={driftReport}
          onFeedbackLogged={loadAllData}
          onRetrain={handleRetrain}
          loadingAction={loadingAction}
        />
      )}
    </>
  );
};

export default App;
