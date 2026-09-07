const { defineConfig } = require('@playwright/test');
module.exports = defineConfig({
    testDir: './tests/browser',
    timeout: 60000,
    workers: 1,
    use: {
        baseURL: 'http://127.0.0.1:18761',
        launchOptions: process.env.CHROME_PATH ? { executablePath: process.env.CHROME_PATH } : {},
    },
    webServer: {
        command: 'python3 -m http.server 18761 --bind 127.0.0.1 --directory docs/books',
        url: 'http://127.0.0.1:18761',
        reuseExistingServer: false,
    },
});
