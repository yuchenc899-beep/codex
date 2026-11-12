export function indexMetrics(closes,price){
 const ma=n=>closes.length>=n?closes.slice(-n).reduce((a,b)=>a+b,0)/n:null;
 const ret=n=>closes.length>n&&closes.at(-n-1)>0?(price/closes.at(-n-1)-1)*100:null;
 const low=closes.length?Math.min(...closes):null,high=closes.length?Math.max(...closes):null;
 return {ma20:ma(20),ma60:ma(60),ma200:ma(200),return5:ret(5),return20:ret(20),return60:ret(60),low,high,location:low!==null&&high>low?(price-low)/(high-low)*100:null};
}
