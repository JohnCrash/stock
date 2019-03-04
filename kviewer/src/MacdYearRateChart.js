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

function MacdYearRateChart(props){
    let {classes} = props;
    return <div className={classes.root}><FetchChart api='/api/macd' init={
        ({name,results})=>{
            let dates = [];
            let values = [];
            let years = {};
            results.reverse().forEach(e => {
                let d = new Date(e.sell_date);
                let y = d.getFullYear();
                years[y] = years[y]?years[y]+e.rate:e.rate;
            });
            for(let y in years){
                dates.push(y);
                values.push(years[y]);
            }
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
        每条线代表年收益率
    </Typography>
    </div>;
}

export default withStyles(styles)(MacdYearRateChart);