import assert from 'node:assert/strict';
import fs from 'node:fs';
import test from 'node:test';

import {
  formatEastern,
  freshnessState,
  parseFreshness
} from '../assets/js/yahoo-live.js';

test('freshness parser rejects malformed and older snapshots',()=>{
  const current=Date.parse('2026-09-15T00:10:00Z');
  assert.equal(parseFreshness('not-a-date',current),null);
  assert.equal(parseFreshness('2026-09-15T00:09:59Z',current),null);
  assert.equal(parseFreshness('2026-09-15T00:10:01Z',current),current+1000);
});

test('freshness state becomes stale without changing score values',()=>{
  const now=Date.parse('2026-09-15T01:00:00Z');
  assert.equal(freshnessState(now-60_000,now),'current');
  assert.equal(freshnessState(now-13*60_000,now),'stale');
});

test('visible freshness time is explicitly Eastern',()=>{
  assert.match(formatEastern(Date.parse('2026-09-15T00:00:00Z')),/8:00 PM EDT/);
});

test('client uses scoped no-cache polling and never reloads the page',()=>{
  const source=fs.readFileSync(new URL('../assets/js/yahoo-live.js',import.meta.url),'utf8');
  assert.match(source,/cache:'no-store'/);
  assert.match(source,/const SCORE_POLL_MS=60_000/);
  assert.match(source,/const ROSTER_POLL_MS=15\*60_000/);
  assert.doesNotMatch(source,/location\.reload|window\.location/);
});
