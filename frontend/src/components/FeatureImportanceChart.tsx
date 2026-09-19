import React from 'react';
import { BarChart3, HelpCircle } from 'lucide-react';
import type { FeatureImportance } from '../services/api';

interface Props {
  features: FeatureImportance[];
}

const FEATURE_LABELS: Record<string, string> = {
  attendance_lag_1: 'Previous Day Attendance (Lag 1)',
  attendance_lag_7: 'Previous Week Attendance (Lag 7)',
  expected_students: 'Expected Students on Campus',
  rolling_mean_7: '7-Day Rolling Attendance Mean',
  rolling_mean_14: '14-Day Rolling Attendance Mean',
  attendance_lag_2: '2-Day Prior Attendance',
  attendance_lag_3: '3-Day Prior Attendance',
  historical_menu_popularity: 'Historical Menu Popularity',
  day_of_week: 'Day of Week / Weekend Dynamics',
  is_exam: 'Academic Exam Active (CAT/FAT)',
  is_fat: 'FAT (Final Exam Travel Dip)',
  is_cat1: 'CAT-1 Examination',
  is_cat2: 'CAT-2 Examination',
  days_to_exam: 'Days Until Next Exam',
  meal_type_code: 'Meal Type (Breakfast/Lunch/Snacks/Dinner)',
  dish_category_code: 'Dish Category (Special/North/South)',
  is_holiday: 'Public / Campus Holiday',
  is_weekend: 'Weekend Mass Leave',
  is_special_dish: 'Special Non-Veg / Paneer Menu',
  expected_class_attendance: 'Classroom Lecture Attendance'
};

export const FeatureImportanceChart: React.FC<Props> = ({ features }) => {
  const topFeatures = features.slice(0, 8);

  return (
    <div className="glass-panel">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <BarChart3 size={20} color="#8B5CF6" />
            <h2 style={{ fontSize: '17px', margin: 0 }}>Random Forest Feature Importance</h2>
          </div>
          <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px' }}>
            Explains which factors drive attendance forecasts (PRD Section 15)
          </p>
        </div>
        <span className="badge badge-purple">MDI Interpretability</span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {topFeatures.map((f, i) => {
          const label = FEATURE_LABELS[f.feature] || f.feature;
          return (
            <div key={i} style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
                <span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>{label}</span>
                <span className="mono" style={{ color: '#A78BFA', fontWeight: 600 }}>
                  {f.percentage}%
                </span>
              </div>
              <div className="progress-bar-bg">
                <div
                  className="progress-bar-fill"
                  style={{
                    width: `${Math.min(100, f.percentage * 2.5)}%`,
                    background: i === 0 ? 'linear-gradient(90deg, #8B5CF6 0%, #3B82F6 100%)' : 'linear-gradient(90deg, #3B82F6 0%, #06B6D4 100%)'
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>

      <div style={{ marginTop: '18px', padding: '12px', background: 'rgba(30, 41, 59, 0.4)', borderRadius: '8px', fontSize: '12px', color: 'var(--text-secondary)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px', color: '#93C5FD' }}>
          <HelpCircle size={14} />
          <strong>Key ML Insight</strong>
        </div>
        Attendance is heavily anchored on recent meal lags (Lag 1 & 7) modulated by academic exams (CAT/FAT) and special menu popularity boosts (Biryani / Paneer).
      </div>
    </div>
  );
};
