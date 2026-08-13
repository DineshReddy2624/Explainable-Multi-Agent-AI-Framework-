import React, { useState } from 'react';

const CorrectedDataGrid = ({ originalRecords = [], correctedRecords = [], headers = [], appliedLogs = [] }) => {
  const [showOnlyChanged, setShowOnlyChanged] = useState(false);

  if (!correctedRecords || correctedRecords.length === 0) return null;

  // Build lookup map for modified cells: "row-col" -> log entry
  const logMap = new Map();
  appliedLogs.forEach(log => {
    logMap.set(`${log.row_index}-${log.column_name}`, log);
  });

  // Calculate changed row indices dynamically
  const changedRowIndices = new Set();

  correctedRecords.forEach((row, rIdx) => {
    const origRow = originalRecords[rIdx] || {};
    headers.forEach(cName => {
      const origVal = origRow[cName];
      const corrVal = row[cName];
      const hasLog = logMap.has(`${rIdx}-${cName}`);
      const isNullOrig = origVal === undefined || origVal === null || String(origVal).trim() === '' || String(origVal).toLowerCase() === 'nan';
      const isFilledCorr = corrVal !== undefined && corrVal !== null && String(corrVal).trim() !== '' && String(corrVal).toLowerCase() !== 'nan';

      if (hasLog || (isNullOrig && isFilledCorr) || String(origVal) !== String(corrVal)) {
        changedRowIndices.add(rIdx);
      }
    });
  });

  const displayRows = showOnlyChanged
    ? correctedRecords.filter((_, idx) => changedRowIndices.has(idx))
    : correctedRecords;

  return (
    <div className="card space-y-4" style={{ marginTop: '2rem', border: '2px solid var(--success)', background: 'rgba(16, 185, 129, 0.03)' }}>
      {/* Header & Controls */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ fontSize: '1.25rem' }}>✨</span>
            <h3 style={{ fontSize: '1.35rem', fontWeight: '700', color: 'var(--success)' }}>Corrected Dataset Preview</h3>
            <span style={{ background: 'rgba(16, 185, 129, 0.2)', color: 'var(--success)', fontSize: '0.75rem', padding: '0.2rem 0.6rem', borderRadius: '12px', fontWeight: '600' }}>
              Post-Remediation Active
            </span>
          </div>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', marginTop: '0.25rem' }}>
            Displaying post-correction output dataset with visual diff highlights and confidence tooltips.
          </p>
        </div>

        {/* Difference View Toggle Buttons */}
        <div style={{ display: 'flex', gap: '0.5rem', background: 'var(--bg-dark)', padding: '0.25rem', borderRadius: 'var(--radius)', border: '1px solid var(--border)' }}>
          <button
            type="button"
            onClick={() => setShowOnlyChanged(false)}
            style={{
              padding: '0.4rem 0.8rem',
              borderRadius: '6px',
              fontSize: '0.875rem',
              fontWeight: '600',
              border: 'none',
              cursor: 'pointer',
              background: !showOnlyChanged ? 'var(--primary)' : 'transparent',
              color: !showOnlyChanged ? '#fff' : 'var(--text-muted)'
            }}
          >
            Show All Rows ({correctedRecords.length})
          </button>
          <button
            type="button"
            onClick={() => setShowOnlyChanged(true)}
            style={{
              padding: '0.4rem 0.8rem',
              borderRadius: '6px',
              fontSize: '0.875rem',
              fontWeight: '600',
              border: 'none',
              cursor: 'pointer',
              background: showOnlyChanged ? 'var(--success)' : 'transparent',
              color: showOnlyChanged ? '#fff' : 'var(--text-muted)'
            }}
          >
            Show Only Changed Rows ({changedRowIndices.size})
          </button>
        </div>
      </div>

      {/* Color Legend Bar */}
      <div style={{ display: 'flex', gap: '1.5rem', fontSize: '0.75rem', background: 'var(--bg-dark)', padding: '0.6rem 1rem', borderRadius: '8px', border: '1px solid var(--border)' }}>
        <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <span style={{ width: '14px', height: '14px', background: 'rgba(16, 185, 129, 0.3)', border: '1px solid var(--success)', borderRadius: '3px' }}></span>
          <strong>Green:</strong> AI Auto-Corrected
        </span>
        <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <span style={{ width: '14px', height: '14px', background: 'rgba(245, 158, 11, 0.3)', border: '1px solid var(--warning)', borderRadius: '3px' }}></span>
          <strong>Yellow:</strong> User Manual Edit
        </span>
        <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <span style={{ width: '14px', height: '14px', background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: '3px' }}></span>
          <strong>Gray:</strong> Unchanged
        </span>
      </div>

      {/* Corrected Grid Table */}
      <div className="table-container" style={{ maxHeight: '450px', overflowY: 'auto' }}>
        <table>
          <thead style={{ position: 'sticky', top: 0, zIndex: 10, background: 'var(--bg-card)' }}>
            <tr>
              <th style={{ width: '50px' }}>#</th>
              {headers.map(h => <th key={h}>{h}</th>)}
            </tr>
          </thead>
          <tbody>
            {displayRows.map((row, idx) => {
              const rIdx = correctedRecords.indexOf(row);
              const origRow = originalRecords[rIdx] || {};

              return (
                <tr key={rIdx}>
                  <td style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>{rIdx + 1}</td>
                  {headers.map(cName => {
                    const origVal = origRow[cName];
                    const corrVal = row[cName];
                    const logEntry = logMap.get(`${rIdx}-${cName}`);
                    
                    const isNullOrig = origVal === undefined || origVal === null || String(origVal).trim() === '' || String(origVal).toLowerCase() === 'nan';
                    const isFilledCorr = corrVal !== undefined && corrVal !== null && String(corrVal).trim() !== '' && String(corrVal).toLowerCase() !== 'nan';
                    const isChanged = logEntry || (isNullOrig && isFilledCorr) || String(origVal) !== String(corrVal);
                    const isUserEdit = logEntry?.applied_by === "User";

                    let style = {};
                    let badge = null;
                    let tooltip = "";

                    if (isChanged) {
                      if (isUserEdit) {
                        style.backgroundColor = 'rgba(245, 158, 11, 0.25)';
                        style.border = '1px solid var(--warning)';
                        badge = <span style={{ fontSize: '0.65rem', background: 'var(--warning)', color: '#000', padding: '0.1rem 0.3rem', borderRadius: '4px', marginLeft: '0.4rem', fontWeight: 'bold' }}>✓ User Edit</span>;
                      } else {
                        style.backgroundColor = 'rgba(16, 185, 129, 0.25)';
                        style.border = '1px solid var(--success)';
                        badge = <span style={{ fontSize: '0.65rem', background: 'var(--success)', color: '#fff', padding: '0.1rem 0.3rem', borderRadius: '4px', marginLeft: '0.4rem', fontWeight: 'bold' }}>✓ Corrected</span>;
                      }

                      tooltip = `Original: ${origVal !== undefined && origVal !== null && String(origVal).trim() !== '' ? String(origVal) : '[NULL]'} ➔ Corrected: ${corrVal} | Method: ${logEntry?.correction_type || 'Median Imputation'} | Confidence: ${logEntry?.confidence_score ? (logEntry.confidence_score * 100).toFixed(0) + '%' : '95%'}`;
                    }

                    return (
                      <td key={cName} style={style} title={tooltip}>
                        <span>{corrVal !== undefined && corrVal !== null ? String(corrVal) : ''}</span>
                        {badge}
                      </td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default CorrectedDataGrid;
