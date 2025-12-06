#!/usr/bin/env node

// Web3search Production Environment Test Script
// November 2025 - Comprehensive API Testing

const https = require('https');
const http = require('http');

// Configuration
const BACKEND_URL = 'https://web3search-api.marovole.workers.dev';
const FRONTEND_URL = 'https://web3search.pages.dev';
const TIMEOUT = 10000; // 10 seconds

// Test results
let results = {
    total: 0,
    passed: 0,
    failed: 0,
    details: []
};

// Utility functions
function log(message, type = 'info') {
    const timestamp = new Date().toISOString();
    const prefix = {
        'info': 'ℹ️',
        'pass': '✅',
        'fail': '❌',
        'warn': '⚠️'
    }[type] || 'ℹ️';
    console.log(`[${timestamp}] ${prefix} ${message}`);
}

function makeRequest(url, options = {}) {
    return new Promise((resolve, reject) => {
        const startTime = Date.now();
        const reqOptions = {
            ...options,
            timeout: TIMEOUT
        };

        const protocol = url.startsWith('https') ? https : http;
        const req = protocol.request(url, reqOptions, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
                const responseTime = Date.now() - startTime;
                resolve({
                    statusCode: res.statusCode,
                    headers: res.headers,
                    body: data,
                    responseTime
                });
            });
        });

        req.on('error', (err) => {
            reject(err);
        });

        req.on('timeout', () => {
            req.destroy();
            reject(new Error('Request timeout'));
        });

        if (options.body) {
            req.write(options.body);
        }
        req.end();
    });
}

async function testEndpoint(name, url, options = {}, expectedStatus = 200) {
    results.total++;
    try {
        const response = await makeRequest(url, options);
        
        if (response.statusCode === expectedStatus) {
            results.passed++;
            log(`${name} - PASSED (${response.responseTime}ms)`, 'pass');
            results.details.push({
                name,
                status: 'PASSED',
                responseTime: response.responseTime,
                statusCode: response.statusCode
            });
            return { success: true, response };
        } else {
            results.failed++;
            log(`${name} - FAILED (HTTP ${response.statusCode})`, 'fail');
            results.details.push({
                name,
                status: 'FAILED',
                responseTime: response.responseTime,
                statusCode: response.statusCode,
                error: `Expected ${expectedStatus}, got ${response.statusCode}`
            });
            return { success: false, response };
        }
    } catch (error) {
        results.failed++;
        log(`${name} - ERROR: ${error.message}`, 'fail');
        results.details.push({
            name,
            status: 'ERROR',
            error: error.message
        });
        return { success: false, error };
    }
}

// Main test function
async function runTests() {
    log('🚀 Starting Web3search Production Environment Tests', 'info');
    log('===============================================');

    // Backend API Tests
    log('\n📡 Backend API Tests', 'info');
    log('---------------------');

    // Health Check
    await testEndpoint('Health Check', `${BACKEND_URL}/api/v1/health`);

    // Search Autocomplete
    await testEndpoint('Search Autocomplete', `${BACKEND_URL}/api/v1/search/autocomplete?q=bitcoin`);

    // Quick Chat
    await testEndpoint('Quick Chat', `${BACKEND_URL}/api/v1/chat/quick-chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: 'What is Bitcoin?', stream: false })
    });

    // Deep Research (expects 202 Accepted for async task creation)
    await testEndpoint('Deep Research', `${BACKEND_URL}/api/v1/deep-research`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symbol: 'BTC', query: 'Research Bitcoin trends' })
    }, 202);

    // Frontend Tests
    log('\n🌐 Frontend Tests', 'info');
    log('------------------');

    // Frontend Home
    await testEndpoint('Frontend Home', FRONTEND_URL);

    // Frontend API Proxy
    await testEndpoint('Frontend API Proxy', `${FRONTEND_URL}/api/v1/health`);

    // Generate Report
    log('\n📊 Test Results Summary', 'info');
    log('========================');
    log(`Total Tests: ${results.total}`);
    log(`Passed: ${results.passed}`, 'pass');
    log(`Failed: ${results.failed}`, 'fail');
    
    const successRate = results.total > 0 ? (results.passed / results.total * 100).toFixed(1) : 0;
    log(`Success Rate: ${successRate}%`);

    // Performance Summary
    const passedTests = results.details.filter(t => t.status === 'PASSED' && t.responseTime);
    if (passedTests.length > 0) {
        const avgResponseTime = passedTests.reduce((sum, t) => sum + t.responseTime, 0) / passedTests.length;
        log(`Average Response Time: ${Math.round(avgResponseTime)}ms`);
    }

    // Detailed Results
    log('\n📋 Detailed Results', 'info');
    log('==================');
    results.details.forEach(test => {
        const status = test.status === 'PASSED' ? '✅' : '❌';
        const time = test.responseTime ? ` (${test.responseTime}ms)` : '';
        const error = test.error ? ` - ${test.error}` : '';
        console.log(`${status} ${test.name}${time}${error}`);
    });

    // Assessment
    log('\n🎯 System Assessment', 'info');
    log('=====================');
    
    if (successRate >= 90) {
        log('🎉 EXCELLENT: System is performing exceptionally well', 'pass');
    } else if (successRate >= 75) {
        log('✅ GOOD: System is functioning well with minor issues', 'pass');
    } else if (successRate >= 50) {
        log('⚠️  FAIR: System has some issues that need attention', 'warn');
    } else {
        log('❌ POOR: System has significant issues requiring immediate attention', 'fail');
    }

    // Exit with appropriate code
    process.exit(results.failed > 0 ? 1 : 0);
}

// Run the tests
runTests().catch(error => {
    console.error('Test execution failed:', error);
    process.exit(1);
});
