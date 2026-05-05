import { Check } from 'lucide-react';

export default function Sidebar({ steps, current, completed, onChange }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-label">工作流程</div>
      <div className="sidebar-steps">
        {steps.map((step, i) => (
          <div key={step.key}>
            <div
              className={`sidebar-step ${i === current ? 'active' : ''} ${completed.includes(i) ? 'completed' : ''}`}
              onClick={() => onChange(i)}
            >
              <div className="sidebar-step-indicator">
                {completed.includes(i) ? <Check size={14} /> : i + 1}
              </div>
              <div className="sidebar-step-content">
                <div className="sidebar-step-title">{step.title}</div>
                <div className="sidebar-step-desc">{step.desc}</div>
              </div>
            </div>
            {i < steps.length - 1 && (
              <div className={`sidebar-step-connector ${completed.includes(i) ? 'completed' : ''}`} />
            )}
          </div>
        ))}
      </div>
    </aside>
  );
}
