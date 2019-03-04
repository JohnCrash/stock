/**
 * k图表使用echarts库显示
 */
import React, { Component } from 'react';
import EChart from './echart';
import {postJson} from './fetch';
import {getDayLength} from './kits';

const upColor = '#ec0000';
const upBorderColor = '#ec0000';
const downColor = '#00da3c';
const downBorderColor = '#008F28';


class KView extends Component{
    constructor(props){
        super(props);  
        this.state = {options:{}};
    }
    componentWillUpdate(nextProps, nextState, snapshot){
        if(nextProps.code!==this.props.code||nextProps.range!==this.props.range)
            this.initComponent(nextProps);
    }
    componentDidMount(){
        this.initComponent(this.props);
    }
    initComponent({code,range}){
        postJson('/api/k',{code,range},(json)=>{
            if(json.results){
                this.setState({options:this.initData(json.name,json.results)});
            }else{
                console.error(json.error);
            }
        });
    }
    initData(name,results){
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
        let dl = Math.abs(Math.floor(16000/getDayLength(results[0].date,results[results.length-1].date)));
        return {
            title: {
                text: name?name:'上证指数',
                left: 0
            },
            tooltip: {
                trigger: 'axis',
                axisPointer: {
                    type: 'cross'
                }
            },
            legend: {
                data: ['日K', 'MA5', 'MA10', 'MA20', 'MA30']
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
            grid: [
                {
                    left: '6%',
                    right: '6%',
                    height: '65%'
                },
                {
                    left: '6%',
                    right: '6%',
                    top: '78%',
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
                    start: 100-dl,
                    end: 100
                },
                {
                    show: true,
                    xAxisIndex: [0, 1],
                    type: 'slider',
                    y: '90%',
                    start: 50,
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
    splitData(rawData) {
        var categoryData = [];
        var values = []
        for (var i = 0; i < rawData.length; i++) {
            categoryData.push(rawData[i].splice(0, 1)[0]);
            values.push(rawData[i])
        }
        return {
            categoryData: categoryData,
            values: values
        };
    }
    
    calculateMA(data0,dayCount) {
        var result = [];
        for (var i = 0, len = data0.values.length; i < len; i++) {
            if (i < dayCount) {
                result.push('-');
                continue;
            }
            var sum = 0;
            for (var j = 0; j < dayCount; j++) {
                sum += data0.values[i - j][1];
            }
            result.push(sum / dayCount);
        }
        return result;
    }
    render(){
        let {width,height} = this.props
        return <EChart options={this.state.options} width={width} height={height}/>;
    }
};

export default KView;