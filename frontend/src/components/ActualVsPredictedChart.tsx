import React, { useState } from 'react';
import { LineChart as ChartIcon, Filter, AlertCircle } from 'lucide-react';
import type { ActualVsPredictedPoint } from '../services/api';

interface Props {
  data: ActualVsPredictedPoint[];
  selectedMeal: string;
  onMealChange: (meal: string) => void;
}

export const ActualVsPredictedChart: React.FC<Props> = ({ data, selectedMeal, onMealChange }) => {
  const [hoveredPoint, setHoveredPoint] = useState<ActualVsPredictedPoint | null>(null);

  const filteredData = selectedMeal === 'all' 
    ? data 
    : data.filter(d => d.meal_type.toLowerCase() === selectedMeal.toLowerCase());

  // Chart dimensions
  const width = 800;
  const height = 320;
  const padding = { top: 30, right: 30, bottom: 40, left: 60 };

  const innerWidth = width - padding.left - padding.right;
  const innerHeight = height - padding.top - padding.bottom;

  // Compute min/max bounds for Y axis
  const allValues = filteredData.flatMap(d => [d.actual_attendance, d.predicted_attendance]);
  const minVal = allValues.length > 0 ? Math.max(0, Math.min(...allValues) - 80) : 0;
  const maxVal = allValues.length > 0 ? Math.max(...allValues) + 80 : 1600;

  const getY = (val: number) => {
    return innerHeight - ((val - minVal) / (maxVal - minVal || 1)) * innerHeight + padding.top;
  };

  const getX = (idx: number) => {
    return padding.left + (idx / Math.max(1, filteredData.length - 1)) * innerWidth;
  };

  // Build SVG paths
  const actualPath = filteredData.map((d, i) => `${i === 0 ? 'M' : 'L'} ${getX(i)} ${getY(d.actual_attendance)}`).join(' ');
  const predictedPath = filteredData.map((d, i) => `${i === 0 ? 'M' : 'L'} ${getX(i)} ${getY(d.predicted_attendance)}`).join(' ');

  return (
    <div className="glass-panel">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <ChartIcon size={20} color="#3B82F6" />
            <h2 style={{ fontSize: '17px', margin: 0 }}>Actual vs Predicted Attendance Analysis</h2>
          </div>
          <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px' }}>
            Timeline tracking model forecast accuracy across meals, exams, and weekends (PRD Section 14)
          </p>
        </div>

        {/* Meal Filter Tabs */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'var(--bg-input)', padding: '4px', borderRadius: '8px' }}>
          <Filter size={14} color="var(--text-muted)" style={{ marginLeft: '6px' }} />
          {['all', 'breakfast', 'lunch', 'snacks', 'dinner'].map(m => (
            <button
              key={m}
              onClick={() => onMealChange(m)}
              style={{
                background: selectedMeal === m ? '#3B82F6' : 'transparent',
                color: selectedMeal === m ? '#FFFFFF' : 'var(--text-secondary)',
                border: 'none',
                borderRadius: '6px',
                padding: '4px 10px',
                fontSize: '12px',
                fontWeight: 600,
                cursor: 'pointer',
                textTransform: 'capitalize'
              }}
            >
              {m}
            </button>
          ))}
        </div>
      </div>

      {filteredData.length === 0 ? (
        <div style={{ padding: '60px 20px', textAlign: 'center', color: 'var(--text-secondary)' }}>
          <AlertCircle size={32} color="#94A3B8" style={{ marginBottom: '8px' }} />
          <p>No evaluation records available. Click <strong>"Seed Data"</strong> above to load multi-semester history.</p>
        </div>
      ) : (
        <div style={{ position: 'relative', width: '100%', overflowX: 'auto' }}>
          <svg viewBox={`0 0 ${width} ${height}`} style={{ width: '100%', height: 'auto', display: 'block' }}>
            <defs>
              <linearGradient id="actualGlow" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#10B981" stopOpacity="0.3" />
                <stop offset="100%" stopColor="#10B981" stopOpacity="0.0" />
              </linearGradient>
              <linearGradient id="predGlow" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#3B82F6" stopOpacity="0.3" />
                <stop offset="100%" stopColor="#3B82F6" stopOpacity="0.0" />
              </linearGradient>
            </defs>

            {/* Horizontal Grid lines */}
            {[0, 0.25, 0.5, 0.75, 1].map((ratio, i) => {
              const yVal = Math.round(minVal + ratio * (maxVal - minVal));
              const yPos = innerHeight - (ratio * innerHeight) + padding.top;
              return (
                <g key={i}>
                  <line
                    x1={padding.left}
                    y1={yPos}
                    x2={width - padding.right}
                    y2={yPos}
                    stroke="#1E293B"
                    strokeDasharray="4 4"
                  />
                  <text
                    x={padding.left - 10}
                    y={yPos + 4}
                    textAnchor="end"
                    fontSize="11"
                    fill="#64748B"
                    fontFamily="inherit"
                  >
                    {yVal}
                  </text>
                </g>
              );
            })}

            {/* Actual Attendance Line */}
            <path
              d={actualPath}
              fill="none"
              stroke="#10B981"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />

            {/* Predicted Attendance Line */}
            <path
              d={predictedPath}
              fill="none"
              stroke="#3B82F6"
              strokeWidth="2.5"
              strokeDasharray="5 4"
              strokeLinecap="round"
              strokeLinejoin="round"
            />

            {/* Data Points with interactive hover */}
            {filteredData.map((d, i) => {
              const x = getX(i);
              const yAct = getY(d.actual_attendance);
              const yPred = getY(d.predicted_attendance);
              const isHovered = hoveredPoint === d;

              return (
                <g key={i} onMouseEnter={() => setHoveredPoint(d)} style={{ cursor: 'pointer' }}>
                  {/* Vertical hover indicator */}
                  {isHovered && (
                    <line
                      x1={x}
                      y1={padding.top}
                      x2={x}
                      y2={height - padding.bottom}
                      stroke="#475569"
                      strokeWidth="1"
                    />
                  )}
                  {/* Actual dot */}
                  <circle
                    cx={x}
                    cy={yAct}
                    r={isHovered ? 5.5 : 3.5}
                    fill="#10B981"
                    stroke="#0B0F19"
                    strokeWidth="1.5"
                  />
                  {/* Predicted dot */}
                  <circle
                    cx={x}
                    cy={yPred}
                    r={isHovered ? 5.5 : 3.5}
                    fill="#3B82F6"
                    stroke="#0B0F19"
                    strokeWidth="1.5"
                  />
                </g>
              );
            })}

            {/* Date label at start and end */}
            {filteredData.length > 0 && (
              <>
                <text x={padding.left} y={height - 12} fontSize="11" fill="#64748B">
                  {filteredData[0].meal_date}
                </text>
                <text x={width - padding.right} y={height - 12} fontSize="11" fill="#64748B" textAnchor="end">
                  {filteredData[filteredData.length - 1].meal_date}
                </text>
              </>
            )}
          </svg>

          {/* Hover Tooltip Card */}
          {hoveredPoint && (
            <div
              style={{
                position: 'absolute',
                top: '12px',
                right: '16px',
                background: 'rgba(15, 23, 42, 0.95)',
                border: '1px solid #3B82F6',
                borderRadius: '8px',
                padding: '10px 14px',
                fontSize: '12px',
                boxShadow: '0 8px 24px rgba(0,0,0,0.6)',
                minWidth: '220px',
                pointerEvents: 'none',
                backdropFilter: 'blur(8px)'
              }}
            >
              <div style={{ fontWeight: 700, color: '#FFFFFF', marginBottom: '4px' }}>
                {hoveredPoint.meal_date} — <span style={{ textTransform: 'capitalize', color: '#60A5FA' }}>{hoveredPoint.meal_type}</span>
              </div>
              <div style={{ color: 'var(--text-secondary)', marginBottom: '6px' }}>{hoveredPoint.menu_name}</div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '3px' }}>
                <span style={{ color: '#34D399' }}>● Actual Attendance:</span>
                <strong>{hoveredPoint.actual_attendance}</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '3px' }}>
                <span style={{ color: '#60A5FA' }}>● Predicted Attendance:</span>
                <strong>{hoveredPoint.predicted_attendance}</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '4px', paddingTop: '4px', borderTop: '1px solid #334155' }}>
                <span>Prediction Error:</span>
                <strong style={{ color: hoveredPoint.error > 0 ? '#F59E0B' : (hoveredPoint.error < 0 ? '#F43F5E' : '#10B981') }}>
                  {hoveredPoint.error > 0 ? `+${hoveredPoint.error} (Waste)` : `${hoveredPoint.error} (Unmet)`}
                </strong>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Legend */}
      <div style={{ display: 'flex', justifyContent: 'center', gap: '24px', marginTop: '14px', fontSize: '12px', color: 'var(--text-secondary)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#10B981', display: 'inline-block' }}></span>
          <span>Actual Attendance</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#3B82F6', display: 'inline-block' }}></span>
          <span>Predicted Attendance (Random Forest)</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ width: '12px', height: '3px', background: '#F59E0B', display: 'inline-block' }}></span>
          <span>Overprediction = Potential Waste</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ width: '12px', height: '3px', background: '#F43F5E', display: 'inline-block' }}></span>
          <span>Underprediction = Unmet Demand</span>
        </div>
      </div>
    </div>
  );
};
