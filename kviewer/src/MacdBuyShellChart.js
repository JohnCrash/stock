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
                let dl = Math.abs(Math.floor(16000/getDayLength(results[0].date,results[results.length-1].date)));
                for(let i=0;i<results.length;i++){
                    let v = results[i];
                    dates.push(dateString(v.date));
                    buys.push(v.buy);
                    sells.push(-v.sell);
                }
                return {
                    tooltip: {},
                    legend: {
                        data: ['卖','买']
                    },
                    xAxis: {
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
                    yAxis: {
                    },
                    dataZoom: [
                        {
                            type: 'inside',
                            xAxisIndex: [0],
                            start: 100-dl,
                            end: 100
                        }                  
                    ],                    
                    series: [{
                        name: '买',
                        type: 'bar',
                        stack:'one',
                        data: buys,
                        itemStyle:{
                            color : upColor
                        }
                    },{
                        name: '卖',
                        type: 'bar',
                        stack:'one',
                        data : sells,
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