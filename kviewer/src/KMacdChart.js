import React, { Component } from 'react';
import FetchChart from './FetchChart';

const upColor = '#ec0000';
const upBorderColor = '#ec0000';
const downColor = '#00da3c';
const downBorderColor = '#008F28';

function KMacdChart(props){
    let {} = props;
    return <FetchChart api={['/api/k','/api/macd']} args={{code:props.code,range:40}} init={
        (a)=>{
            let name = a[0].name;
            let results = a[0].results;
            let dates = [];
            let values = [];
            let ma5 = [];
            let ma10 = [];
            let ma20 = [];
            let ma30 = [];
            let macd = [];
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
            });
            return {
            //    title: {
            //        text: name?name:'上证指数',
            //        left: 0
            //    },
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
                    seriesIndex: 5,
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
                        axisLine: {onZero: false},
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
                        axisLabel: {show: false},
                        axisLine: {show: false},
                        axisTick: {show: false},
                        splitLine: {show: false}
                    }
                ],
                dataZoom: [
                    {
                        type: 'inside',
                        xAxisIndex: [0, 1],
                        start: 98,
                        end: 100
                    },
                    {
                        show: true,
                        xAxisIndex: [0, 1],
                        type: 'slider',
                        y: '90%',
                        start: 90,
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
                        },
                        markPoint: {
                            label: {
                                normal: {
                                    formatter: function (param) {
                                        return param != null ? Math.round(param.value) : '';
                                    }
                                }
                            },
                            data: [
    
                                {
                                    name: 'highest value',
                                    type: 'max',
                                    valueDim: 'highest'
                                },
                                {
                                    name: 'lowest value',
                                    type: 'min',
                                    valueDim: 'lowest'
                                },
                                {
                                    name: 'average value on close',
                                    type: 'average',
                                    valueDim: 'close'
                                }
                            ],
                            tooltip: {
                                formatter: function (param) {
                                    return param.name + '<br>' + (param.data.coord || '');
                                }
                            }
                        },
                        markLine: {
                            symbol: ['none', 'none'],
                            data: [
                                [
                                    {
                                        name: 'from lowest to highest',
                                        type: 'min',
                                        valueDim: 'lowest',
                                        symbol: 'circle',
                                        symbolSize: 10,
                                        label: {
                                            normal: {show: false},
                                            emphasis: {show: false}
                                        }
                                    },
                                    {
                                        type: 'max',
                                        valueDim: 'highest',
                                        symbol: 'circle',
                                        symbolSize: 10,
                                        label: {
                                            normal: {show: false},
                                            emphasis: {show: false}
                                        }
                                    }
                                ],
                                {
                                    name: 'min line on close',
                                    type: 'min',
                                    valueDim: 'close'
                                },
                                {
                                    name: 'max line on close',
                                    type: 'max',
                                    valueDim: 'close'
                                }                           
                            ]
                        }
                    },
                    {
                        name: 'MA5',
                        type: 'line',
                        symbol: 'none',
                        data: ma5,
                        smooth: true,
                        lineStyle: {
                            normal: {color:'#fdd835'}
                        }
                    },
                    {
                        name: 'MA10',
                        type: 'line',
                        symbol: 'none',
                        data: ma10,
                        smooth: true,
                        lineStyle: {
                            normal: {color:'#0277bd'}
                        }
                    },
                    {
                        name: 'MA20',
                        type: 'line',
                        symbol: 'none',
                        data: ma20,
                        smooth: true,
                        lineStyle: {
                            normal: {color:'#ab47bc'}
                        }
                    },
                    {
                        name: 'MA30',
                        type: 'line',
                        symbol: 'none',
                        data: ma30,
                        smooth: true,
                        lineStyle: {
                            normal: {color:'#ef6c00'}
                        }
                    },
                    {
                        name: 'MACD',
                        type: 'bar',
                        xAxisIndex: 1,
                        yAxisIndex: 1,
                        data: macd
                    }                             
                ]            
            };          
        }
    } {...props}/>;
}

export default KMacdChart;