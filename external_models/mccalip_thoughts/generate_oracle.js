/**
 * generate_oracle.js
 *
 * Generates expected_outputs.json by driving CostModel (McCalip math.js) over
 * a parameter grid. Run once at the pinned commit; freeze the output.
 *
 * Usage (from this directory):
 *   node generate_oracle.js > expected_outputs.json
 *
 * Pinned commit: d1e4238d3d3f4924e5ca65bafbd4ba5b39af2eb8
 * Repository:    https://github.com/andrewmccalip/thoughts
 */

'use strict';

const CostModel = require('./math.js');

function runCase(label, overrides) {
    CostModel.setState({
        years: 5,
        targetGW: 1,
        solarAbsorptivity: 0.92,
        emissivityPV: 0.85,
        emissivityRad: 0.90,
        pvEfficiency: 0.22,
        betaAngle: 90,
        orbitalAltitudeKm: 550,
        maxDieTempC: 85,
        tempDropC: 10,
        launchCostPerKg: 500,
        satelliteCostPerW: 22,
        specificPowerWPerKg: 36.5,
        satellitePowerKW: 27,
        sunFraction: 0.98,
        cellDegradation: 2.5,
        gpuFailureRate: 9,
        nreCost: 1000,
        gasTurbineCapexPerKW: 1800,
        electricalCostPerW: 5.25,
        mechanicalCostPerW: 3.0,
        civilCostPerW: 2.5,
        networkCostPerW: 1.75,
        pue: 1.2,
        gasPricePerMMBtu: 4.30,
        heatRateBtuKwh: 6200,
        capacityFactor: 0.85,
    });

    if (overrides) CostModel.setState(overrides);

    const orbital = CostModel.calculateOrbital();
    const thermal = CostModel.calculateThermal();
    const breakeven = CostModel.calculateBreakeven();

    return {
        label,
        state_overrides: overrides || {},
        geometry: {
            vfNadirMax: thermal.vfNadirMax,
            earthAngularRadiusDeg: thermal.earthAngularRadiusDeg,
            vfSideA: thermal.vfSideA,
            vfSideB: thermal.vfSideB,
            vfTotal: thermal.vfTotal,
        },
        thermal: {
            eqTempK: thermal.eqTempK,
            eqTempC: thermal.eqTempC,
            totalHeatInW: thermal.totalHeatInW,
            qSolarW: thermal.qSolarW,
            qEarthIRW: thermal.qEarthIRW,
            qAlbedoW: thermal.qAlbedoW,
            qHeatLoopW: thermal.qHeatLoopW,
            radiativeCapacityW: thermal.radiativeCapacityW,
            areaSufficient: thermal.areaSufficient,
            tempMarginC: thermal.tempMarginC,
            areaRequiredM2: thermal.areaRequiredM2,
            availableAreaM2: thermal.availableAreaM2,
        },
        orbital: {
            satelliteCount: orbital.satelliteCount,
            totalMassKg: orbital.totalMassKg,
            starshipLaunches: orbital.starshipLaunches,
            totalCost: orbital.totalCost,
            costPerW: orbital.costPerW,
            lcoe: orbital.lcoe,
            energyMWh: orbital.energyMWh,
            avgCapacityFactor: orbital.avgCapacityFactor,
            arrayAreaKm2: orbital.arrayAreaKm2,
        },
        breakeven_launch_cost_per_kg: breakeven,
    };
}

const cases = [];

cases.push(runCase('defaults', {}));

for (const beta of [0, 30, 60, 90]) {
    cases.push(runCase('beta_' + beta, { betaAngle: beta }));
}

for (const alt of [400, 550, 800]) {
    cases.push(runCase('alt_' + alt + 'km', { orbitalAltitudeKm: alt }));
}

for (const eRad of [0.85, 0.90, 0.95]) {
    cases.push(runCase('eRad_' + eRad, { emissivityRad: eRad }));
}

const output = {
    _meta: {
        generated_by: 'generate_oracle.js',
        source_repo: 'https://github.com/andrewmccalip/thoughts',
        pinned_commit: 'd1e4238d3d3f4924e5ca65bafbd4ba5b39af2eb8',
        commit_date: '2025-12-29T17:42:13Z',
        generated_on: '2026-06-12',
        source_file: 'static/js/math.js',
        node_version: process.version,
        conventions: {
            sigma_sb: '5.67e-8  (McCalip truncated; CODATA exact: 5.670374419e-8)',
            T_space_K: '3 K  (McCalip rounded; CMB: 2.7255 K)',
            replication_tolerance_K: 0.05,
        },
    },
    cases,
};

process.stdout.write(JSON.stringify(output, null, 2) + '\n');
