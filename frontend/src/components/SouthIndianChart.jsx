import React from 'react';

/**
 * South Indian Chart Component
 * 
 * The South Indian chart has a fixed 4x4 grid layout where each sign 
 * has a fixed position. The houses rotate based on the Ascendant.
 * 
 * Fixed Sign Positions in South Indian Style:
 * 
 *  Pisces  | Aries   | Taurus  | Gemini
 *  --------|---------|---------|--------
 *  Aquarius|         |         | Cancer
 *  --------|  CENTER |  CENTER |--------
 *  Capricorn|        |         | Leo
 *  --------|---------|---------|--------
 *  Sagittarius|Scorpio|Libra   | Virgo
 */

// Fixed positions for each sign in the 4x4 grid (row, col)
const SIGN_POSITIONS = {
  "Pisces": { row: 0, col: 0 },
  "Aries": { row: 0, col: 1 },
  "Taurus": { row: 0, col: 2 },
  "Gemini": { row: 0, col: 3 },
  "Aquarius": { row: 1, col: 0 },
  "Cancer": { row: 1, col: 3 },
  "Capricorn": { row: 2, col: 0 },
  "Leo": { row: 2, col: 3 },
  "Sagittarius": { row: 3, col: 0 },
  "Scorpio": { row: 3, col: 1 },
  "Libra": { row: 3, col: 2 },
  "Virgo": { row: 3, col: 3 },
};

// Sign abbreviations
const SIGN_ABBREV = {
  "Aries": "Ari", "Taurus": "Tau", "Gemini": "Gem", "Cancer": "Can",
  "Leo": "Leo", "Virgo": "Vir", "Libra": "Lib", "Scorpio": "Sco",
  "Sagittarius": "Sag", "Capricorn": "Cap", "Aquarius": "Aqu", "Pisces": "Pis"
};

// Sign order
const SIGN_ORDER = [
  "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
  "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
];

const SouthIndianChart = ({ chartData, birthInfo }) => {
  if (!chartData || !chartData.ascendant) {
    return (
      <div className="text-center text-cosmic-text-muted p-8">
        Chart data not available
      </div>
    );
  }

  const ascendantSign = chartData.ascendant.sign || "Aries";
  const ascendantIndex = SIGN_ORDER.indexOf(ascendantSign);
  
  // Build house to sign mapping based on ascendant
  const houseToSign = {};
  const signToHouse = {};
  for (let i = 0; i < 12; i++) {
    const signIndex = (ascendantIndex + i) % 12;
    const sign = SIGN_ORDER[signIndex];
    const house = i + 1;
    houseToSign[house] = sign;
    signToHouse[sign] = house;
  }

  // Get planets in each sign
  const planetsInSign = {};
  SIGN_ORDER.forEach(sign => { planetsInSign[sign] = []; });
  
  if (chartData.planets) {
    chartData.planets.forEach(planet => {
      const sign = planet.sign;
      if (sign && planetsInSign[sign]) {
        planetsInSign[sign].push({
          abbrev: planet.abbrev || planet.name?.substring(0, 2),
          name: planet.name,
          retrograde: planet.retrograde,
          isAscendant: planet.name === "Ascendant"
        });
      }
    });
  }

  // Add Ascendant marker to its sign
  if (ascendantSign && planetsInSign[ascendantSign]) {
    // Check if Ascendant is not already added
    const hasAsc = planetsInSign[ascendantSign].some(p => p.name === "Ascendant");
    if (!hasAsc) {
      planetsInSign[ascendantSign].unshift({
        abbrev: "As",
        name: "Ascendant",
        isAscendant: true
      });
    }
  }

  // Render a single cell
  const renderCell = (sign) => {
    const position = SIGN_POSITIONS[sign];
    const house = signToHouse[sign];
    const planets = planetsInSign[sign] || [];
    const isAscendantHouse = house === 1;

    return (
      <div
        key={sign}
        className={`chart-cell relative ${isAscendantHouse ? 'ring-1 ring-cosmic-brand-accent/50' : ''}`}
        style={{
          gridRow: position.row + 1,
          gridColumn: position.col + 1,
        }}
        data-testid={`chart-cell-${sign.toLowerCase()}`}
      >
        {/* Sign abbreviation */}
        <span className="chart-sign font-mono">
          {SIGN_ABBREV[sign]}
        </span>
        
        {/* House number */}
        <span className="absolute top-1 right-1.5 text-[10px] text-cosmic-text-muted font-mono">
          {house}
        </span>
        
        {/* Planets */}
        <div className="chart-planets flex flex-wrap justify-center gap-1 mt-3">
          {planets.map((planet, idx) => (
            <span
              key={idx}
              className={`${planet.isAscendant ? 'chart-lagna font-bold' : ''} ${planet.retrograde ? 'text-red-400' : ''}`}
              title={`${planet.name}${planet.retrograde ? ' (R)' : ''}`}
            >
              {planet.abbrev}{planet.retrograde ? 'ᴿ' : ''}
            </span>
          ))}
        </div>
      </div>
    );
  };

  // Render center info
  const renderCenter = () => (
    <div
      className="chart-cell center flex flex-col items-center justify-center text-center"
      style={{
        gridRow: '2 / 4',
        gridColumn: '2 / 4',
      }}
      data-testid="chart-center"
    >
      <p className="font-cinzel text-cosmic-brand-accent text-sm md:text-base font-semibold mb-1">
        {birthInfo?.name || 'Birth Chart'}
      </p>
      <p className="text-cosmic-text-secondary text-xs mb-2">
        <span className="font-cinzel">Rasi:</span> {chartData.nakshatra?.moon_sign || 'N/A'}
      </p>
      <p className="text-cosmic-text-muted text-xs">
        <span className="font-cinzel">Lagna:</span> {ascendantSign}
      </p>
      {chartData.nakshatra?.nakshatra && (
        <p className="text-cosmic-text-muted text-[10px] mt-1">
          {chartData.nakshatra.nakshatra} - Pada {chartData.nakshatra.pada || 1}
        </p>
      )}
    </div>
  );

  return (
    <div className="south-indian-chart mx-auto" data-testid="south-indian-chart">
      {/* Top row */}
      {renderCell("Pisces")}
      {renderCell("Aries")}
      {renderCell("Taurus")}
      {renderCell("Gemini")}
      
      {/* Middle rows - left and right columns + center */}
      {renderCell("Aquarius")}
      {renderCenter()}
      {renderCell("Cancer")}
      
      {renderCell("Capricorn")}
      {renderCell("Leo")}
      
      {/* Bottom row */}
      {renderCell("Sagittarius")}
      {renderCell("Scorpio")}
      {renderCell("Libra")}
      {renderCell("Virgo")}
    </div>
  );
};

export default SouthIndianChart;
