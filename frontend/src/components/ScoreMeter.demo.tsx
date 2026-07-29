// Demo file to demonstrate ScoreMeter component usage
import React from 'react';
import ScoreMeter from './ScoreMeter';

const ScoreMeterDemo: React.FC = () => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem', padding: '2rem' }}>
      <h2>ScoreMeter Component Demo</h2>
      
      <div>
        <h3>Reliable Content (Score: 85)</h3>
        <ScoreMeter 
          score={85} 
          label="Reliable" 
          confidence={0.92}
        />
      </div>

      <div>
        <h3>Mixed Reliability (Score: 55)</h3>
        <ScoreMeter 
          score={55} 
          label="Mixed" 
          confidence={0.67}
        />
      </div>

      <div>
        <h3>Unreliable Content (Score: 25)</h3>
        <ScoreMeter 
          score={25} 
          label="Unreliable" 
          confidence={0.81}
        />
      </div>

      <div>
        <h3>Low Confidence Result (Score: 50)</h3>
        <ScoreMeter 
          score={50} 
          label="Unknown" 
          confidence={0.25}
        />
      </div>

      <div>
        <h3>Without Confidence Display</h3>
        <ScoreMeter 
          score={75} 
          label="Mostly Reliable"
        />
      </div>
    </div>
  );
};

export default ScoreMeterDemo;