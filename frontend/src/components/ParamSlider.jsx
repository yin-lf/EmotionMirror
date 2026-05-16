export default function ParamSlider({ label, value, min, max, step, defaultValue, onChange }) {
  const decimals = step < 1 ? Math.max(2, -Math.floor(Math.log10(step))) : 0;
  return (
    <div className="param-slider-row">
      <span className="param-slider-label">{label}</span>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="param-slider-input"
      />
      <span className="param-slider-value">{value.toFixed(decimals)}</span>
      <button
        type="button"
        className="param-slider-reset"
        onClick={() => onChange(defaultValue)}
        disabled={value === defaultValue}
        title="重置"
      >
        &#x21BA;
      </button>
    </div>
  );
}
