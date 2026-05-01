import type { StatusData } from "../types";

interface Props {
  status: StatusData | null;
}

export default function DashboardPanel({ status }: Props) {
  if (!status) {
    return (
      <div className="dashboard-panel">
        <h3>Dashboard</h3>
        <p className="muted">Waiting for status...</p>
      </div>
    );
  }

  const { budget } = status;
  const usedPct = budget.total > 0 ? (budget.used / budget.total) * 100 : 0;
  const availPct = 100 - usedPct;

  return (
    <div className="dashboard-panel">
      <h3>Dashboard</h3>

      <div className="dash-section">
        <div className="dash-label">Token Budget</div>
        <div className="budget-bar">
          <div
            className="budget-fill"
            style={{ width: `${usedPct}%` }}
            title={`Used: ${budget.used.toLocaleString()}`}
          />
        </div>
        <div className="budget-nums">
          <span>{budget.used.toLocaleString()} used</span>
          <span>{budget.available.toLocaleString()} available</span>
          <span className="muted">{budget.total.toLocaleString()} total</span>
        </div>
        {budget.action !== "ok" && (
          <div className={`budget-action budget-${budget.action}`}>
            {budget.action.toUpperCase()}
          </div>
        )}
      </div>

      <div className="dash-section dash-numbers">
        <span>Used: {usedPct.toFixed(1)}%</span>
        <span>Available: {availPct.toFixed(1)}%</span>
      </div>
    </div>
  );
}
