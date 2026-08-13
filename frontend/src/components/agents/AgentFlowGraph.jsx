import React, { useMemo } from 'react';
import ReactFlow, { Background, Controls } from 'reactflow';
import 'reactflow/dist/style.css';

const AgentFlowGraph = () => {
  const nodes = useMemo(() => [
    {
      id: 'coord',
      data: { label: '👑 Coordinator Agent' },
      position: { x: 350, y: 20 },
      style: { background: '#6366F1', color: '#fff', fontWeight: 'bold', padding: '12px', borderRadius: '8px', border: '2px solid #818CF8' },
    },
    { id: '1', data: { label: '1. Profiling Agent' }, position: { x: 50, y: 150 } },
    { id: '2', data: { label: '2. Missing Value Agent' }, position: { x: 250, y: 150 } },
    { id: '3', data: { label: '3. Duplicate Agent' }, position: { x: 450, y: 150 } },
    { id: '4', data: { label: '4. Format Agent' }, position: { x: 650, y: 150 } },
    
    { id: '5', data: { label: '5. Quality Score Agent' }, position: { x: 50, y: 260 } },
    { id: '6', data: { label: '6. Isolation Forest Agent' }, position: { x: 250, y: 260 }, style: { background: '#EF4444', color: '#fff' } },
    { id: '7', data: { label: '7. SHAP Explainability Agent' }, position: { x: 450, y: 260 }, style: { background: '#06B6D4', color: '#fff' } },
    { id: '8', data: { label: '8. Auto-Correction Agent' }, position: { x: 650, y: 260 }, style: { background: '#10B981', color: '#fff' } },

    { id: '9', data: { label: '9. Rule Engine Agent' }, position: { x: 150, y: 370 } },
    { id: '10', data: { label: '10. Monitoring Agent' }, position: { x: 350, y: 370 } },
    { id: '11', data: { label: '11. FAISS Chat Agent' }, position: { x: 550, y: 370 } },
  ], []);

  const edges = useMemo(() => [
    { id: 'e-coord-1', source: 'coord', target: '1', animated: true },
    { id: 'e-coord-2', source: 'coord', target: '2', animated: true },
    { id: 'e-coord-3', source: 'coord', target: '3', animated: true },
    { id: 'e-coord-4', source: 'coord', target: '4', animated: true },
    { id: 'e-coord-5', source: 'coord', target: '5', animated: true },
    { id: 'e-coord-6', source: 'coord', target: '6', animated: true },
    { id: 'e-coord-7', source: 'coord', target: '7', animated: true },
    { id: 'e-coord-8', source: 'coord', target: '8', animated: true },
    { id: 'e-coord-9', source: 'coord', target: '9', animated: true },
    { id: 'e-coord-10', source: 'coord', target: '10', animated: true },
    { id: 'e-coord-11', source: 'coord', target: '11', animated: true },
  ], []);

  return (
    <div className="card" style={{ height: '480px', width: '100%', position: 'relative' }}>
      <h3 className="text-lg font-bold mb-2">Multi-Agent AI Architecture Workflow</h3>
      <ReactFlow nodes={nodes} edges={edges} fitView>
        <Background color="#374151" gap={16} />
        <Controls />
      </ReactFlow>
    </div>
  );
};

export default AgentFlowGraph;
