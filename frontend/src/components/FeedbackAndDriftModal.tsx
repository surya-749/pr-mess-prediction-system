import React, { useState } from 'react';
import { CheckSquare, AlertTriangle, RefreshCw, Send, CheckCircle2 } from 'lucide-react';
import { submitFeedback } from '../services/api';
import type { DriftReport } from '../services/api';

interface Props {
  driftReport: DriftReport | null;
  onFeedbackLogged: () => void;
  onRetrain: () => void;
  loadingAction: string | null;
}

export const FeedbackAndDriftModal: React.FC<Props> = ({
  driftReport,
  onFeedbackLogged,
  onRetrain,
  loadingAction
}) => {
  // Feedback form state
  const [mealDate, setMealDate] = useState('2026-09-20');
  const [mealType, setMealType] = useState('lunch');
  const [predicted, setPredicted] = useState(1247);
  const [actual, setActual] = useState(1218);
  const [menuName, setMenuName] = useState('Chicken Biryani / Paneer Biryani');
  const [notes, setNotes] = useState('Turnout recorded at biometric turnstile');
  const [submitting, setSubmitting] = useState(false);
  const [lastSubmitted, setLastSubmitted] = useState<any>(null);

  const error = predicted - actual;
  const waste = Math.max(error, 0);
  const unmet = Math.max(-error, 0);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const res = await submitFeedback({
        meal_date: mealDate,
        meal_type: mealType,
        predicted_attendance: Number(predicted),
        actual_attendance: Number(actual),
        menu_name: menuName,
        notes: notes
      });
      setLastSubmitted(res);
      onFeedbackLogged();
    } catch (err) {
      console.error('Feedback error:', err);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="grid-two-col">
      {/* Feedback Logging Form (PRD Section 11) */}
      <div className="glass-panel">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
          <CheckSquare size={20} color="#10B981" />
          <h2 style={{ fontSize: '17px', margin: 0 }}>Log Post-Meal Actual Attendance</h2>
        </div>
        <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '16px' }}>
          Compare prediction against real turnstile headcounts to accumulate retraining data (PRD Section 11)
        </p>

        <form onSubmit={handleSubmit}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
            <div className="form-group">
              <label>Meal Date</label>
              <input
                type="date"
                value={mealDate}
                onChange={e => setMealDate(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label>Meal Type</label>
              <select value={mealType} onChange={e => setMealType(e.target.value)}>
                <option value="breakfast">Breakfast</option>
                <option value="lunch">Lunch</option>
                <option value="snacks">Snacks</option>
                <option value="dinner">Dinner</option>
              </select>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
            <div className="form-group">
              <label>Predicted Attendance</label>
              <input
                type="number"
                value={predicted}
                onChange={e => setPredicted(Number(e.target.value))}
                required
              />
            </div>

            <div className="form-group">
              <label>Actual Attendance (Turnstile)</label>
              <input
                type="number"
                value={actual}
                onChange={e => setActual(Number(e.target.value))}
                required
              />
            </div>
          </div>

          {/* Real-time calculated Waste / Unmet callout */}
          <div style={{ display: 'flex', gap: '14px', marginBottom: '16px', background: 'var(--bg-input)', padding: '12px', borderRadius: '8px' }}>
            <div style={{ flex: 1 }}>
              <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Prediction Error:</span>
              <div style={{ fontSize: '18px', fontWeight: 700, color: error === 0 ? '#10B981' : (error > 0 ? '#F59E0B' : '#F43F5E') }}>
                {error > 0 ? `+${error}` : error} students
              </div>
            </div>
            <div style={{ flex: 1 }}>
              <span style={{ fontSize: '11px', color: '#F59E0B' }}>Potential Food Waste:</span>
              <div style={{ fontSize: '18px', fontWeight: 700, color: '#F59E0B' }}>
                {waste} meals
              </div>
            </div>
            <div style={{ flex: 1 }}>
              <span style={{ fontSize: '11px', color: '#F43F5E' }}>Unmet Demand:</span>
              <div style={{ fontSize: '18px', fontWeight: 700, color: '#F43F5E' }}>
                {unmet} meals
              </div>
            </div>
          </div>

          <div className="form-group">
            <label>Menu Item</label>
            <input
              type="text"
              value={menuName}
              onChange={e => setMenuName(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label>Operational Notes</label>
            <input
              type="text"
              value={notes}
              onChange={e => setNotes(e.target.value)}
              placeholder="e.g. Heavy rain during lunch hour"
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            style={{ width: '100%', marginTop: '4px' }}
            disabled={submitting}
          >
            <Send size={15} />
            <span>{submitting ? 'Recording Outcome...' : 'Submit Post-Meal Feedback'}</span>
          </button>
        </form>

        {lastSubmitted && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '12px', color: '#34D399', fontSize: '13px' }}>
            <CheckCircle2 size={16} />
            <span>Successfully recorded feedback #<strong>{lastSubmitted.id}</strong> into retraining pool.</span>
          </div>
        )}
      </div>

      {/* Model Drift & Retraining Monitor (PRD Section 16 & 17) */}
      <div className="glass-panel">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertTriangle size={20} color={driftReport?.drift_detected ? '#F43F5E' : '#10B981'} />
            <h2 style={{ fontSize: '17px', margin: 0 }}>Model Drift & Retraining Engine</h2>
          </div>
          <span className={`badge ${driftReport?.drift_detected ? 'badge-rose' : 'badge-emerald'}`}>
            {driftReport?.status || 'MONITORING'}
          </span>
        </div>

        <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '16px' }}>
          Tracks error deterioration over time caused by semester transitions or student appetite shifts (PRD Section 17)
        </p>

        {driftReport ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <div className="metric-box" style={{ padding: '12px' }}>
                <span className="metric-title">Baseline MAE</span>
                <div style={{ fontSize: '20px', fontWeight: 800 }}>{driftReport.baseline_mae}</div>
                <div className="metric-subtext">Training benchmark error</div>
              </div>

              <div className="metric-box" style={{ padding: '12px' }}>
                <span className="metric-title">Recent Rolling MAE</span>
                <div style={{ fontSize: '20px', fontWeight: 800, color: driftReport.drift_detected ? '#F43F5E' : '#34D399' }}>
                  {driftReport.recent_mae !== null ? driftReport.recent_mae : 'N/A'}
                </div>
                <div className="metric-subtext">Past 14 meals window</div>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <div className="metric-box" style={{ padding: '12px' }}>
                <span className="metric-title">Drift Threshold</span>
                <div style={{ fontSize: '20px', fontWeight: 800 }}>
                  {driftReport.threshold_mae !== null ? driftReport.threshold_mae : '--'}
                </div>
                <div className="metric-subtext">1.35x baseline trigger</div>
              </div>

              <div className="metric-box" style={{ padding: '12px' }}>
                <span className="metric-title">Systematic Bias</span>
                <div style={{ fontSize: '18px', fontWeight: 800, color: driftReport.bias > 0 ? '#F59E0B' : '#60A5FA' }}>
                  {driftReport.bias > 0 ? `+${driftReport.bias}` : driftReport.bias}
                </div>
                <div className="metric-subtext">{driftReport.bias_direction}</div>
              </div>
            </div>

            {/* Drift Recommendation Alert */}
            <div style={{ padding: '14px', borderRadius: '10px', background: driftReport.drift_detected ? 'rgba(244, 63, 94, 0.15)' : 'rgba(16, 185, 129, 0.1)', border: `1px solid ${driftReport.drift_detected ? 'rgba(244, 63, 94, 0.3)' : 'rgba(16, 185, 129, 0.3)'}`, fontSize: '13px' }}>
              <div style={{ fontWeight: 700, marginBottom: '4px', color: driftReport.drift_detected ? '#FB7185' : '#34D399' }}>
                {driftReport.message}
              </div>
              <div style={{ color: 'var(--text-secondary)' }}>
                <strong>Recommendation:</strong> {driftReport.recommended_action}
              </div>
            </div>

            {/* Scheduled / Manual Retraining Trigger */}
            <div style={{ marginTop: '6px' }}>
              <button
                className="btn btn-primary"
                onClick={onRetrain}
                disabled={loadingAction !== null}
                style={{ width: '100%', justifyContent: 'center' }}
              >
                <RefreshCw size={15} className={loadingAction === 'retrain' ? 'animate-spin' : ''} />
                <span>
                  {loadingAction === 'retrain' ? 'Retraining & Evaluating Candidate Model...' : 'Execute Rolling Model Retraining'}
                </span>
              </button>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', textAlign: 'center', marginTop: '6px' }}>
                Retrains Random Forest on full historical + feedback dataset. Evaluates chronologically and promotes only if MAE improves.
              </div>
            </div>
          </div>
        ) : (
          <div style={{ padding: '30px', textAlign: 'center', color: 'var(--text-secondary)' }}>
            Loading drift metrics...
          </div>
        )}
      </div>
    </div>
  );
};
