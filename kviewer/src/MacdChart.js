import React, { Component } from 'react';
import { withStyles } from '@material-ui/core/styles';
import FetchChart from './FetchChart';
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

const moo = [['2005/6/30','2007/10/30'],['2013/1/30','2015/5/29']];

function nearDate(d,dates,dir){
    let dd = new Date(d);
    if(dir){
        for(let i=0;i<dates.length;i++){
            if(dd<(new Date(dates[i]))){
                return dates[i];
            }
        }
        return dates[dates.length-1];
    }else{
        for(let i=dates.length-1;i>=0;i--){
            if(dd>(new Date(dates[i]))){
                return dates[i];
            }
        }
        return dates[0];
    }
}

function MacdChart(props){
    let {classes} = props;
    let init = S =>({name,results})=>{
        let dates = [];
        let values = [];
        results.reverse().forEach(e => {
            let d = new Date(e.buy_date);
            let dateString = `${d.getFullYear()}/${d.getMonth()+1}/${d.getDate()}`;
            dates.push(dateString);
            if(S===0)
                values.push(e.rate);
            else{
                if(e.max_dd==0){
                    values.push(e.rate);
                }else
                    values.push(e.max_rate);
            }
        });
        let marka = moo.map(it=>{
            return [
                {xAxis: nearDate(it[0],dates,false)},
                {xAxis: nearDate(it[1],dates,true)}
            ]});
        return {
            legend: {
                data: [name],
                align: 'left'
            },
            visualMap: {
                show: false,
                seriesIndex: 0,
                dimension: 1,
                pieces: [{
                    max: 0,
                    color: downColor
                }, {
                    min: 0,
                    color: upColor
                }]
            },
            tooltip: {},
            xAxis: {
                data: dates,
                silent: false,
                splitLine: {
                    show: false
                }
            },
            yAxis: {
            },
            series: [{
                name: name,
                type: 'bar',
                markArea:  {
                    data: marka
                },                    
                data: values
            }]
        };            
    }
    return <div className={classes.root}>
        <FetchChart api='/api/macd' init={init(0)} {...props}/>
        <FetchChart api='/api/macd' init={init(1)} args={{db:'tech_macd2'}} {...props}/>
        <Typography>
            每一条代表一次买入卖出的完整交易，红色表示获利，绿色表示亏损。
        </Typography>    
    </div>;
}

export default withStyles(styles)(MacdChart);