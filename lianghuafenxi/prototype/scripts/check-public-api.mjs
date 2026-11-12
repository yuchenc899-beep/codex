import {writeFile} from 'node:fs/promises';
const origin='http://127.0.0.1:8787/api/v1/';
const today=new Date().toLocaleDateString('en-CA',{timeZone:'Asia/Shanghai'});
const cases=[
 ['health','health',{},200],['config','config',{},200],['search-public-sample','instruments?q=600905',{},200],
 ['public-quotes','quotes/batch',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({instrument_ids:['INDEX:SH000001','INDEX:HSI','XSHG:600905']})},200],
 ['public-daily',`history/XSHG:600905?from=${today.slice(0,4)}-01-01&to=${today}`,{},200],
 ['public-finance','financials/XSHG:600905',{},200],
 ['unsupported-hk-finance','financials/XHKG:00762',{},422],
 ['unsupported-us-history',`history/INDEX:IXIC?from=${today.slice(0,4)}-01-01&to=${today}`,{},422],
 ['private-upload-disabled','ledger',{},403],
];
const results=[];
for(const [name,path,options,expected] of cases){const start=Date.now();try{const response=await fetch(origin+path,{...options,signal:AbortSignal.timeout(15000)});const body=await response.json(),d=body.data;results.push({name,status:response.status,expected,passed:response.status===expected,milliseconds:Date.now()-start,summary:d?{items:d.items?.length,indices:d.indices?.length,bars:d.bars?.length,rejected:d.rejected,reports:d.reports?.map(r=>({year:r.year,hasProfit:r.profit!=null,currency:r.currency,provider:r.provider})),quoteTimes:d.items?.filter(r=>r.receivedAt).map(r=>({id:r.id,last:r.last,sourceTime:r.sourceTime,sourceTimeRaw:r.sourceTimeRaw,receivedAt:r.receivedAt,provider:r.provider}))}:body.error});}catch(e){results.push({name,passed:false,error:e.message});}}
await writeFile(new URL('../../docs/validation/functional/public-api-check.json',import.meta.url),JSON.stringify({checkedAt:new Date().toISOString(),scope:'Public samples only; no personal holdings or full private watchlist',results},null,2));
for(const r of results)console.log(`${r.passed?'PASS':'FAIL'} ${r.name}: ${r.status??r.error}`);
if(results.some(r=>!r.passed))process.exitCode=1;
