import React, { Component } from 'react';
import { withStyles } from '@material-ui/core/styles';
import {dateString,getDayLength,days} from './kits';
import FetchChart from './FetchChart';

const upColor = '#ec0000';
const upBorderColor = '#ec0000';
const downColor = '#00da3c';
const downBorderColor = '#008F28';
const goldColor = '#ffd54f';
const buyColor = '#7c4dff';

const styles = theme => ({
    root: {
        width:'100%'
      }
  });

function KView(props){
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
        let volume = [];
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

        function getMerchsRate(date,i){
            let v = merchsMaps[date];
            return [i,v?v.rate:0,date&&v&&v.max_date&&date==v.max_date?-1:1];
        }
        results.reverse().forEach((element,i) => {
            let dateStr = dateString(element.date);
            dates.push(dateStr);
            values.push([element.open,element.close,element.low,element.high]);
            ma5.push(element.ma5);
            ma10.push(element.ma10);
            ma20.push(element.ma20);
            ma30.push(element.ma30);
            volume.push([i,element.volume,element.close-element.open]);
            macd.push(element.macd);
            merchs.push(getMerchsRate(element.date,i)); //将改天的交易数据放入，没有就是0
        });
        //金叉死叉分布，将时间走同步的kd线一致
        //=================================
        let buysells = a[2].results;
        let dateBuySell = {};
        let buys = [];
        let sells = [];
        let positives = [];
        let negatives = [];
        for(let i=0;i<buysells.length;i++){
            let v = buysells[i];
            dateBuySell[dateString(v.date)] = {buy:v.buy,sell:v.sell,positive:v.positive,negative:v.negative};
        }
        for(let d of dates){
            let v = dateBuySell[dateString(d)];
            if(v){
                buys.push(v.buy);
                sells.push(-v.sell);
                positives.push(v.positive);
                negatives.push(-v.negative);       
            }else{
                buys.push(0);
                sells.push(0);
                positives.push(0);
                negatives.push(0);                   
            }
        }
        //=================================
        let dl = Math.abs(Math.floor(16000/getDayLength(results[0].date,results[results.length-1].date)));
        return {
            tooltip: {
                trigger: 'axis',
                axisPointer: {
                    type: 'cross'
                }
            },
            legend: {
                data: ['日K', 'MA5', 'MA10', 'MA20', 'MA30','成交量','MACD','交易','金叉','死叉','macd正','macd负']
            },
            visualMap: [{
                show: false,
                seriesIndex: [5],
                dimension: 2,
                pieces: [{
                    max: 0,
                    color: downColor
                }, {
                    min: 0,
                    color: upColor
                }]
                },
                {
                    show: false,
                    seriesIndex: [6,7],
                    dimension: 1,
                    pieces: [{
                        max: 0,
                        color: downColor
                    }, {
                        min: 0,
                        color: upColor
                    }]
                },
                {
                    show: false,
                    seriesIndex: [7],
                    dimension: 2,
                    pieces: [{
                        max: 0,
                        color: goldColor
                    }, {
                        min: 0,
                        color: buyColor
                    }]
                }
            ],
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
                link: {xAxisIndex: 'all'}
            },
            grid: [
                { //k
                    left: '3%',
                    right: '3%',
                    height: '58%'
                },
                {//volume
                    left: '3%',
                    right: '3%',
                    top: '60.3%',
                    height: '5%'
                },
                {//macd
                    left: '3%',
                    right: '3%',
                    top: '68%',
                    height: '6%'
                },
                {//tr
                    left: '3%',
                    right: '3%',
                    top: '72%',
                    height: '3%'
                },
                {//sign
                    left: '3%',
                    right: '3%',
                    top: '73%',
                    height: '16%'
                },
                {//金叉死叉存量
                    left: '3%',
                    right: '3%',
                    top: '83%',
                    height: '10%'
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
                    max: 'dataMax',
                    axisPointer: {
                        label:{
                            show:false
                        }
                    }
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
                    max: 'dataMax',
                    axisPointer: {
                        label:{
                            show:false
                        }
                    }
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
                    max: 'dataMax',
                    axisPointer: {
                        label:{
                            show:false
                        }
                    }
                },                
                {
                    type: 'category',
                    gridIndex: 3,
                    data: dates,
                    scale: true,
                    boundaryGap : false,
                    axisLine: {onZero: true},
                    axisTick: {show: false},
                    splitLine: {show: false},
                    axisLabel: {show: false},
                    splitNumber: 20,
                    min: 'dataMin',
                    max: 'dataMax',
                    axisPointer: {
                        label:{
                            show:false
                        }
                    }
                },                
                {
                    type: 'category',
                    gridIndex: 4,
                    data: dates,
                    scale: true,
                    boundaryGap : false,
                    axisLine: {onZero: true},
                    axisTick: {show: false},
                    splitLine: {show: false},
                    axisLabel: {show: false},
                    splitNumber: 20,
                    min: 'dataMin',
                    max: 'dataMax',
                    axisPointer: {
                        label:{
                            show:false
                        }
                    }
                },                
                {
                    type: 'category',
                    gridIndex: 5,
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
                },
                {
                    scale: true,
                    gridIndex: 3,
                    splitNumber: 2,
                    axisLabel: {show: true},
                    axisLine: {show: true},
                    axisTick: {show: false},
                    splitLine: {show: false}
                },
                {
                    scale: true,
                    gridIndex: 4,
                    splitNumber: 2,
                    axisLabel: {show: true},
                    axisLine: {show: true},
                    axisTick: {show: false},
                    splitLine: {show: false}
                },
                {
                    scale: true,
                    gridIndex: 5,
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
                    xAxisIndex: [0,1,2,3,4,5],
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
                    name: '成交量',
                    type: 'bar',
                    xAxisIndex: 1,
                    yAxisIndex: 1,
                    data: volume
                },                
                {
                    name: 'MACD',
                    type: 'bar',
                    xAxisIndex: 2,
                    yAxisIndex: 2,
                    data: macd
                },               
                {
                    name: '交易',
                    type: 'bar',
                    xAxisIndex: 3,
                    yAxisIndex: 3,
                    data: merchs
                },
                {
                    name: '金叉',
                    type: 'bar',
                    stack:'one',
                    data: buys,
                    xAxisIndex: 4,
                    yAxisIndex: 4,                    
                    itemStyle:{
                        color : upColor
                    }
                },
                {
                    name: '死叉',
                    type: 'bar',
                    stack:'one',
                    data : sells,
                    xAxisIndex: 4,
                    yAxisIndex: 4,                    
                    itemStyle:{
                        color : downColor
                    }
                },
                {
                    name: 'macd正',
                    type: 'line',
                    stack:'two',
                    data: positives,
                    xAxisIndex: 5,
                    yAxisIndex: 5,                    
                    itemStyle:{
                        color : upColor
                    }
                },
                {
                    name: 'macd负',
                    type: 'line',
                    stack:'two',
                    data : negatives,
                    xAxisIndex: 5,
                    yAxisIndex: 5,                    
                    itemStyle:{
                        color : downColor
                    }
                }
            ]            
        };        
    }
    //<FetchChart api={['/api/k','/api/macd']} args={{db:'tech_macdrate'}} init={init} {...props}/>
    return <div className={classes.root}>
        <FetchChart api={['/api/k','/api/macd','/api/buysell']} init={init} {...props}/>
    </div>;
}

export default withStyles(styles)(KView);