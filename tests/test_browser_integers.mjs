// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. https://mozilla.org/MPL/2.0/.
import assert from 'node:assert/strict';
import test from 'node:test';
import { parseExactJson, exactStringify } from '../scripts/fht_json_compare.mjs';

test('unbounded canonical integer and both adjacent changes remain distinct', () => {
  const expected = parseExactJson('{"count":9007199254740993}');
  assert.equal(expected.count, 9007199254740993n);
  assert.equal(exactStringify(expected), exactStringify({ count: 9007199254740993n }));
  for (const token of ['9007199254740992', '9007199254740994']) {
    assert.notEqual(exactStringify(expected), exactStringify(parseExactJson(`{"count":${token}}`)));
  }
});

test('integer tokens stay separate from floats, strings and ordered arrays', () => {
  const value = parseExactJson('[0,-9007199254740993,1.0,1e2,"9007199254740993"]');
  assert.deepEqual(value, [0n, -9007199254740993n, 1, 100, '9007199254740993']);
  assert.notEqual(exactStringify(value), exactStringify([...value].reverse()));
  assert.notEqual(exactStringify(1n), exactStringify(1));
});
