import test from 'node:test';
import assert from 'node:assert/strict';
import {indexMetrics} from '../src/index-metrics.mjs';
test('指数均线与区位来自相同序列，五日涨跌以五个交易日前收盘为基准',()=>{
 const m=indexMetrics([10,11,12,13,14,15],15);
 assert.equal(m.return5,50);
 assert.equal(m.low,10);assert.equal(m.high,15);assert.equal(m.location,100);
 assert.equal(m.ma20,null);
});
test('均线不足和固定价格序列不伪造趋势或区位',()=>{
 const m=indexMetrics(Array(250).fill(100),100);
 assert.equal(m.ma20,100);assert.equal(m.ma60,100);assert.equal(m.ma200,100);
 assert.equal(m.location,null);assert.equal(m.return20,0);
});
