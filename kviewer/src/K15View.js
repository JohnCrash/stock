import React, { Component } from 'react';
import { withStyles } from '@material-ui/core/styles';
import {timestampString,getDayLength,days} from './kits';
import FetchChart from './FetchChart';
import GameChart from './GameChart';
import Button from '@material-ui/core/Button';
import Chip from '@material-ui/core/Chip';
import AttachMoneyIcon from '@material-ui/icons/AttachMoney';
import Typography from '@material-ui/core/Typography';
import macd from 'macd';

const upColor = '#ec0000';
const upBorderColor = '#ec0000';
const downColor = '#00da3c';
const downBorderColor = '#008F28';
const goldColor = '#ffd54f';
const buyColor = '#7c4dff';

const styles = theme => ({
    root: {
        width:'100%'     
    },
    graph:{
        width:'100%',
        display:'flex',

    },
    button: {
        margin: theme.spacing.unit
    },
    clip: {
        margin: theme.spacing.unit,
        primaryColor:{
            backgroundColor:'#00FF00',
            color:'#00FF00'
        }
    },
    control:{
        width:'100%',
        display:'flex',
        justifyContent:"center",
        flexWrap:"wrap"
    }   
  });

function p100(d){
    return Math.floor(d*10000)/10000;
}

function arrayScale(a,n){
    let s = [];
    for(let it of a){
        for(let i=0;i<n;i++)
            s.push(it);
    }
    return s;
}

class K15View extends Component{
    constructor(props){
        super(props);
    }

    init = ([{results}])=>{
        let dates = [];
        let values = [];
        let volumes = [];
        let macd15data = [];
        let macd30data = [];
        let macd60data = [];
        let macd120data = [];
        let macddaydata = [];
        let beili15 = [];
        results.reverse().forEach((k,i) => {
            let dateStr = timestampString(k.timestamp);
            dates.push(dateStr);
            values.push([k.open,k.close,k.low,k.high]);
            volumes.push([i,k.volume,k.close-k.open]);
            macd15data.push(k.close);
            if(i%2==0)macd30data.push(k.close);
            if(i%4==0)macd60data.push(k.close);
            if(i%8==0)macd120data.push(k.close);
            if(i%16==0)macddaydata.push(k.close);
        });
        let macd15 = macd(macd15data).histogram;
        let macd30 = arrayScale(macd(macd30data).histogram,2);
        let macd60 = arrayScale(macd(macd60data).histogram,4);
        let macd120 = arrayScale(macd(macd120data).histogram,8);
        let macdday = arrayScale(macd(macddaydata).histogram,16);
        //计算背离率
        /*
        beili15.push(0);
        for(let i=1;i<macd15.length;i++){
            if(values[i][1]-values[i-1][1]>0 && macd15[i]-macd15[i-1]<0 )
                beili15.push(-1);
            else if(values[i][1]-values[i-1][1] < 0 && macd15[i]-macd15[i-1]>0)
                beili15.push(1);
            else
                beili15.push(0);
        }*/
        
        let dl = Math.abs(Math.floor(12000/dates.length));
        return {
            tooltip: {
                trigger: 'axis',
                axisPointer: {
                    type: 'cross'
                }
            },
            axisPointer: {
                link: {xAxisIndex: 'all'}
            },            
            legend: {
                data: ['15K','Volume','15','30','60','120','day']
            }, 
            visualMap: [{
                show: false,
                seriesIndex: [1],
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
                seriesIndex: [2],
                dimension: 1,
                pieces: [{
                    max: 0,
                    color: downColor
                }, {
                    min: 0,
                    color: upColor
                }]
            }],            
            grid: [
                { //k
                    left: '3%',
                    right: '3%',
                    height: '48%'
                },
                {//volume
                    left: '3%',
                    right: '3%',
                    top: '58%',
                    height: '12%'
                },                
                {//macd
                    left: '3%',
                    right: '3%',
                    top: '62%',
                    height: '36%'
                },
                {//背离
                    left: '3%',
                    right: '3%',
                    top: '0%',
                    height: '36%'
                }                
            ],
            xAxis: [
                {
                    type: 'category',
                    data: dates,
                    scale: true,
                    boundaryGap : false,
                    axisLine: {onZero: false},
                    splitLine: {
                        interval:15,
                        show: true},
                    splitNumber: 16,
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
                }],
            yAxis: [
                {
                    scale: true
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
                    splitNumber: 3,
                    axisLabel: {show: true},
                    axisLine: {show: true},
                    axisTick: {show: false},
                    splitLine: {show: false}
                }],
            dataZoom: [
                {
                    type: 'inside',
                    xAxisIndex: [0,1,2,3],
                    start: 100-dl,
                    end: 100
                }],
            series: [
                {
                    name: '15K',
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
                    name: 'Volume',
                    type: 'bar',
                    symbol: 'none',
                    data: volumes,
                    xAxisIndex: 1,
                    yAxisIndex: 1
                },
                {
                    name: '15',
                    type: 'bar',
                    symbol: 'none',
                    data: macd15,
                    xAxisIndex: 2,
                    yAxisIndex: 2,                     
                    barWidth:3
                },
                {
                    name: '30',
                    type: 'line',
                    symbol: 'none',
                    data: macd30,
                    xAxisIndex: 2,
                    yAxisIndex: 2,
                    itemStyle:{
                        color:'#00acc1'
                    }
                },
                {
                    name: '60',
                    type: 'line',
                    symbol: 'none',
                    data: macd60,
                    xAxisIndex: 2,
                    yAxisIndex: 2,
                    itemStyle:{
                        color:'#ffa000'
                    }
                },
                {
                    name: '120',
                    type: 'line',
                    symbol: 'none',
                    data: macd120,
                    xAxisIndex: 2,
                    yAxisIndex: 2,
                    itemStyle:{
                        color:'#ef5350'
                    }
                },
                {
                    name: 'day',
                    type: 'line',
                    symbol: 'none',
                    data: macdday,
                    xAxisIndex: 2,
                    yAxisIndex: 2,
                    itemStyle:{
                        color:'#ab47bc'
                    }
                }
                /*,{
                    name: 'beili',
                    type: 'bar',
                    symbol: 'none',
                    data: beili15,
                    xAxisIndex: 3,
                    yAxisIndex: 3,
                    itemStyle:{
                        color:'#ab47bc'
                    }
                }        */                                
            ]              
        };
    }

    render(){
        let {classes} = this.props;
        return <div className={classes.root}>
            <FetchChart api={['/api/k15']} init={this.init} width="100%" height={860}/>
        </div>
    }
}

export default withStyles(styles)(K15View);

