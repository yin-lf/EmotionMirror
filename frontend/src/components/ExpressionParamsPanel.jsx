import { useState } from 'react';
import ParamSlider from './ParamSlider';
import { getExpressionParams } from '../services/api';

export default function ExpressionParamsPanel({ emotion, onIntensityChange, onParamsChange }) {
  const [intensity, setIntensity] = useState(5);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [meta, setMeta] = useState(null);
  const [values, setValues] = useState({});

  const handleToggleAdvanced = async () => {
    if (!showAdvanced && !meta) {
      const data = await getExpressionParams();
      setMeta(data);
      const defaults = data.defaults[emotion] || {};
      const next = {};
      for (const key of Object.keys(data.ranges)) {
        next[key] = defaults[key] ?? data.ranges[key].default;
      }
      setValues(next);
    }
    setShowAdvanced(!showAdvanced);
  };

  const handleIntensityChange = (val) => {
    setIntensity(val);
    onIntensityChange(val);
  };

  const handleParamChange = (key, val) => {
    const next = { ...values, [key]: val };
    setValues(next);
    if (onParamsChange) onParamsChange(next);
  };

  const resetAll = () => {
    if (!meta) return;
    const defaults = meta.defaults[emotion] || {};
    const next = {};
    for (const key of Object.keys(meta.ranges)) {
      next[key] = defaults[key] ?? meta.ranges[key].default;
    }
    setValues(next);
    if (onParamsChange) onParamsChange(next);
  };

  return (
    <div className="expression-params-panel">
      <div className="expression-params-header">
        <span>表情调节</span>
        <button type="button" className="btn btn-ghost expression-params-toggle" onClick={handleToggleAdvanced}>
          {showAdvanced ? '收起高级选项' : '高级选项'}
        </button>
      </div>

      <ParamSlider
        label="情绪强度"
        value={intensity}
        min={1}
        max={5}
        step={1}
        defaultValue={5}
        onChange={handleIntensityChange}
      />

      {showAdvanced && meta && (
        <>
          <div className="expression-params-divider" />
          <div className="expression-params-advanced-header">
            <span>高级参数</span>
            <button type="button" className="btn btn-ghost expression-params-reset-all" onClick={resetAll}>
              全部重置
            </button>
          </div>
          {Object.entries(meta.ranges).map(([key, range]) => (
            <ParamSlider
              key={key}
              label={meta.labels[key] || key}
              value={values[key] ?? range.default}
              min={range.min}
              max={range.max}
              step={range.step}
              defaultValue={range.default}
              onChange={(val) => handleParamChange(key, val)}
            />
          ))}
        </>
      )}
    </div>
  );
}
