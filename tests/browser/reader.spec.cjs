const { test, expect } = require('@playwright/test');
const manifest = require('../../docs/books/files.json').courses;
for (const [course, entries] of Object.entries(manifest)) {
    const day = Number(course.slice(0, 2));
    test(`day ${day}: offline rendering, diagrams, and links`, async ({ page }) => {
        const errors = [];
        page.on('pageerror', error => errors.push(error.message));
        // All assets must be bundled: simulate a reader with no Internet access.
        await page.route('**/*', route => new URL(route.request().url()).hostname === '127.0.0.1' ? route.continue() : route.abort());
        await page.goto(`/reader.html?b=${day}&c=book`);
        await expect(page.locator('#loadingMsg')).toBeHidden();
        await expect(page.locator('.book-section')).toHaveCount(entries.length);
        await expect(page.locator('.error-msg')).toHaveCount(0);
        const diagrams = page.locator('.mermaid');
        expect(await diagrams.count()).toBeGreaterThanOrEqual(2);
        for (const diagram of await diagrams.all()) {
            await expect(diagram.locator('svg')).toHaveCount(1);
            await expect(diagram).not.toContainText('Syntax error');
        }
        expect(errors).toEqual([]);
        await expect(page.locator('.book-section a[href$=".md"]')).toHaveCount(0);
        const link = page.locator('#book a[href="#chapter-01"]').first();
        await link.click();
        await expect(page).toHaveURL(/#chapter-01$/);
        await expect(page.locator('#chapter-01')).toBeVisible();
        await page.locator('#chapter-02 pre button').first().click();
        await expect(page.locator('#chapter-02 pre button').first()).toHaveClass(/copied|failed/);
    });
}
test('markdown sanitization strips executable HTML', async ({ page }) => {
    await page.route('**/01-map-and-llm-basics/book.md*', route => route.fulfill({
        contentType: 'text/plain', body: '# Test\n<img src=x onerror="window.leaked=true">\n<script>window.leaked=true</script>\n[bad](javascript:alert(1))',
    }));
    await page.goto('/reader.html?b=1&c=book');
    await expect(page.locator('#loadingMsg')).toBeHidden();
    expect(await page.evaluate(() => window.leaked)).toBeUndefined();
    await expect(page.locator('#book [onerror], #book script, #book a[href^="javascript:"]')).toHaveCount(0);
});
