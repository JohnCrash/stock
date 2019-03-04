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

function MacdChart(props){
    let {classes} = props;
    return <div className={classes.root}><FetchChart api='/api/macd' init={
        ({name,results})=>{
            let dates = [];
            let values = [];
            results.reverse().forEach(e => {
                let d = new Date(e.sell_date);
                let dateString = `${d.getFullYear()}/${d.getMonth()+1}/${d.getDate()}`;
                dates.push(dateString);
                values.push(e.rate);
            });        
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
                    data: values
                }]
            };            
        }
    } {...props}/>
    <Typography>
        每一条代表一次买入卖出的完整交易，红色表示获利，绿色表示亏损。
    </Typography>    
    </div>;
}

export default withStyles(styles)(MacdChart);