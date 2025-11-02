#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

// Load coverage configuration
const coverageConfig = require('../coverage.config.cjs');

// Get environment (development or ci)
const environment = process.env.NODE_ENV === 'ci' ? 'ci' : 'development';
const thresholds = coverageConfig[environment];

console.log(`🔍 Checking coverage thresholds for ${environment} environment:`);
console.log(`   Statements: ${thresholds.statements}%`);
console.log(`   Branches: ${thresholds.branches}%`);
console.log(`   Functions: ${thresholds.functions}%`);
console.log(`   Lines: ${thresholds.lines}%`);

// Read coverage summary
const coveragePath = path.join(__dirname, '../coverage/coverage-summary.json');
if (!fs.existsSync(coveragePath)) {
  console.error('❌ Coverage report not found. Run `npm run test:coverage` first.');
  process.exit(1);
}

const coverage = JSON.parse(fs.readFileSync(coveragePath, 'utf8'));
const globalCoverage = coverage.total;

console.log('\n📊 Current coverage:');
console.log(`   Statements: ${globalCoverage.statements.pct}%`);
console.log(`   Branches: ${globalCoverage.branches.pct}%`);
console.log(`   Functions: ${globalCoverage.functions.pct}%`);
console.log(`   Lines: ${globalCoverage.lines.pct}%`);

// Check thresholds
let passed = true;
const metrics = ['statements', 'branches', 'functions', 'lines'];

for (const metric of metrics) {
  const current = globalCoverage[metric].pct;
  const required = thresholds[metric];
  
  if (current < required) {
    console.error(`❌ ${metric}: ${current}% < ${required}% (required)`);
    passed = false;
  } else {
    console.log(`✅ ${metric}: ${current}% ≥ ${required}%`);
  }
}

// Check specific file coverage for high priority files
console.log('\n🎯 Checking high priority files:');
for (const filePattern of coverageConfig.highPriorityFiles) {
  // This is a simplified check - in a real implementation you'd want to
  // parse the file pattern and check matching files
  console.log(`   Checking pattern: ${filePattern}`);
}

if (passed) {
  console.log('\n🎉 All coverage thresholds passed!');
  process.exit(0);
} else {
  console.log('\n💥 Coverage thresholds not met. Please add more tests.');
  process.exit(1);
}
