const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const links = require('../docs/books/reader-links.js');
const root = path.join(__dirname, '../docs/books');
const courses = JSON.parse(fs.readFileSync(path.join(root, 'files.json'))).courses;
const one = '01-map-and-llm-basics', two = '02-rag-deep';
assert.equal(links.resolve('chapter-01.md', one, 'book.md', courses), '#chapter-01');
assert.equal(links.resolve('chapter-01.md#схема', one, 'book.md', courses), '#chapter-01--схема');
assert.equal(links.resolve('glossary.md', one, 'book.md', courses), '#glossary');
assert.equal(links.resolve('#практика', one, 'chapter-02.md', courses), '#chapter-02--практика');
assert.equal(links.resolve('../02-rag-deep/chapter-01.md', one, 'book.md', courses), 'reader.html?b=2&c=chapter-01#chapter-01');
assert.equal(links.resolve('https://example.org/file.md', one, 'book.md', courses), null);
assert.equal(links.resolve('javascript:alert(1)', one, 'book.md', courses), null);
assert.equal(links.resolve('missing.md', one, 'book.md', courses), null);
assert.equal(links.slug('Что проверить?'), 'что-проверить');
let count = 0;
for (const [course, entries] of Object.entries(courses)) {
    for (const entry of entries) {
        const file = typeof entry === 'string' ? entry : entry.file;
        // Fenced code blocks are not rendered as links; validate-book.py strips them the same way.
        const text = fs.readFileSync(path.join(root, course, file), 'utf8').replace(/^```[^\n]*\n[\s\S]*?^```[ \t]*$/gm, '');
        for (const match of text.matchAll(/\]\(([^)\s]+\.md(?:#[^)]*)?)\)/g)) {
            const href = match[1];
            if (/^(?:https?:|\/)/.test(href)) continue;
            assert.ok(links.resolve(href, course, file, courses), `${course}/${file}: unresolved ${href}`);
            count++;
        }
    }
}
console.log(`PASS: reader routes and ${count} Markdown links`);
