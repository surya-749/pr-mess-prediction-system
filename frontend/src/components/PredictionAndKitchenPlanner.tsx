import React, { useState, useEffect } from 'react';
import { Utensils, Sparkles, Scale, Sliders, Calendar, Users, FileText } from 'lucide-react';
import {
  predictAttendance,
  fetchFoodRequirement
} from '../services/api';
import type {
  PredictionResult,
  FoodRequirementResponse
} from '../services/api';

export const PredictionAndKitchenPlanner: React.FC = () => {
  // Form State
  const [date, setDate] = useState('2026-09-20');
  const [meal, setMeal] = useState('lunch');
  const [menu, setMenu] = useState('Chicken Biryani / Paneer Biryani');
  const [dishCategory, setDishCategory] = useState('Special');
  const [isHoliday, setIsHoliday] = useState(false);
  const [isExam, setIsExam] = useState(false);
  const [expectedStudents, setExpectedStudents] = useState(1500);
  const [bufferPct, setBufferPct] = useState(3.0);

  // Results State
  const [loading, setLoading] = useState(false);
  const [prediction, setPrediction] = useState<PredictionResult | null>(null);
  const [foodReq, setFoodReq] = useState<FoodRequirementResponse | null>(null);

  // Pre-fill menus based on meal
  const handleMealChange = (newMeal: string) => {
    setMeal(newMeal);
    if (newMeal === 'breakfast') {
      setMenu('Idli Sambar & Vada');
      setDishCategory('South Indian');
    } else if (newMeal === 'lunch') {
      setMenu('Chicken Biryani / Paneer Biryani');
      setDishCategory('Special');
    } else if (newMeal === 'snacks') {
      setMenu('Samosa & Masala Chai');
      setDishCategory('Snack');
    } else {
      setMenu('Butter Chicken / Paneer Butter Masala & Naan');
      setDishCategory('Special');
    }
  };

  // Run prediction
  const handlePredict = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setLoading(true);
    try {
      const predRes = await predictAttendance({
        date,
        meal,
        menu,
        dish_category: dishCategory,
        is_holiday: isHoliday,
        is_exam: isExam,
        expected_students: expectedStudents
      });
      setPrediction(predRes);

      // Immediately calculate food requirements
      const isSpecial = dishCategory === 'Special' || menu.toLowerCase().includes('biryani') || menu.toLowerCase().includes('chicken') || menu.toLowerCase().includes('paneer');
      const foodRes = await fetchFoodRequirement(
        predRes.predicted_attendance,
        meal,
        isSpecial,
        bufferPct
      );
      setFoodReq(foodRes);
    } catch (err) {
      console.error('Prediction error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Recalculate food requirements when buffer percentage changes
  useEffect(() => {
    if (prediction) {
      const isSpecial = dishCategory === 'Special' || menu.toLowerCase().includes('biryani') || menu.toLowerCase().includes('chicken') || menu.toLowerCase().includes('paneer');
      fetchFoodRequirement(prediction.predicted_attendance, meal, isSpecial, bufferPct)
        .then(setFoodReq)
        .catch(console.error);
    }
  }, [bufferPct]);

  // Initial run on mount
  useEffect(() => {
    handlePredict();
  }, []);

  return (
    <div className="grid-two-col">
      {/* Forecasting Input Card */}
      <div className="glass-panel">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
          <Sparkles size={20} color="#3B82F6" />
          <h2 style={{ fontSize: '17px', margin: 0 }}>Upcoming Meal Demand Forecaster</h2>
        </div>

        <form onSubmit={handlePredict}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
            {/* Date */}
            <div className="form-group">
              <label><Calendar size={13} style={{ display: 'inline', marginRight: '4px' }} /> Meal Date</label>
              <input
                type="date"
                value={date}
                onChange={e => setDate(e.target.value)}
                required
              />
            </div>

            {/* Meal Type */}
            <div className="form-group">
              <label><Utensils size={13} style={{ display: 'inline', marginRight: '4px' }} /> Meal Type</label>
              <select value={meal} onChange={e => handleMealChange(e.target.value)}>
                <option value="breakfast">Breakfast</option>
                <option value="lunch">Lunch</option>
                <option value="snacks">Snacks</option>
                <option value="dinner">Dinner</option>
              </select>
            </div>
          </div>

          {/* Menu Name */}
          <div className="form-group">
            <label>Menu Item</label>
            <input
              type="text"
              value={menu}
              onChange={e => setMenu(e.target.value)}
              placeholder="e.g. Chicken Biryani / Paneer Biryani"
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
            {/* Dish Category */}
            <div className="form-group">
              <label>Dish Category</label>
              <select value={dishCategory} onChange={e => setDishCategory(e.target.value)}>
                <option value="Special">Special (Non-Veg / Paneer)</option>
                <option value="North Indian">North Indian</option>
                <option value="South Indian">South Indian</option>
                <option value="Snack">Snack</option>
                <option value="Light">Light / Regular</option>
              </select>
            </div>

            {/* Expected Campus Students */}
            <div className="form-group">
              <label><Users size={13} style={{ display: 'inline', marginRight: '4px' }} /> Hostel Population: <strong>{expectedStudents}</strong></label>
              <input
                type="range"
                min="500"
                max="1800"
                step="50"
                value={expectedStudents}
                onChange={e => setExpectedStudents(Number(e.target.value))}
                style={{ accentColor: '#3B82F6', marginTop: '8px' }}
              />
            </div>
          </div>

          {/* Exam & Holiday Checkboxes */}
          <div style={{ display: 'flex', gap: '20px', margin: '14px 0' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={isExam}
                onChange={e => setIsExam(e.target.checked)}
                style={{ width: '16px', height: '16px', accentColor: '#3B82F6' }}
              />
              <span>Exam Week (CAT / FAT)</span>
            </label>

            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={isHoliday}
                onChange={e => setIsHoliday(e.target.checked)}
                style={{ width: '16px', height: '16px', accentColor: '#3B82F6' }}
              />
              <span>Campus Holiday</span>
            </label>
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            style={{ width: '100%', marginTop: '6px' }}
            disabled={loading}
          >
            {loading ? 'Running Random Forest Model...' : 'Forecast Student Demand & Prep Quantities'}
          </button>
        </form>

        {/* Prediction Results Banner (PRD Section 9) */}
        {prediction && (
          <div style={{ marginTop: '20px', padding: '16px', background: 'linear-gradient(135deg, rgba(37, 99, 235, 0.15) 0%, rgba(16, 185, 129, 0.1) 100%)', border: '1px solid rgba(59, 130, 246, 0.35)', borderRadius: '12px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <span style={{ fontSize: '12px', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Expected Attendance Forecast
                </span>
                <div style={{ fontSize: '36px', fontWeight: 800, color: '#FFFFFF', lineHeight: 1.1, marginTop: '4px' }}>
                  {prediction.predicted_attendance.toLocaleString()}
                  <span style={{ fontSize: '16px', fontWeight: 500, color: '#93C5FD', marginLeft: '8px' }}>students</span>
                </div>
              </div>
              <span className="badge badge-purple">{prediction.model_version}</span>
            </div>

            <div style={{ display: 'flex', gap: '20px', marginTop: '14px', paddingTop: '12px', borderTop: '1px solid rgba(255, 255, 255, 0.1)', fontSize: '13px' }}>
              <div>
                <span style={{ color: 'var(--text-muted)' }}>Estimated Confidence Range: </span>
                <strong style={{ color: '#38BDF8' }}>{prediction.range_low.toLocaleString()} – {prediction.range_high.toLocaleString()}</strong>
              </div>
              <div>
                <span style={{ color: 'var(--text-muted)' }}>Meal: </span>
                <strong style={{ textTransform: 'capitalize' }}>{meal}</strong>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Kitchen Food Requirement Sheet (PRD Section 10) */}
      <div className="glass-panel">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Scale size={20} color="#10B981" />
            <h2 style={{ fontSize: '17px', margin: 0 }}>Kitchen Preparation Recommendation</h2>
          </div>
          <span className="badge badge-emerald">Operational Targets</span>
        </div>

        {/* Safety Buffer Slider */}
        <div style={{ background: 'var(--bg-input)', padding: '12px 16px', borderRadius: '10px', marginBottom: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', margin: 0 }}>
              <Sliders size={14} color="#38BDF8" />
              Kitchen Safety Buffer: <strong>+{bufferPct}%</strong>
            </label>
            <span style={{ fontSize: '12px', color: '#34D399' }}>
              Preps for <strong>{foodReq?.effective_preparation_headcount || '--'}</strong> students
            </span>
          </div>
          <input
            type="range"
            min="0"
            max="10"
            step="0.5"
            value={bufferPct}
            onChange={e => setBufferPct(Number(e.target.value))}
            style={{ width: '100%', accentColor: '#10B981' }}
          />
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
            Buffer prevents shortages during unexpected crowd surges while bounding potential waste.
          </div>
        </div>

        {/* Ingredients Table */}
        {foodReq ? (
          <div style={{ overflowX: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Ingredient / Item</th>
                  <th>Per Student</th>
                  <th>Base Quantity</th>
                  <th>Recommended Prep</th>
                </tr>
              </thead>
              <tbody>
                {foodReq.ingredients.map((item, i) => (
                  <tr key={i}>
                    <td>
                      <strong>{item.item_name}</strong>
                    </td>
                    <td style={{ color: 'var(--text-secondary)' }}>{item.per_student_consumption}</td>
                    <td style={{ color: 'var(--text-muted)' }}>
                      {item.base_quantity} {item.unit}
                    </td>
                    <td>
                      <span className="mono" style={{ fontSize: '15px', fontWeight: 700, color: '#34D399' }}>
                        {item.recommended_quantity} {item.unit}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-secondary)' }}>
            Submit prediction to generate operational kitchen quantities.
          </div>
        )}

        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '16px' }}>
          <button
            className="btn btn-secondary"
            onClick={() => window.print()}
            style={{ fontSize: '13px' }}
          >
            <FileText size={14} />
            Print Kitchen Prep Sheet
          </button>
        </div>
      </div>
    </div>
  );
};
