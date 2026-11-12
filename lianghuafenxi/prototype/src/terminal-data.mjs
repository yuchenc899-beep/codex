export function comparisonSeries(count=90,seed=1){
 const make=(phase,slope)=>{const initial=Math.sin(phase)*1.4;return Array.from({length:count},(_,i)=>+(i/(count-1)*slope+Math.sin(i/9+phase)*1.4-initial+Math.sin(i/2.8)*.3-(i>count*.58?1.7:0)).toFixed(2));};
 return {primary:make(seed*.6,4.8+seed*.35),benchmark:make(seed*.4,3.5+seed*.22),volume:Array.from({length:count},(_,i)=>Math.round(22+Math.abs(Math.sin(i*1.8+seed))*42+(i%17===0?42:0)))};
}
export function coverageSummary(stocks){
 const companies=stocks.filter(s=>s.market!=='ETF');
 const valid=stocks.filter(s=>Number.isFinite(s.price)&&Number.isFinite(s.low)&&s.low>0);
 return {total:stocks.length,companies:companies.length,profitable:companies.filter(s=>s.profit===5).length,complete:stocks.filter(s=>s.quality==='完整').length,nearLow:valid.filter(s=>(s.price/s.low-1)<.15).length,valid:valid.length};
}
