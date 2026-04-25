// Mock Prediction Logic for City Sentinel Traffic Forecast
const MOCK_DATA = {
    junctions: {
        1: { base: 2500, volatility: 500, name: "Central Square" },
        2: { base: 1800, volatility: 400, name: "Industrial East" },
        3: { base: 3200, volatility: 800, name: "Tech Corridor" },
        4: { base: 1200, volatility: 300, name: "Waterfront Drive" }
    }
};

function generateForecast(junctionId, considerHolidays, includeWeekends) {
    const junction = MOCK_DATA.junctions[junctionId] || MOCK_DATA.junctions[1];
    let baseFlow = junction.base;
    
    if (considerHolidays) baseFlow *= 1.25;
    if (includeWeekends) baseFlow *= 0.85;

    // Simulate 48 points (48 hours)
    const points = [];
    for (let i = 0; i < 48; i++) {
        const hour = i % 24;
        let flow = baseFlow;
        
        // Diurnal pattern (peak at 8am and 5pm)
        const peak1 = Math.exp(-Math.pow(hour - 8, 2) / 8) * 1.5;
        const peak2 = Math.exp(-Math.pow(hour - 17, 2) / 8) * 1.8;
        flow = flow * (0.5 + peak1 + peak2) + (Math.random() * junction.volatility);
        
        points.push(Math.round(flow));
    }
    return points;
}

function updateForecastUI() {
    const junctionSelect = document.querySelector('select');
    const holidayToggle = document.querySelector('input[type="checkbox"]'); // First toggle is holiday
    const weekendToggle = document.querySelectorAll('input[type="checkbox"]')[1];
    
    const junctionId = junctionSelect.selectedIndex + 1;
    const considerHolidays = holidayToggle.checked;
    const includeWeekends = weekendToggle.checked;

    const forecast = generateForecast(junctionId, considerHolidays, includeWeekends);
    const peak = Math.max(...forecast);
    const peakHour = forecast.indexOf(peak);

    // Update the "Projected Peak" card
    const peakValueDisplay = document.querySelector('.text-lg.font-headline.font-bold.text-white');
    if (peakValueDisplay) peakValueDisplay.textContent = `${peak.toLocaleString()} vph`;

    const peakTimeDisplay = document.querySelector('.text-\\[9px\\].text-secondary-container');
    if (peakTimeDisplay) peakTimeDisplay.textContent = `${peakHour}:00 Today`;

    // Update Severity
    const severityBadge = document.querySelector('.text-error.uppercase.tracking-widest');
    const severityText = document.querySelector('.text-xs.text-gray-400.mt-3');
    if (peak > 4500) {
        severityBadge.textContent = "Critical Alert";
        severityText.textContent = "Extreme congestion expected. All lanes reaching saturation.";
    } else if (peak > 3000) {
        severityBadge.textContent = "High Impact";
        severityText.textContent = "Significant delays expected during peak hours. Use alternate routes.";
    } else {
        severityBadge.textContent = "Optimal Flow";
        severityText.textContent = "Traffic is within normal operational parameters.";
    }

    // Note: Actually updating the SVG path is complex without a library, 
    // but we can at least update the numbers and status.
}

// Attach listeners
document.addEventListener('DOMContentLoaded', () => {
    const selects = document.querySelectorAll('select');
    const checkboxes = document.querySelectorAll('input[type="checkbox"]');

    selects.forEach(s => s.addEventListener('change', updateForecastUI));
    checkboxes.forEach(c => c.addEventListener('change', updateForecastUI));

    updateForecastUI(); // Initial run
});
