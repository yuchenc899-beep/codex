export function filterStocks(rows, f={}) {
 return rows.filter(s=>(!f.market||f.market==='全部市场'||s.market===f.market)&&(!f.max||(s.price!==null&&s.price<f.max))&&(!f.min||(s.price!==null&&s.price>=f.min))&&(!f.industry||f.industry==='全部行业'||s.industry===f.industry)&&(!f.ownership||f.ownership==='全部属性'||s.ownership===f.ownership)&&(!f.query||`${s.name} ${s.code} ${s.industry}`.toLowerCase().includes(f.query.toLowerCase())));
}
export function trade(position,event) {
 const {qty,price,fee,type}=event;
 if(![qty,price,fee].every(Number.isFinite)||qty<=0||price<=0||fee<0)throw new Error('请输入有效的数量、成交价与费用');
 if(!['BUY','SELL','OPENING'].includes(type))throw new Error('不支持的记录类型');
 if(type==='OPENING'){
  if(position.qty>0)throw new Error('已有持仓，请使用买入或更正');
  return {qty,cost:qty*price+fee,realized:0};
 }
 if(type==='BUY')return {...position,qty:position.qty+qty,cost:position.cost+qty*price+fee};
 if(qty>position.qty)throw new Error('卖出数量超过当前示例持仓');
 const released=qty===position.qty?position.cost:position.cost/position.qty*qty;
 return {qty:position.qty-qty,cost:qty===position.qty?0:position.cost-released,realized:position.realized+qty*price-fee-released};
}
export function addWatch(ids,id){ return ids.includes(id)?ids:[...ids,id]; }
