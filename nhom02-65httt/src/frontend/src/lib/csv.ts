/*
 * CSV export helper.
 * SPEC §10 requires guarding against CSV formula injection, so any cell that
 * starts with = + - @ or a control character is prefixed with an apostrophe
 * before quoting.
 */

const FORMULA_PREFIX = /^[=+\-@\t\r]/;

export function parseCsv(text: string): string[][] {
  const source = text.replace(/^\uFEFF/, '');
  const rows: string[][] = [];
  let row: string[] = [];
  let cell = '';
  let inQuotes = false;
  let closedQuote = false;

  function finishRow() {
    row.push(cell);
    if (row.some((value) => value.trim() !== '')) rows.push(row);
    row = [];
    cell = '';
    closedQuote = false;
  }

  for (let index = 0; index < source.length; index += 1) {
    const char = source[index]!;
    if (inQuotes) {
      if (char === '"' && source[index + 1] === '"') {
        cell += '"';
        index += 1;
      } else if (char === '"') {
        inQuotes = false;
        closedQuote = true;
      } else {
        cell += char;
      }
      continue;
    }

    if (closedQuote) {
      if (char === ',') {
        row.push(cell);
        cell = '';
        closedQuote = false;
      } else if (char === '\n' || char === '\r') {
        if (char === '\r' && source[index + 1] === '\n') index += 1;
        finishRow();
      } else if (!/\s/.test(char)) {
        throw new Error('CSV không hợp lệ: có dữ liệu nằm sau dấu ngoặc kép đóng.');
      }
      continue;
    }

    if (char === ',') {
      row.push(cell);
      cell = '';
    } else if (char === '\n' || char === '\r') {
      if (char === '\r' && source[index + 1] === '\n') index += 1;
      finishRow();
    } else if (char === '"') {
      if (cell.length !== 0) {
        throw new Error('CSV không hợp lệ: dấu ngoặc kép phải bắt đầu ở đầu ô.');
      }
      inQuotes = true;
    } else {
      cell += char;
    }
  }

  if (inQuotes) throw new Error('CSV không hợp lệ: thiếu dấu ngoặc kép đóng.');
  if (cell.length > 0 || row.length > 0 || closedQuote) finishRow();
  return rows;
}

function toCell(value: string | number | null | undefined): string {
  const text = value === null || value === undefined ? '' : String(value);
  const guarded = FORMULA_PREFIX.test(text) ? `'${text}` : text;
  return `"${guarded.replace(/"/g, '""')}"`;
}

export function downloadCsv(
  filename: string,
  headers: string[],
  rows: (string | number | null | undefined)[][],
): void {
  const content = [headers, ...rows]
    .map((row) => row.map(toCell).join(','))
    .join('\r\n');
  // BOM so Excel opens Vietnamese text in the right encoding.
  const blob = new Blob(['\uFEFF', content], {
    type: 'text/csv;charset=utf-8;',
  });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.rel = 'noopener';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
