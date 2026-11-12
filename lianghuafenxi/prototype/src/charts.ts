import * as core from 'echarts/core';
import {LineChart,PieChart,BarChart,CandlestickChart} from 'echarts/charts';
import {GridComponent,TooltipComponent,LegendComponent} from 'echarts/components';
import {SVGRenderer} from 'echarts/renderers';
core.use([LineChart,PieChart,BarChart,CandlestickChart,GridComponent,TooltipComponent,LegendComponent,SVGRenderer]);
core.registerTheme('yuchen',{
  color:['#9ccbfa','#7ad3af','#b5ace3','#dec38d','#8da9c7'],
  backgroundColor:'transparent',
  textStyle:{fontFamily:'Segoe UI Variable Text, Segoe UI, Microsoft YaHei, sans-serif',fontSize:12,color:'#aab1bc'},
  legend:{textStyle:{color:'#aab1bc',fontSize:11}},
  tooltip:{backgroundColor:'#1b1b1b',borderColor:'#363636',textStyle:{color:'#e8eaed',fontSize:12}},
  categoryAxis:{axisLabel:{color:'#9099a6',fontSize:11},axisLine:{lineStyle:{color:'#303030'}}},
  valueAxis:{axisLabel:{color:'#9099a6',fontSize:11},splitLine:{lineStyle:{color:'rgba(255,255,255,0.055)',type:'dashed'}}}
});
export const echarts=core;
