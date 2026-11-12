import test from 'node:test';
import assert from 'node:assert/strict';
import {comparisonSeries,coverageSummary} from '../src/terminal-data.mjs';
test('对比曲线以共同起点归零，量能与曲线长度一致',()=>{
 const x=comparisonSeries(60,3);
 assert.equal(x.primary.length,60);assert.equal(x.benchmark.length,60);assert.equal(x.volume.length,60);
 assert.equal(x.primary[0],0);assert.equal(x.benchmark[0],0);
 assert.ok([...x.primary,...x.benchmark,...x.volume].every(Number.isFinite));
});
test('盈利覆盖排除ETF，低位统计分母为有效样本',()=>{
 const c=coverageSummary([{market:'ETF',profit:0,quality:'完整',price:1,low:.9},{market:'A股',profit:5,quality:'完整',price:10,low:9},{market:'港股',profit:4,quality:'缺失',price:20,low:10}]);
 assert.equal(c.profitable,1);assert.equal(c.companies,2);assert.equal(c.nearLow,2);assert.equal(c.total,3);assert.equal(c.complete,2);
});
