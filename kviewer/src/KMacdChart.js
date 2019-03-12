import React, { Component } from 'react';
import { withStyles } from '@material-ui/core/styles';
import FetchChart from './FetchChart';
import {getDayLength,days} from './kits';
import Typography from '@material-ui/core/Typography';

const upColor = '#ec0000';
const upBorderColor = '#ec0000';
const downColor = '#00da3c';
const downBorderColor = '#008F28';

const styles = theme => ({
    root: {
        width:'100%'
      }
  });

function KMacdChart(props){
    let {classes} = props;
    function init(a){
        let name = a[0].name;
        let results = a[0].results;
        let dates = [];
        let values = [];
        let ma5 = [];
        let ma10 = [];
        let ma20 = [];
        let ma30 = [];
        let macd = [];
        let merchsData = a[1].results;
        let merchs = [];
        // 将macd交易数据的时间整合到k的时间线上
        let merchsMaps = {};
        for(let v of merchsData){
            //merchsMaps[v.buy_date] = v;
            //merchsMaps[v.sell_date] = v;
            //将中间填满
            for(let d of days(v.buy_date,v.sell_date)){
                merchsMaps[d] = v;
            }
        }
        function getMerchsRate(date){
            let v = merchsMaps[date];
            return v?v.rate:0;
        }
        results.reverse().forEach(element => {
            let d = new Date(element.date);
            let dateString = `${d.getFullYear()}/${d.getMonth()+1}/${d.getDate()}`;
            dates.push(dateString);
            values.push([element.open,element.close,element.low,element.high]);
            ma5.push(element.ma5);
            ma10.push(element.ma10);
            ma20.push(element.ma20);
            ma30.push(element.ma30);
            macd.push(element.macd);
            merchs.push(getMerchsRate(element.date)); //将改天的交易数据放入，没有就是0
        });
        let dl = Math.abs(Math.floor(32000/getDayLength(results[0].date,results[results.length-1].date)));
        return {
            tooltip: {
                trigger: 'axis',
                axisPointer: {
                    type: 'cross'
                }
            },
            legend: {
                data: ['日K', 'MA5', 'MA10', 'MA20', 'MA30']
            },
            visualMap: {
                show: false,
                seriesIndex: [5,6],
                dimension: 1,
                pieces: [{
                    max: 0,
                    color: downColor
                }, {
                    min: 0,
                    color: upColor
                }]
            },
            tooltip: {
                trigger: 'axis',
                axisPointer: {
                    type: 'cross'
                },
                backgroundColor: 'rgba(245, 245, 245, 0.5)',
                borderWidth: 1,
                borderColor: '#ccc',
                padding: 10,
                textStyle: {
                    color: '#000'
                }                    
            },    
            axisPointer: {
                link: {xAxisIndex: 'all'},
                label: {
                    backgroundColor: '#777'
                }
            },                      
            grid: [
                {
                    left: '6%',
                    right: '6%',
                    height: '50%'
                },
                {
                    left: '6%',
                    right: '6%',
                    top: '63%',
                    height: '8%'
                },
                {
                    left: '6%',
                    right: '6%',
                    top: '72%',
                    height: '16%'
                }
            ],
            xAxis: [
                {
                    type: 'category',
                    data: dates,
                    scale: true,
                    boundaryGap : false,
                    axisLine: {onZero: false},
                    splitLine: {show: false},
                    splitNumber: 20,
                    min: 'dataMin',
                    max: 'dataMax'
                },
                {
                    type: 'category',
                    gridIndex: 1,
                    data: dates,
                    scale: true,
                    boundaryGap : false,
                    axisLine: {onZero: true},
                    axisTick: {show: false},
                    splitLine: {show: false},
                    axisLabel: {show: false},
                    splitNumber: 20,
                    min: 'dataMin',
                    max: 'dataMax'
                },
                {
                    type: 'category',
                    gridIndex: 2,
                    data: dates,
                    scale: false,
                    boundaryGap : false,
                    axisLine: {onZero: true},
                    axisTick: {show: false},
                    splitLine: {show: false},
                    axisLabel: {show: false},
                    splitNumber: 20,
                    min: 'dataMin',
                    max: 'dataMax'
                }
            ],
            yAxis: [
                {
                    scale: true,
                    splitArea: {
                        show: true
                    }
                },
                {
                    scale: true,
                    gridIndex: 1,
                    splitNumber: 2,
                    axisLabel: {show: true},
                    axisLine: {show: true},
                    axisTick: {show: false},
                    splitLine: {show: false}
                },
                {
                    scale: true,
                    gridIndex: 2,
                    splitNumber: 2,
                    axisLabel: {show: true},
                    axisLine: {show: true},
                    axisTick: {show: false},
                    splitLine: {show: false}
                }                    
            ],
            dataZoom: [
                {
                    type: 'inside',
                    xAxisIndex: [0, 1],
                    start: 100-dl,
                    end: 100
                },
                {
                    show: true,
                    xAxisIndex: [0,1,2],
                    type: 'slider',
                    y: '90%',
                    start: 100-dl,
                    end: 100
                }                   
            ],
            series: [
                {
                    name: '日K',
                    type: 'candlestick',
                    data: values,
                    itemStyle: {
                        normal: {
                            color: upColor,
                            color0: downColor,
                            borderColor: upBorderColor,
                            borderColor0: downBorderColor
                        }
                    }
                },
                {
                    name: 'MA5',
                    type: 'line',
                    symbol: 'none',
                    data: ma5,
                    smooth: true,
                    itemStyle: {
                        normal: {color:'#fdd835'}
                    }
                },
                {
                    name: 'MA10',
                    type: 'line',
                    symbol: 'none',
                    data: ma10,
                    smooth: true,
                    itemStyle: {
                        normal: {color:'#0277bd'}
                    }
                },
                {
                    name: 'MA20',
                    type: 'line',
                    symbol: 'none',
                    data: ma20,
                    smooth: true,
                    itemStyle: {
                        normal: {color:'#ab47bc'}
                    }
                },
                {
                    name: 'MA30',
                    type: 'line',
                    symbol: 'none',
                    data: ma30,
                    smooth: true,
                    itemStyle: {
                        normal: {color:'#ef6c00'}
                    }
                },
                {
                    name: 'MACD',
                    type: 'bar',
                    xAxisIndex: 1,
                    yAxisIndex: 1,
                    data: macd
                },
                {
                    name: '交易',
                    type: 'bar',
                    xAxisIndex: 2,
                    yAxisIndex: 2,
                    data: merchs
                }                       
            ]            
        };        
    }
    return <div className={classes.root}>
        <FetchChart api={['/api/k','/api/macd']} init={init} {...props}/>
        <FetchChart api={['/api/k','/api/macd']} args={{db:'tech_macdrate'}} init={init} {...props}/>
        <Typography>
            图像的上部是标准的k线图，中间是macd，下部是交易情况，一个方块代表一次交易，红色代表盈利，绿色代表亏损。高度是盈利率。
        </Typography>
    </div>;
}

export default withStyles(styles)(KMacdChart);