import test from 'node:test';
import assert from 'node:assert/strict';
import { filterStocks, trade, addWatch } from '../src/domain.mjs';
test('严格低于20，排除空报价，港股条件独立',()=>{
 const rows=[{id:'a',price:19.99,market:'A股'},{id:'b',price:20,market:'A股'},{id:'c',price:null,market:'A股'},{id:'h',price:15,market:'港股'}];
 assert.deepEqual(filterStocks(rows,{market:'A股',max:20}).map(x=>x.id),['a']);
});
test('含费买入和部分卖出保留成本，不能重复扣费',()=>{
 const p=trade({qty:100,cost:1000,realized:0},{type:'BUY',qty:100,price:12,fee:5});
 assert.deepEqual(p,{qty:200,cost:2205,realized:0});
 assert.deepEqual(trade(p,{type:'SELL',qty:50,price:13,fee:5}),{qty:150,cost:1653.75,realized:93.75});
});
test('超额卖出和非法值不改变持仓',()=>{
 assert.throws(()=>trade({qty:100,cost:1000,realized:0},{type:'SELL',qty:101,price:10,fee:0}));
 assert.throws(()=>trade({qty:100,cost:1000,realized:0},{type:'BUY',qty:-1,price:10,fee:0}));
});
test('重复加入自选幂等',()=>assert.deepEqual(addWatch(['a'],'a'),['a']));
