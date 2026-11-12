export type Stock={id:string;name:string;code:string;market:string;industry:string;ownership:string;price:number;change:number;low:number;high:number;profit:number;pe:number|null;label:string;quality:string;color:string};
export const stocks:Stock[]=[
{id:'600905',name:'三峡能源',code:'600905',market:'A股',industry:'公用事业',ownership:'央企控股',price:4.32,change:1.17,low:3.86,high:6.2,profit:5,pe:18.6,label:'重点关注',quality:'完整',color:'#79b9a2'},
{id:'601668',name:'中国建筑',code:'601668',market:'A股',industry:'建筑装饰',ownership:'央企控股',price:5.18,change:.78,low:4.65,high:7.1,profit:5,pe:4.2,label:'值得考虑',quality:'完整',color:'#aaa4db'},
{id:'600028',name:'中国石化',code:'600028',market:'A股',industry:'石油石化',ownership:'央企控股',price:5.69,change:-.52,low:5.1,high:7.85,profit:5,pe:12.8,label:'继续观察',quality:'完整',color:'#c1ab7b'},
{id:'601288',name:'农业银行',code:'601288',market:'A股',industry:'银行',ownership:'央企控股',price:5.84,change:.86,low:3.3,high:7.25,profit:5,pe:6.4,label:'继续观察',quality:'完整',color:'#86abc8'},
{id:'00762',name:'中国联通',code:'00762',market:'港股',industry:'通信',ownership:'红筹 / 央企',price:7.18,change:-1.24,low:5.48,high:10.6,profit:5,pe:10.3,label:'重点关注',quality:'延迟15分钟',color:'#7c9bd0'},
{id:'601390',name:'中国中铁',code:'601390',market:'A股',industry:'建筑装饰',ownership:'央企控股',price:5.36,change:-.37,low:5.02,high:8.18,profit:5,pe:4.9,label:'重点关注',quality:'完整',color:'#aaa4db'},
{id:'000898',name:'鞍钢股份',code:'000898',market:'A股',industry:'钢铁',ownership:'央企控股',price:2.41,change:-1.63,low:2.08,high:4.06,profit:2,pe:null,label:'风险优先',quality:'完整',color:'#b79b8f'},
{id:'600019',name:'宝钢股份',code:'600019',market:'A股',industry:'钢铁',ownership:'央企控股',price:6.65,change:.45,low:5.45,high:8.54,profit:5,pe:13.1,label:'继续观察',quality:'完整',color:'#b79b8f'},
{id:'00941',name:'中国移动',code:'00941',market:'港股',industry:'通信',ownership:'红筹 / 央企',price:77.4,change:.65,low:59.2,high:91.2,profit:5,pe:11.6,label:'继续观察',quality:'延迟15分钟',color:'#7c9bd0'},
{id:'588080',name:'科创板50ETF',code:'588080',market:'ETF',industry:'宽基指数',ownership:'不适用',price:1.12,change:1.82,low:.72,high:1.52,profit:0,pe:null,label:'规则待配置',quality:'完整',color:'#a6bd86'},
{id:'002415',name:'海康威视',code:'002415',market:'A股',industry:'计算机',ownership:'央企控股',price:28.5,change:-.83,low:24.2,high:39.4,profit:5,pe:19.2,label:'继续观察',quality:'历史待补齐',color:'#b0a1c1'},
{id:'600104',name:'上汽集团',code:'600104',market:'A股',industry:'汽车',ownership:'地方国企',price:14.26,change:1.13,low:11.85,high:21.5,profit:4,pe:16.4,label:'资料不足',quality:'缺少1年财报',color:'#c2a48c'}];
export const indices=[['上证指数','3,365.12',.82,'A股'],['深证成指','10,821.46',1.16,'A股'],['创业板指','2,264.83',1.43,'A股'],['恒生指数','23,186.62',-.64,'港股'],['恒生科技','5,218.37',-1.08,'港股'],['标普500','5,918.24',.38,'美股'],['纳斯达克综合','18,426.52',.72,'美股'],['道琼斯指数','43,621.16',-.15,'美股'],['沪深300','3,986.28',.69,'A股']] as const;
export type Position={id:string;qty:number;cost:number;realized:number};
export type Entry={id:string;stock:string;type:string;qty:number;price:number;fee:number;time:string};
export type Alert={id:string;stock:string;metric:string;value:number;enabled:boolean};
export type State={version:number;watch:string[];positions:Position[];entries:Entry[];alerts:Alert[];notes:Record<string,string>;settings:{interval:string;maxPrice:string;redUp:boolean};};
export const initialState:State={version:1,watch:stocks.map(s=>s.id),positions:[{id:'600905',qty:4000,cost:18120,realized:0},{id:'601668',qty:3000,cost:14700,realized:0},{id:'00762',qty:2000,cost:13100,realized:0},{id:'601288',qty:3000,cost:15810,realized:0},{id:'588080',qty:10000,cost:10200,realized:0}],entries:[],alerts:[{id:'a1',stock:'600905',metric:'价格低于',value:4.2,enabled:true},{id:'a2',stock:'601390',metric:'距低点小于',value:8,enabled:true},{id:'a3',stock:'00762',metric:'价格高于',value:8,enabled:false}],notes:{'600905':'关注新能源运营现金流与分红改善，等待趋势确认。此处为示例研究笔记。'},settings:{interval:'5',maxPrice:'20',redUp:true}};
export function series(base:number,count=60,seed=2){let x=seed;return Array.from({length:count},(_,i)=>{x=(x*9301+49297)%233280;return +(base*(.92+i/count*.07+(x/233280-.5)*.022+Math.sin(i/7)*.018)).toFixed(3)});}
