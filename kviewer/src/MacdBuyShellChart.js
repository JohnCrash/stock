import React, { Component } from 'react';
import { withStyles } from '@material-ui/core/styles';
import FetchChart from './FetchChart';
import {postJson} from './fetch';
import Typography from '@material-ui/core/Typography';
import Button from '@material-ui/core/Button';
import {dateString} from './kits';
import {getDayLength,days} from './kits';
import EChart from './echart';
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
    state = {
        options:{}
    }
    pause5(d,pd5,dates,dl){
        if(d && pd5 &&dates){
            let buys = [];
            let sells = [];
            let jump = 0;
            for(let date of dates){
                if(date===d){
                    console.log(dateString(pd5.date));
                    for(let i = 1;i<=5;i++){
                        let death = pd5[`d${i}1`];
                        let gold = pd5[`d${i}2`];
                        buys.push(gold);
                        sells.push(-death);
                        jump = 5;
                    }
                }else{
                    if(jump===0){
                        buys.push(0);
                        sells.push(0);    
                    }else{
                        jump--;
                    }
                }
            }
            let options = {
                xAxis:{
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
                dataZoom: [
                    {
                        type: 'inside',
                        xAxisIndex: [0],
                        start: 100-dl,
                        end: 100
                    }                  
                ],
                yAxis:{
                    scale: true,
                    splitArea: {
                        show: true
                    },
                    min: -1500,
                    max: 1000                       
                },
                series:[
                    {
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
                    }
                ]
            };
            this.setState({options});
        }
    }
    render(){
        const {classes} = this.props;

        return (<div className={classes.root}>
        <FetchChart api={['/api/buysell','/api/phase']} init={
            ([{results},phase])=>{
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
                /**
                 * 增加5天的数据预测
                 */
                let mapTable = {};
                for(let p of phase.results){
                    mapTable[dateString(p.date)] = p;
                }

                let lastDayStr = dates[dates.length-1];
                let lastDay = new Date(lastDayStr);
                let j = 0;
                for(let i=1;i<10;i++){
                    let d = new Date(lastDay.getTime()+24*3600*1000*i);
                    if(d.getDay()!=6&&d.getDay()!=0){
                        dates.push(dateString(d));
                        j++;
                        if(j>=5)break;
                    }
                }
                let pd5 = mapTable[lastDayStr];
                let lastPosi = positives[positives.length-1];
                let lastNage = -negatives[negatives.length-1];
                for(let i=1;i<=5;i++){
                    let death = pd5[`d${i}1`];
                    let gold = pd5[`d${i}2`];
                    lastPosi -= death;
                    lastNage += gold;
                    buys.push(gold);
                    sells.push(-death);
                    positives.push(lastPosi);
                    negatives.push(-lastNage);
                }
                let markArea = {
                    silent:true,
                    data:[[{xAxis:lastDayStr},{xAxis:dates[dates.length-1]}]]
                };
                return {
                    tooltip: {
                        trigger: 'axis',
                        triggerOn:'click',
                        position:(point,param,dom,rect,size)=>{

                            console.log(param[0].axisValue);
                            if(param[0].axisValue)
                                this.pause5(param[0].axisValue,mapTable[param[0].axisValue],dates,dl);
                        },
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
                        markArea: markArea,
                        itemStyle:{
                            color : upColor
                        }
                    },{
                        name: '死叉',
                        type: 'bar',
                        stack:'one',
                        data : sells,
                        markArea: markArea,
                        itemStyle:{
                            color : downColor
                        }                        
                    },{
                        name: '金叉存量',
                        type: 'bar',
                        stack:'two',
                        xAxisIndex: 1,
                        yAxisIndex: 1,   
                        markArea: markArea,                     
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
                        markArea: markArea,
                        data : negatives,
                        itemStyle:{
                            color : downColor
                        }                        
                    }]
                };            
            }
        } {...this.props}/>
        <EChart options={this.state.options} width="100%" height={this.props.height/2}/>
        </div>);
    }
}

export default withStyles(styles)(MacdBuyShellChart);