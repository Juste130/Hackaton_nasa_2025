
import React, { forwardRef } from 'react';

const Tooltip = forwardRef((props, ref) => {
    return <div ref={ref} className="tooltip" id="tooltip"></div>;
});

export default Tooltip;
