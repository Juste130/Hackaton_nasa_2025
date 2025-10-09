
import React from 'react';

function Legend({ nodeColors }) {
    return (
        <div className="legend">
            <h4 style={{ margin: '0 0 0.5rem 0' }}>Node Types</h4>
            {Object.entries(nodeColors).map(([type, color]) => (
                <div className="legend-item" key={type}>
                    <div className="legend-color" style={{ backgroundColor: color }}></div>
                    <span>{type}</span>
                </div>
            ))}
        </div>
    );
}

export default Legend;

