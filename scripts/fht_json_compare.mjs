// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. https://mozilla.org/MPL/2.0/.
// Preserve unbounded integer tokens before JSON.parse's Number rounding occurs.
export function parseExactJson(text) {
  return JSON.parse(text, (key, value, context) => {
    if (typeof value !== 'number') return value;
    if (!context || typeof context.source !== 'string') {
      throw Error('lossless integer parsing requires JSON reviver source support');
    }
    return /^-?(?:0|[1-9][0-9]*)$/.test(context.source) ? BigInt(context.source) : value;
  });
}

export function exactStringify(value) {
  return JSON.stringify(value, (key, item) => typeof item === 'bigint'
    ? { '$fht-integer': item.toString() } : item);
}
