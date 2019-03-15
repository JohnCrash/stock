import React, { Component } from 'react';
import { withStyles } from '@material-ui/core/styles';
import FetchChart from './FetchChart';
import {postJson} from './fetch';
import Typography from '@material-ui/core/Typography';
import Button from '@material-ui/core/Button';
import {dateString} from './kits';
import {getDayLength,days} from './kits';

const upColor = '#ec0000';
const upBorderColor = '#ec0000';
const downColor = '#00da3c';
const downBorderColor = '#008F28';

const styles = theme => ({
    root: {
        width:'100%'
      },
    button: {
    }
});

class MacdBuyShellChart extends Component{
    render(){
        const {classes} = this.props;

        return (<div className={classes.root}>
        <FetchChart api='/api/buysell' init={
            ({results})=>{
                let dates = [];
                let buys = [];
                let sells = [];
                let positives = [];
                let negatives = [];
                let dl = Math.abs(Math.floor(16000/getDayLength(results[0].date,results[results.length-1].date)));
                for(let i=0;i<results.length;i++){
                    let v = results[i];
                    dates.push(dateString(v.date));
                    buys.push(v.buy);
                    sells.push(-v.sell);
                    positives.push(v.positive);
                    negatives.push(-v.negative);                    
                }
                return {
                    tooltip: {
                        trigger: 'axis',
                        axisPointer: {
                            type: 'cross'
                        }
                    },
                    legend: {
                        data: ['金叉','死叉','金叉存量','死叉存量']
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
                            height: '45%'
                        },
                        {
                            left: '6%',
                            right: '6%',
                            top: '55%',
                            height: '42%'
                        }
                    ],                    
                    xAxis: [{
                            type: 'category',
                            data: dates,
                            scale: true,
                            silent: false,
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
                            splitArea: {
                                show: true
                            }
                        }                        
                    ],
                    dataZoom: [
                        {
                            type: 'inside',
                            xAxisIndex: [0,1],
                            start: 100-dl,
                            end: 100
                        }                  
                    ],                    
                    series: [{
                        name: '金叉',
                        type: 'bar',
                        stack:'one',
                        data: buys,
                        itemStyle:{
                            color : upColor
                        }
                    },{
                        name: '死叉',
                        type: 'bar',
                        stack:'one',
                        data : sells,
                        itemStyle:{
                            color : downColor
                        }                        
                    },{
                        name: '金叉存量',
                        type: 'bar',
                        stack:'two',
                        xAxisIndex: 1,
                        yAxisIndex: 1,                        
                        data: positives,
                        itemStyle:{
                            color : upColor
                        }
                    },{
                        name: '死叉存量',
                        type: 'bar',
                        stack:'two',
                        xAxisIndex: 1,
                        yAxisIndex: 1,
                        data : negatives,
                        itemStyle:{
                            color : downColor
                        }                        
                    }]
                };            
            }
        } {...this.props}/>
        </div>);
    }
}

export default withStyles(styles)(MacdBuyShellChart);