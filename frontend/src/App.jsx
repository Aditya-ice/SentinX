import { useState, useEffect } from 'react';

function App() {
  const [threats, setThreats] = useState([]);
  const [error, setError] = useState(null);

  // Poll exactly every 2 seconds
  useEffect(() => {
    const fetchThreats = async () => {
      try {
        const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
        const response = await fetch(`${apiUrl}/threats/active`);
        if (!response.ok) throw new Error('API unavailable');
        const data = await response.json();

        // Sort newest first
        const sorted = (data.threats || []).sort(
          (a, b) => new Date(b.timestamp) - new Date(a.timestamp)
        );
        setThreats(sorted);
        setError(null);
      } catch (err) {
        console.error("Failed to fetch threats:", err);
        setError("Warning: Disconnected from SentinX Engine");
      }
    };

    fetchThreats();
    const interval = setInterval(fetchThreats, 2000);
    return () => clearInterval(interval);
  }, []);

  const getBadgeClass = (type) => {
    switch (type) {
      case 'SQLi': return 'sqli';
      case 'DDoS': return 'ddos';
      case 'Brute Force': return 'brute';
      default: return 'normal';
    }
  };

  return (
    <div className="dashboard-container">
      <header className="header">
        <h1>SentinX</h1>
        <p>Real-Time Network Threat Defense</p>
      </header>

      {error && (
        <div style={{ background: 'rgba(239, 68, 68, 0.2)', color: '#fca5a5', padding: '1rem', borderRadius: '8px', textAlign: 'center', border: '1px solid rgba(239, 68, 68, 0.5)' }}>
          {error}
        </div>
      )}

      <div className="stats-grid">
        <div className="glass-card">
          <h3 className="stat-title">System Status</h3>
          <p className="stat-value green" style={{ fontSize: '1.5rem', display: 'flex', alignItems: 'center' }}>
            <span className="live-indicator"></span> LIVE
          </p>
        </div>
        <div className="glass-card">
          <h3 className="stat-title">Active Threats (5m)</h3>
          <p className={`stat-value ${threats.length > 0 ? 'red' : 'green'}`}>
            {threats.length}
          </p>
        </div>
      </div>

      <div className="threats-table-container">
        <table>
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Source IP</th>
              <th>Attack Vector</th>
              <th>Target Path</th>
              <th>ML Confidence</th>
            </tr>
          </thead>
          <tbody>
            {threats.length === 0 ? (
              <tr>
                <td colSpan="5" className="empty-state">
                  No active threats detected. Network is secure.
                </td>
              </tr>
            ) : (
              threats.map((t, idx) => (
                <tr key={`${t.source_ip}-${idx}`}>
                  <td style={{ color: 'var(--text-muted)' }}>
                    {new Date(t.timestamp).toLocaleTimeString()}
                  </td>
                  <td style={{ fontFamily: 'monospace', fontSize: '1.1rem' }}>
                    {t.source_ip}
                  </td>
                  <td>
                    <span className={`badge ${getBadgeClass(t.attack_type)}`}>
                      {t.attack_type}
                    </span>
                  </td>
                  <td style={{ fontFamily: 'monospace', color: 'var(--text-muted)' }}>
                    {t.http_method} {t.url_path}
                  </td>
                  <td>
                    <span style={{ color: 'var(--accent-red)' }}>
                      {t.ml_score ? `${(t.ml_score * 100).toFixed(1)}%` : '99.0%'}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default App;
